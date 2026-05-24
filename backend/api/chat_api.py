"""
Chat API endpoints for PRIV AI assistant
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import random
from openai import OpenAI
from backend.config import settings

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    sentiment: Optional[str] = None


def get_ai_response(message: str) -> str:
    """Generate AI response using OpenAI or local Ollama fallback."""
    try:
        # Primary: OpenAI when configured
        if settings.OPENAI_API_KEY:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.responses.create(
                model="gemma4:31b-cloud",
                input=[{"role": "user", "content": message}],
                text={"format": {"type": "text"}, "verbosity": "medium"},
                reasoning={"effort": "medium", "summary": "auto"},
                tools=[],
                store=True,
                include=["reasoning.encrypted_content", "web_search_call.action.sources"]
            )
            return response.text if hasattr(response, 'text') else str(response)
        
        # Secondary: Local Ollama Fallback
        import requests
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma4:31b-cloud", "prompt": message, "stream": False}
        )
        if ollama_response.status_code == 200:
            return ollama_response.json().get("response", "Ollama returned an empty response.")
            
    except Exception as e:
        print(f"AI Backend Error: {e}")
    
    return "I'm currently unable to connect to my reasoning cores. Please check the local Ollama service or OpenAI API key."


@router.post("/support", response_model=ChatResponse)
async def chat_support(request: ChatRequest):
    """
    Chat with PRIV AI assistant
    
    This endpoint provides conversational AI support for trading and portfolio management.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Generate AI response
        ai_message = get_ai_response(request.message)
        
        return ChatResponse(
            message=ai_message,
            sentiment="neutral"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
@router.post("/chat/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Alternative chat endpoints (aliases for /support)
    """
    return await chat_support(request)
