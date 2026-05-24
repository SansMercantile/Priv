"""
Comprehensive unit tests for the person cloning system
"""
import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock

from person_cloner import (
    PersonCloner,
    PersonData,
    CloneProfile
)

@pytest.fixture
async def person_cloner():
    """Fixture for person cloner"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cloner = PersonCloner(temp_dir)
        await cloner.initialize()
        yield cloner

@pytest.fixture
def sample_person_data():
    """Fixture for sample person data"""
    return PersonData(
        images=["/fake/image1.jpg", "/fake/image2.jpg"],
        videos=["/fake/video1.mp4"],
        social_media_posts=[
            {
                "platform": "twitter",
                "content": "Just had a great day at work!",
                "timestamp": "2024-01-01T12:00:00",
                "engagement": {"likes": 10, "shares": 2}
            }
        ],
    )

class TestPersonCloner:
    """Test suite for Person Cloner"""
    
    @pytest.mark.asyncio
    async def test_cloner_initialization(self, person_cloner):
        """Test cloner initialization"""
        async for cloner in person_cloner:
            assert cloner.initialized is True
