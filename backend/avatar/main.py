"""
Main application entry point for Avatar System (Constellation port 8012).
"""

import logging
import os

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from backend.avatar.api import app
except ImportError:
    from api import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


@app.get("/")
async def read_root():
    return {
        "system": "avatar",
        "status": "operational",
        "description": "Customer Support Avatar System",
        "docs": "/docs",
        "frontend": "/frontend",
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8012"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
