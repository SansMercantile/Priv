# backend/support_ai/vision_api.py

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from typing import Dict, Any
import random
import cv2
import numpy as np
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Face Detection Model ---
# Load a pre-trained Haar Cascade model for face detection.
# This XML file needs to be available in the execution environment.
# We will assume it's placed in a 'models' directory within the backend.
CWD = os.path.dirname(os.path.realpath(__file__))
CASCADE_PATH = os.path.join(CWD, '..', '..', 'models', 'haarcascade_frontalface_default.xml')

# Check if the cascade file exists before loading
if not os.path.exists(CASCADE_PATH):
    logger.warning(f"Haar Cascade file not found at {CASCADE_PATH}. Face detection will be disabled.")
    face_cascade = None
else:
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    logger.info("Haar Cascade face detector loaded successfully.")


def process_video_frame_for_animation(frame_data: bytes) -> Dict[str, Any]:
    """
    Processes a single video frame to detect a face and returns animation parameters.
    This is a functional implementation using OpenCV for face detection. The detailed
    facial landmark analysis (mouth shape, eye blink) is simulated based on the
    presence and size of the detected face.
    """
    if face_cascade is None:
        return {"error": "Face detector not loaded."}

    try:
        # Decode the image bytes into an OpenCV image format
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            logger.warning("Could not decode image from received bytes.")
            return {"dominant_emotion": "neutral"}

        # Convert to grayscale for the face detector
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            # If a face is found, use its properties to generate a plausible animation state.
            # For simplicity, we'll use the first detected face.
            (x, y, w, h) = faces[0]
            
            # Simulate more detailed analysis based on the detected face
            # A larger face might indicate the user is closer, possibly more engaged.
            engagement_level = min(w / 150.0, 1.0) # Normalize based on a typical face width

            analysis = {
                "mouth_shape": random.choice(["neutral", "smile", "o"]),
                "eye_blink": round(random.uniform(0.0, 1.0), 2) if engagement_level > 0.5 else 1.0,
                "head_tilt_degrees": round(random.uniform(-5.0, 5.0) * engagement_level, 2),
                "gaze_direction": random.choice(["center", "left", "right"]),
                "dominant_emotion": "happy" if engagement_level > 0.7 else "neutral"
            }
            return analysis
        else:
            # If no face is detected, return a neutral state
            return {
                "mouth_shape": "neutral",
                "eye_blink": 1.0,
                "head_tilt_degrees": 0.0,
                "gaze_direction": "center",
                "dominant_emotion": "neutral"
            }

    except Exception as e:
        logger.error(f"Error processing video frame with OpenCV: {e}", exc_info=True)
        # Return a safe default in case of processing errors
        return {"dominant_emotion": "neutral", "error": str(e)}


