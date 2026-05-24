# backend/support_ai/audio_api.py
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
from fastapi.responses import StreamingResponse
import io

from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the OpenAI client for this module
try:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found in settings.")
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except (ValueError, ImportError) as e:
    logger.error(f"Failed to initialize OpenAI client for audio API: {e}")
    client = None

class TextPayload(BaseModel):
    text: str
    voice: str = "alloy" # Default voice

@router.post("/synthesize-speech")
async def synthesize_speech(payload: TextPayload):
    """
    Converts text to speech using OpenAI's TTS API and streams the audio back.
    """
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured.")

    try:
        logger.info(f"Synthesizing speech for text: '{payload.text[:50]}...' with voice '{payload.voice}'")
        response = client.audio.speech.create(
            model="tts-1",
            voice=payload.voice,
            input=payload.text,
            response_format="mp3"
        )
        
        # Stream the audio data back to the client
        return StreamingResponse(io.BytesIO(response.content), media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"Error during text-to-speech synthesis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to synthesize speech.")


@router.post("/transcribe-audio")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribes audio to text using OpenAI's Whisper API.
    """
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured.")

    try:
        logger.info(f"Transcribing audio file: {audio_file.filename}")
        
        # Pass the uploaded file directly to the API
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file.file,
        )
        logger.info(f"Transcription result: '{transcript.text}'")
        return {"text": transcript.text}
        
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")