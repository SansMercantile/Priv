from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None

class AIResponse(APIResponse):
    message: str
    emotion: str
    confidence: Optional[float] = None
    state_snapshot: Optional[Dict[str, Any]] = None