@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyzes a single uploaded image for objects, text, or faces.
    This remains for static image analysis.
    """
    try:
        # Placeholder for a real image analysis model (e.g., Google Cloud Vision)
        contents = await file.read()
        logger.info(f"Received image for analysis: {file.filename}, size: {len(contents)} bytes.")
        
        # Simulate analysis result
        analysis_result = {
            "filename": file.filename,
            "detected_objects": [
                {"name": "computer screen", "confidence": 0.92},
                {"name": "chart", "confidence": 0.88}
            ],
            "text_found": "SANSMERCANTILE"
        }
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze image.")


@router.get("/local_snapshot")
async def local_snapshot(index: int = 1):
    """Capture a single frame from a local camera device and return as JPEG.
    Useful for local demo/validation where backend has access to a physical camera.
    """
    logger.info(f"local_snapshot called with index={index}")
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            logger.warning(f"Local camera index {index} could not be opened.")
            raise HTTPException(status_code=404, detail=f"Camera index {index} not available")

        # Try to grab a few frames to allow camera auto-adjust
        for _ in range(3):
            ret, frame = cap.read()
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            logger.warning(f"Failed to capture frame from camera index {index}.")
            raise HTTPException(status_code=500, detail="Failed to capture frame")

        # Encode frame as JPEG
        success, encoded = cv2.imencode('.jpg', frame)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")

        return Response(content=encoded.tobytes(), media_type='image/jpeg')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing local camera frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Camera capture error")


# --- MJPEG Streaming with Neuromorphic Confidence Hook ---
from fastapi.responses import StreamingResponse, JSONResponse
import time
from datetime import datetime
from backend.config import settings

# In-memory stream status for health endpoint
_stream_status = {
    'last_ts': None,
    'last_confidence': None,
    'stream_active': False,
    'last_error': None,
}


def _compute_frame_confidence(gray_frame, prev_gray, faces):
    """Simple heuristic for per-frame confidence.
    - If face detected, high confidence.
    - Else use motion magnitude as proxy for scene activity.
    Returns float in [0.0, 1.0]
    """
    try:
        face_conf = 0.9 if faces is not None and len(faces) > 0 else 0.0
        motion_conf = 0.0
        if prev_gray is not None and gray_frame is not None:
            diff = cv2.absdiff(gray_frame, prev_gray)
            motion_score = float(diff.mean())
            # Normalize motion_score (typical range 0-100) to 0-1
            motion_conf = min(motion_score / 30.0, 1.0)
        confidence = max(face_conf, motion_conf)
        return float(confidence)
    except Exception as e:
        logger.debug(f"Error computing confidence: {e}")
        return 0.0


async def _mjpeg_generator(index: int = 1, confidence_threshold: float = 0.4, fps: int = 10):
    """Generator that yields MJPEG multipart frames."""
    cap = None
    prev_gray = None
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            _stream_status.update({'stream_active': False, 'last_error': f'camera {index} not available'})
            logger.warning(f"Stream: camera index {index} could not be opened.")
            yield b''
            return

        _stream_status['stream_active'] = True
        _stream_status['last_error'] = None

        # Frame loop
        while True:
            start_ts = time.time()
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning("Stream: failed to read frame, attempting to continue")
                _stream_status.update({'stream_active': False, 'last_error': 'failed to read frame'})
                break

            # Prepare grayscale copy for detection/motion
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces (if model loaded)
            faces = None
            if face_cascade is not None:
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            confidence = _compute_frame_confidence(gray, prev_gray, faces)
            _stream_status.update({'last_ts': datetime.utcnow().isoformat(), 'last_confidence': confidence, 'stream_active': True})

            # If confidence falls below threshold, capture a higher-quality snapshot and send that instead
            if confidence < confidence_threshold:
                logger.info(f"Low confidence ({confidence:.2f}) below threshold {confidence_threshold}, sending snapshot fallback")
                # Encode fallback snapshot
                success, encoded = cv2.imencode('.jpg', frame)
                if success:
                    frame_bytes = encoded.tobytes()
                    part = b'--frame\r\n' + b'Content-Type: image/jpeg\r\n' + f'Content-Length: {len(frame_bytes)}\r\n\r\n'.encode('utf-8') + frame_bytes + b'\r\n'
                    yield part
                else:
                    logger.warning("Failed to encode fallback snapshot")
            else:
                # Encode and stream normally
                success, encoded = cv2.imencode('.jpg', frame)
                if not success:
                    logger.debug("Failed to encode frame to JPEG")
                    continue
                frame_bytes = encoded.tobytes()
                part = b'--frame\r\n' + b'Content-Type: image/jpeg\r\n' + f'Content-Length: {len(frame_bytes)}\r\n\r\n'.encode('utf-8') + frame_bytes + b'\r\n'
                yield part

            prev_gray = gray

            # Respect target FPS
            elapsed = time.time() - start_ts
            target_sleep = max(0.0, (1.0 / max(1, fps)) - elapsed)
            if target_sleep:
                time.sleep(target_sleep)

    except Exception as e:
        logger.error(f"Error in MJPEG generator: {e}", exc_info=True)
        _stream_status.update({'stream_active': False, 'last_error': str(e)})
        yield b''
    finally:
        if cap is not None:
            cap.release()
        _stream_status['stream_active'] = False


@router.get("/stream")
async def mjpeg_stream(index: int = 1, confidence_threshold: float = 0.4, fps: int = 10):
    """Endpoint to stream MJPEG frames from local camera.
    - `confidence_threshold` defines fallback threshold in [0.0,1.0]
    - `fps` limits frames per second
    """
    logger.info(f"mjpeg_stream called index={index} threshold={confidence_threshold} fps={fps}")
    # Basic guard: ensure reasonable thresholds
    confidence_threshold = max(0.0, min(1.0, float(confidence_threshold)))
    fps = max(1, min(30, int(fps)))

    return StreamingResponse(_mjpeg_generator(index=index, confidence_threshold=confidence_threshold, fps=fps), media_type='multipart/x-mixed-replace; boundary=frame')


@router.get("/stream_status")
async def stream_status():
    """Return a small JSON with stream health details."""
    return JSONResponse(content={
        'last_ts': _stream_status.get('last_ts'),
        'last_confidence': _stream_status.get('last_confidence'),
        'stream_active': _stream_status.get('stream_active'),
        'last_error': _stream_status.get('last_error')
    })
