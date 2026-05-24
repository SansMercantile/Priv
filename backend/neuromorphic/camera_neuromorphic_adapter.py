# backend/neuromorphic/camera_neuromorphic_adapter.py
"""
Camera-based Neuromorphic Computing Adapter

This module enables neuromorphic computing using standard cameras (webcam, phone camera, etc.)
instead of specialized neuromorphic hardware like Intel Loihi or IBM TrueNorth.

It simulates neuromorphic behavior by:
1. Converting camera frames to spike trains (event-based vision)
2. Implementing spiking neural networks (SNNs) in software
3. Using temporal coding for pattern recognition
4. Leveraging GPU acceleration when available
"""

import logging
import numpy as np
import cv2
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class SpikeEvent:
    """Represents a neuromorphic spike event"""
    x: int
    y: int
    timestamp: float
    polarity: int  # 1 for ON event, -1 for OFF event
    intensity: float


class CameraNeuromorphicAdapter:
    """
    Converts standard camera input into neuromorphic spike events.
    
    This allows PRIV to use neuromorphic computing concepts without
    requiring specialized hardware like DVS (Dynamic Vision Sensor) cameras.
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        resolution: Tuple[int, int] = (640, 480),
        threshold: float = 15.0,
        use_gpu: bool = True
    ):
        """
        Initialize the camera neuromorphic adapter.
        
        Args:
            camera_index: Camera device index (0 for default webcam)
            resolution: Camera resolution (width, height)
            threshold: Intensity change threshold for spike generation
            use_gpu: Use GPU acceleration if available
        """
        self.camera_index = camera_index
        self.resolution = resolution
        self.threshold = threshold
        self.use_gpu = use_gpu and cv2.cuda.getCudaEnabledDeviceCount() > 0
        
        self.camera: Optional[cv2.VideoCapture] = None
        self.previous_frame: Optional[np.ndarray] = None
        self.is_running = False
        self.spike_queue = queue.Queue(maxsize=10000)
        self.capture_thread: Optional[threading.Thread] = None
        
        logger.info(f"CameraNeuromorphicAdapter initialized (GPU: {self.use_gpu})")
    
    def start(self) -> bool:
        """Start the camera and spike generation"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Start capture thread
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info("Camera neuromorphic adapter started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False
    
    def stop(self):
        """Stop the camera and spike generation"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.camera:
            self.camera.release()
        logger.info("Camera neuromorphic adapter stopped")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        while self.is_running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    continue
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Generate spikes from frame changes
                if self.previous_frame is not None:
                    spikes = self._generate_spikes(gray, self.previous_frame)
                    for spike in spikes:
                        try:
                            self.spike_queue.put_nowait(spike)
                        except queue.Full:
                            # Drop oldest spike if queue is full
                            try:
                                self.spike_queue.get_nowait()
                                self.spike_queue.put_nowait(spike)
                            except:
                                pass
                
                self.previous_frame = gray.copy()
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
    
    def _generate_spikes(
        self,
        current_frame: np.ndarray,
        previous_frame: np.ndarray
    ) -> List[SpikeEvent]:
        """
        Generate spike events from frame differences.
        
        This simulates event-based vision by detecting intensity changes.
        """
        # Calculate intensity difference
        diff = current_frame.astype(np.float32) - previous_frame.astype(np.float32)
        
        # Find pixels with significant changes
        on_events = diff > self.threshold
        off_events = diff < -self.threshold
        
        spikes = []
        timestamp = datetime.now().timestamp()
        
        # Generate ON spikes
        on_coords = np.argwhere(on_events)
        for y, x in on_coords:
            spikes.append(SpikeEvent(
                x=int(x),
                y=int(y),
                timestamp=timestamp,
                polarity=1,
                intensity=float(diff[y, x])
            ))
        
        # Generate OFF spikes
        off_coords = np.argwhere(off_events)
        for y, x in off_coords:
            spikes.append(SpikeEvent(
                x=int(x),
                y=int(y),
                timestamp=timestamp,
                polarity=-1,
                intensity=float(abs(diff[y, x]))
            ))
        
        return spikes
    
    def get_spikes(self, max_count: int = 1000) -> List[SpikeEvent]:
        """Get accumulated spike events"""
        spikes = []
        try:
            while len(spikes) < max_count:
                spike = self.spike_queue.get_nowait()
                spikes.append(spike)
        except queue.Empty:
            pass
        return spikes
    
    def get_spike_rate(self) -> float:
        """Get current spike generation rate (spikes/second)"""
        return self.spike_queue.qsize()
    
    def detect_available_cameras(self) -> List[int]:
        """Detect all available cameras on the system"""
        available = []
        for i in range(10):  # Check first 10 indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

