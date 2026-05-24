# Avatar System API Documentation

## Overview

The Avatar System API provides comprehensive endpoints for creating, managing, and interacting with photorealistic avatars and person clones. The system supports advanced features including facial animation, lip-sync, person cloning from multi-modal data, and real-time rendering.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Avatar Endpoints](#avatar-endpoints)
3. [Clone Endpoints](#clone-endpoints)
4. [Utility Endpoints](#utility-endpoints)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Rate Limiting](#rate-limiting)
8. [Authentication](#authentication)

## Getting Started

### Base URL
```
http://localhost:8000
```

### Content Type
All requests and responses use `application/json` unless otherwise specified.

### Installation
```bash
pip install -r requirements.txt
python api.py
```

## Avatar Endpoints

### Create Avatar
Create a new photorealistic avatar with customizable features.

**Endpoint:** `POST /avatars/create`

**Request Body:**
```json
{
  "name": "business_woman",
  "gender": "female",
  "ethnicity": "asian",
  "body_type": "athletic",
  "age": 28,
  "height": 1.68,
  "face_shape": "oval",
  "eye_color": "brown",
  "hair_color": "black",
  "hair_style": "long",
  "skin_tone": "medium",
  "outfit": "business",
  "accessories": ["glasses", "watch"]
}
```

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "status": "success",
  "created_at": "2024-01-15T12:00:00"
}
```

**Parameters:**
- `name` (optional): Custom name for the avatar
- `gender`: `male`, `female`, `neutral`
- `ethnicity`: `caucasian`, `african`, `asian`, `hispanic`, `middle_eastern`, `mixed`
- `body_type`: `slim`, `athletic`, `average`, `muscular`, `plus_size`
- `age`: Integer between 18-100
- `height`: Float in meters (1.0-2.5)
- `face_shape`: `oval`, `round`, `square`, `heart`, `diamond`
- `eye_color`: `brown`, `blue`, `green`, `hazel`, `gray`
- `hair_color`: `black`, `brown`, `blonde`, `red`, `gray`, `white`
- `hair_style`: `short`, `long`, `curly`, `straight`, `wavy`
- `skin_tone`: `light`, `medium`, `dark`
- `outfit`: `casual`, `business`, `formal`, `athletic`, `ethnic`
- `accessories`: Array of accessory names

### Get Avatar
Retrieve avatar details by ID.

**Endpoint:** `GET /avatars/{avatar_id}`

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "config": {
    "gender": "female",
    "ethnicity": "asian",
    "body_type": "athletic",
    "age": 28,
    "height": 1.68,
    "face_shape": "oval",
    "eye_color": "brown",
    "hair_color": "black",
    "hair_style": "long",
    "skin_tone": "medium",
    "outfit": "business",
    "accessories": ["glasses", "watch"]
  },
  "created_at": 1234567890.123
}
```

### List Avatars
Get a list of all avatar IDs.

**Endpoint:** `GET /avatars`

**Response:**
```json
{
  "avatars": ["avatar_1234567890", "avatar_0987654321"]
}
```

### Animate Avatar
Apply animation to an avatar.

**Endpoint:** `POST /avatars/{avatar_id}/animate`

**Request Body:**
```json
{
  "avatar_id": "avatar_1234567890",
  "animation_type": "greeting",
  "duration": 2.0,
  "keyframes": [
    {"time": 0, "pose": "standing", "expression": "neutral"},
    {"time": 1.0, "pose": "waving", "expression": "happy"},
    {"time": 2.0, "pose": "standing", "expression": "neutral"}
  ],
  "loop": false
}
```

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "animation": "greeting",
  "result": {
    "frames": [],
    "duration": 2.0,
    "fps": 30
  }
}
```

### Animate Facial Expression
Apply facial expression animation to an avatar.

**Endpoint:** `POST /avatars/{avatar_id}/expression`

**Form Data:**
- `expression`: `happy`, `sad`, `angry`, `surprised`, `disgusted`, `fearful`, `neutral`
- `intensity`: Float between 0.0-1.0 (default: 1.0)

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "expression": "happy",
  "intensity": 0.8,
  "result": {
    "expression": "happy",
    "intensity": 0.8,
    "blendshapes": {}
  }
}
```

### Generate Lip Sync
Generate lip-sync animation from audio file.

**Endpoint:** `POST /avatars/{avatar_id}/lipsync`

**Form Data:**
- `audio_file`: Audio file (WAV, MP3, etc.)
- `text` (optional): Text transcript of the audio

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "result": {
    "phonemes": [],
    "timing": [],
    "visemes": []
  }
}
```

### Render Avatar
Render avatar to image with optional camera and lighting settings.

**Endpoint:** `GET /avatars/{avatar_id}/render`

**Query Parameters:**
- `camera_position`: JSON array [x, y, z]
- `camera_rotation`: JSON array [x, y, z]
- `lighting`: JSON object with lighting configuration

**Response:** PNG image data

### Customize Avatar
Update existing avatar with new configuration.

**Endpoint:** `PUT /avatars/{avatar_id}`

**Request Body:**
```json
{
  "age": 30,
  "hair_color": "blonde",
  "outfit": "formal"
}
```

**Response:**
```json
{
  "avatar_id": "avatar_1234567890",
  "status": "updated",
  "customization": {
    "age": 30,
    "hair_color": "blonde",
    "outfit": "formal"
  }
}
```

## Clone Endpoints

### Create Clone
Create a digital clone from multi-modal person data.

**Endpoint:** `POST /clones/create`

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "images": ["/path/to/image1.jpg", "/path/to/image2.jpg"],
  "videos": ["/path/to/video1.mp4"],
  "social_media_posts": [
    {
      "platform": "twitter",
      "content": "Just had a great day at work!",
      "timestamp": "2024-01-01T12:00:00",
      "engagement": {"likes": 10, "shares": 2}
    }
  ],
  "emails": [
    {
      "subject": "Meeting reminder",
      "body": "Don't forget our meeting tomorrow",
      "timestamp": "2024-01-01T09:00:00"
    }
  ],
  "voice_notes": ["/path/to/voice1.wav"],
  "personal_documents": ["/path/to/resume.pdf"]
}
```

**Response:**
```json
{
  "person_id": "abc123def4567890",
  "status": "success",
  "created_at": "2024-01-15T12:00:00"
}
```

### Get Clone
Retrieve clone profile details.

**Endpoint:** `GET /clones/{person_id}`

**Response:**
```json
{
  "person_id": "abc123def4567890",
  "name": "Jane Smith",
  "personality_traits": {
    "openness": 0.7,
    "conscientiousness": 0.6,
    "extraversion": 0.5,
    "agreeableness": 0.8,
    "neuroticism": 0.3
  },
  "speech_patterns": {
    "voice_embedding": null,
    "speech_patterns": {},
    "accent": null,
    "tone": null,
    "pace": null,
    "emotion": []
  },
  "visual_features": {
    "face_embeddings": [],
    "facial_features": {},
    "clothing_styles": [],
    "backgrounds": [],
    "lighting_conditions": []
  },
  "behavioral_data": {
    "communication_style": "formal",
    "response_time": "quick",
    "topics": [],
    "vocabulary": [],
    "sentence_structure": "complex",
    "emotional_tone": "positive",
    "formality_level": 0.8
  },
  "created_at": "2024-01-15T12:00:00",
  "last_updated": "2024-01-15T12:00:00"
}
```

### List Clones
Get a list of all clone IDs.

**Endpoint:** `GET /clones`

**Response:**
```json
{
  "clones": ["abc123def4567890", "xyz987fed6543210"]
}
```

### Upload Person Data
Upload files for person data (images, videos, audio, documents).

**Endpoint:** `POST /clones/{person_id}/upload`

**Form Data:**
- `images`: Array of image files
- `videos`: Array of video files
- `voice_notes`: Array of audio files
- `documents`: Array of document files

**Response:**
```json
{
  "person_id": "abc123def4567890",
  "uploaded_files": {
    "images": ["/tmp/images/photo1.jpg"],
    "videos": ["/tmp/videos/video1.mp4"],
    "voice_notes": ["/tmp/audio/voice1.wav"],
    "documents": ["/tmp/documents/doc1.pdf"]
  }
}
```

## Utility Endpoints

### Health Check
Check system health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "avatar_engine": {
    "initialized": true,
    "total_avatars": 5,
    "rendering_engine": true,
    "physics_engine": true,
    "animation_system": true
  },
  "person_cloner": {
    "total_clones": 3,
    "initialized": true,
    "storage_path": "/workspace/avatar_clones",
    "storage_size": 10485760
  },
  "timestamp": "2024-01-15T12:00:00"
}
```

### System Statistics
Get comprehensive system statistics.

**Endpoint:** `GET /statistics`

**Response:**
```json
{
  "avatar_system": {
    "initialized": true,
    "total_avatars": 5,
    "rendering_engine": true,
    "physics_engine": true,
    "animation_system": true
  },
  "cloning_system": {
    "total_clones": 3,
    "initialized": true,
    "storage_path": "/workspace/avatar_clones",
    "storage_size": 10485760
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Examples

### Python Example
```python
import requests
import json

# Create avatar
response = requests.post(
    "http://localhost:8000/avatars/create",
    json={
        "name": "my_avatar",
        "gender": "female",
        "ethnicity": "asian",
        "age": 25,
        "outfit": "business"
    }
)
avatar_data = response.json()
print(f"Created avatar: {avatar_data['avatar_id']}")

# Create clone
response = requests.post(
    "http://localhost:8000/clones/create",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "images": ["/path/to/photo.jpg"],
        "social_media_posts": [
            {
                "platform": "twitter",
                "content": "Hello world!",
                "timestamp": "2024-01-01T12:00:00"
            }
        ]
    }
)
clone_data = response.json()
print(f"Created clone: {clone_data['person_id']}")
```

### cURL Example
```bash
# Create avatar
curl -X POST "http://localhost:8000/avatars/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_avatar",
    "gender": "male",
    "ethnicity": "caucasian",
    "age": 30
  }'

# Create clone
curl -X POST "http://localhost:8000/clones/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "images": ["/path/to/photo.jpg"]
  }'
```

## Rate Limiting

Currently, no rate limiting is implemented. However, it's recommended to implement rate limiting in production environments.

## Authentication

The API currently doesn't require authentication. For production use, implement appropriate authentication mechanisms such as API keys or OAuth.

## Performance Considerations

- Avatar creation and rendering can be computationally intensive
- Large file uploads for cloning should be handled with appropriate timeouts
- Consider implementing caching for frequently accessed avatars
- Use appropriate server resources for rendering operations

## Support

For support and questions, please refer to the system documentation or contact the development team.