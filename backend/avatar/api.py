"""
FastAPI endpoints for the avatar system
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import asyncio
import io
import json
import os
import numpy as np
from pydantic import BaseModel, Field
from datetime import datetime
import logging

try:
    from backend.avatar.avatar_engine import (
        PhotorealisticAvatarEngine,
        AvatarConfig,
        AvatarGender,
        AvatarEthnicity,
        AvatarBodyType,
        AvatarAnimation,
    )
    from backend.avatar.person_cloner import PersonCloner, PersonData
except ImportError:
    from avatar_engine import (
        PhotorealisticAvatarEngine,
        AvatarConfig,
        AvatarGender,
        AvatarEthnicity,
        AvatarBodyType,
        AvatarAnimation,
    )
    from person_cloner import PersonCloner, PersonData

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Avatar System API", version="1.0.0")

# Initialize engines
avatar_engine = PhotorealisticAvatarEngine()
person_cloner = PersonCloner()

# Pydantic models for API
class AvatarCreateRequest(BaseModel):
    """Request model for creating avatars"""
    name: Optional[str] = None
    gender: str = "neutral"
    ethnicity: str = "caucasian"
    body_type: str = "average"
    age: int = Field(default=30, ge=18, le=100)
    height: float = Field(default=1.75, ge=1.0, le=2.5)
    face_shape: str = "oval"
    eye_color: str = "brown"
    hair_color: str = "brown"
    hair_style: str = "short"
    skin_tone: str = "medium"
    outfit: str = "casual"
    accessories: List[str] = Field(default_factory=list)

class AvatarCreateResponse(BaseModel):
    """Response model for avatar creation"""
    avatar_id: str
    status: str
    created_at: datetime

class AvatarAnimationRequest(BaseModel):
    """Request model for avatar animation"""
    avatar_id: str
    animation_type: str
    duration: float = Field(default=1.0, gt=0)
    keyframes: List[Dict[str, Any]] = Field(default_factory=list)
    loop: bool = False

class CloneCreateRequest(BaseModel):
    """Request model for creating person clones"""
    name: str
    email: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    social_media_posts: List[Dict[str, Any]] = Field(default_factory=list)
    emails: List[Dict[str, Any]] = Field(default_factory=list)
    voice_notes: List[str] = Field(default_factory=list)
    personal_documents: List[str] = Field(default_factory=list)

class CloneCreateResponse(BaseModel):
    """Response model for clone creation"""
    person_id: str
    status: str
    created_at: datetime

class CloneProfileResponse(BaseModel):
    """Response model for clone profile"""
    person_id: str
    name: str
    personality_traits: Dict[str, float]
    speech_patterns: Dict[str, Any]
    visual_features: Dict[str, Any]
    behavioral_data: Dict[str, Any]
    created_at: datetime
    last_updated: datetime

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Avatar System API...")
    await avatar_engine.initialize()
    await person_cloner.initialize()
    logger.info("Avatar System API started successfully")

# Avatar endpoints
@app.post("/avatars/create", response_model=AvatarCreateResponse)
async def create_avatar(request: AvatarCreateRequest):
    """Create a new avatar"""
    try:
        # Map string values to enums
        gender = AvatarGender(request.gender.lower())
        ethnicity = AvatarEthnicity(request.ethnicity.lower())
        body_type = AvatarBodyType(request.body_type.lower())
        
        config = AvatarConfig(
            gender=gender,
            ethnicity=ethnicity,
            body_type=body_type,
            age=request.age,
            height=request.height,
            face_shape=request.face_shape,
            eye_color=request.eye_color,
            hair_color=request.hair_color,
            hair_style=request.hair_style,
            skin_tone=request.skin_tone,
            outfit=request.outfit,
            accessories=request.accessories
        )
        
        avatar_id = await avatar_engine.create_avatar(config, request.name)
        
        return AvatarCreateResponse(
            avatar_id=avatar_id,
            status="success",
            created_at=datetime.now()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating avatar: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/avatars/{avatar_id}")
async def get_avatar(avatar_id: str):
    """Get avatar details"""
    avatar = avatar_engine.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return {
        "avatar_id": avatar_id,
        "config": avatar["config"].__dict__,
        "created_at": avatar["created_at"]
    }

@app.get("/avatars")
async def list_avatars():
    """List all avatars"""
    avatar_ids = avatar_engine.list_avatars()
    return {"avatars": avatar_ids}

@app.post("/avatars/{avatar_id}/animate")
async def animate_avatar(request: AvatarAnimationRequest):
    """Animate an avatar"""
    try:
        animation = AvatarAnimation(
            animation_type=request.animation_type,
            duration=request.duration,
            keyframes=request.keyframes,
            loop=request.loop
        )
        
        result = await avatar_engine.animate_avatar(request.avatar_id, animation)
        
        return {
            "avatar_id": request.avatar_id,
            "animation": request.animation_type,
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error animating avatar: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/avatars/{avatar_id}/expression")
async def animate_expression(
    avatar_id: str,
    expression: str = Form(...),
    intensity: float = Form(1.0)
):
    """Animate facial expression"""
    try:
        result = await avatar_engine.animate_facial_expression(
            avatar_id, 
            expression, 
            intensity
        )
        
        return {
            "avatar_id": avatar_id,
            "expression": expression,
            "intensity": intensity,
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error animating expression: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/avatars/{avatar_id}/lipsync")
async def generate_lipsync(
    avatar_id: str,
    audio_file: UploadFile = File(...),
    text: Optional[str] = Form(None)
):
    """Generate lip-sync animation from audio"""
    try:
        # Read audio data
        audio_data = await audio_file.read()
        audio_array = np.frombuffer(audio_data, dtype=np.float32)
        
        result = await avatar_engine.lip_sync(avatar_id, audio_array, text)
        
        return {
            "avatar_id": avatar_id,
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating lip-sync: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/avatars/{avatar_id}/render")
async def render_avatar(
    avatar_id: str,
    camera_position: Optional[str] = None,
    camera_rotation: Optional[str] = None,
    lighting: Optional[str] = None
):
    """Render avatar to image"""
    try:
        camera_config = None
        if camera_position:
            camera_config = {
                "position": json.loads(camera_position),
                "rotation": json.loads(camera_rotation) if camera_rotation else [0, 0, 0]
            }
            
        lighting_config = None
        if lighting:
            lighting_config = json.loads(lighting)
        
        image = await avatar_engine.render_avatar(
            avatar_id,
            camera_config=camera_config,
            lighting_config=lighting_config
        )
        
        # Convert numpy array to bytes
        img_bytes = image.tobytes()
        
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/png"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rendering avatar: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/avatars/{avatar_id}")
async def customize_avatar(
    avatar_id: str,
    customization: Dict[str, Any]
):
    """Customize an existing avatar"""
    try:
        updated_id = await avatar_engine.customize_avatar(avatar_id, customization)
        
        return {
            "avatar_id": updated_id,
            "status": "updated",
            "customization": customization
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error customizing avatar: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Clone endpoints
@app.post("/clones/create", response_model=CloneCreateResponse)
async def create_clone(request: CloneCreateRequest):
    """Create a person clone from multi-modal data"""
    try:
        person_data = PersonData(
            images=request.images,
            videos=request.videos,
            social_media_posts=request.social_media_posts,
            emails=request.emails,
            voice_notes=request.voice_notes,
            personal_documents=request.personal_documents
        )
        
        person_id = await person_cloner.create_clone(
            request.name,
            person_data,
            request.email
        )
        
        return CloneCreateResponse(
            person_id=person_id,
            status="success",
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error creating clone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/clones/{person_id}", response_model=CloneProfileResponse)
async def get_clone(person_id: str):
    """Get clone profile"""
    clone = person_cloner.get_clone(person_id)
    if not clone:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    return CloneProfileResponse(
        person_id=clone.person_id,
        name=clone.name,
        personality_traits=clone.personality_traits,
        speech_patterns=clone.speech_patterns,
        visual_features=clone.visual_features,
        behavioral_data=clone.behavioral_data,
        created_at=clone.created_at,
        last_updated=clone.last_updated
    )

@app.get("/clones")
async def list_clones():
    """List all clones"""
    clone_ids = person_cloner.list_clones()
    return {"clones": clone_ids}

@app.post("/clones/{person_id}/upload")
async def upload_person_data(
    person_id: str,
    images: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[]),
    voice_notes: List[UploadFile] = File(default=[]),
    documents: List[UploadFile] = File(default=[])
):
    """Upload person data files"""
    try:
        uploaded_files = {
            "images": [],
            "videos": [],
            "voice_notes": [],
            "documents": []
        }
        
        # Process uploaded files
        for file_list, category in [
            (images, "images"),
            (videos, "videos"),
            (voice_notes, "voice_notes"),
            (documents, "documents")
        ]:
            for file in file_list:
                content = await file.read()
                filename = file.filename
                
                # Save file to storage
                file_path = f"/tmp/{category}/{filename}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, "wb") as f:
                    f.write(content)
                    
                uploaded_files[category].append(file_path)
        
        return {
            "person_id": person_id,
            "uploaded_files": uploaded_files
        }
        
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    avatar_stats = avatar_engine.get_statistics()
    clone_stats = person_cloner.get_clone_statistics()
    
    return {
        "status": "healthy",
        "avatar_engine": avatar_stats,
        "person_cloner": clone_stats,
        "timestamp": datetime.now()
    }

@app.get("/statistics")
async def get_statistics():
    """Get system statistics"""
    avatar_stats = avatar_engine.get_statistics()
    clone_stats = person_cloner.get_clone_statistics()
    
    return {
        "avatar_system": avatar_stats,
        "cloning_system": clone_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)