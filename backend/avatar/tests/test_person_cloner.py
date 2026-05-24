"""
Comprehensive unit tests for the person cloning system
"""
import pytest
import pytest_asyncio
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

@pytest_asyncio.fixture
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
        emails=[
            {
                "subject": "Meeting reminder",
                "body": "Don't forget our meeting tomorrow at 2 PM",
                "timestamp": "2024-01-01T09:00:00"
            }
        ],
        voice_notes=["/fake/voice1.wav"],
        personal_documents=["/fake/doc1.txt"]
    )

class TestPersonCloner:
    """Test suite for Person Cloner"""
    
    @pytest.mark.asyncio
    async def test_cloner_initialization(self, person_cloner):
        """Test cloner initialization"""
        assert person_cloner.initialized is True
        assert len(person_cloner.clones) == 0
        
    @pytest.mark.asyncio
    async def test_generate_person_id(self, person_cloner):
        """Test person ID generation"""
        person_id1 = person_cloner.generate_person_id("John Doe", "john@example.com")
        person_id2 = person_cloner.generate_person_id("Jane Smith", "jane@example.com")
        
        assert len(person_id1) == 16
        assert len(person_id2) == 16
        assert person_id1 != person_id2
        
    @pytest.mark.asyncio
    async def test_create_clone(self, person_cloner, sample_person_data):
        """Test clone creation"""
        # Create mock files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock image
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock image data")
                
            # Create mock video
            vid_path = os.path.join(temp_dir, "test.mp4")
            with open(vid_path, "w") as f:
                f.write("mock video data")
                
            # Create mock voice note
            voice_path = os.path.join(temp_dir, "test.wav")
            with open(voice_path, "w") as f:
                f.write("mock audio data")
                
            # Create mock document
            doc_path = os.path.join(temp_dir, "test.txt")
            with open(doc_path, "w") as f:
                f.write("mock document content")
                
            # Update person data with real paths
            person_data = PersonData(
                images=[img_path],
                videos=[vid_path],
                voice_notes=[voice_path],
                personal_documents=[doc_path],
                social_media_posts=sample_person_data.social_media_posts,
                emails=sample_person_data.emails
            )
            
            person_id = await person_cloner.create_clone(
                "Test Person",
                person_data,
                "test@example.com"
            )
            
            assert person_id is not None
            assert len(person_id) == 16
            assert person_id in person_cloner.clones
            
    @pytest.mark.asyncio
    async def test_get_clone(self, person_cloner, sample_person_data):
        """Test getting clone profile"""
        # Create mock files
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock")
                
            person_data = PersonData(images=[img_path])
            
            person_id = await person_cloner.create_clone(
                "Test Person",
                person_data
            )
            
            clone = person_cloner.get_clone(person_id)
            assert clone is not None
            assert clone.person_id == person_id
            assert clone.name == "Test Person"
            
    @pytest.mark.asyncio
    async def test_get_nonexistent_clone(self, person_cloner):
        """Test getting non-existent clone"""
        clone = person_cloner.get_clone("nonexistent")
        assert clone is None
        
    @pytest.mark.asyncio
    async def test_list_clones(self, person_cloner, sample_person_data):
        """Test listing clones"""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock")
                
            person_data = PersonData(images=[img_path])
            
            # Create multiple clones
            person_id1 = await person_cloner.create_clone(
                "Person 1",
                person_data
            )
            person_id2 = await person_cloner.create_clone(
                "Person 2",
                person_data
            )
            
            clone_list = person_cloner.list_clones()
            assert len(clone_list) == 2
            assert person_id1 in clone_list
            assert person_id2 in clone_list
            
    @pytest.mark.asyncio
    async def test_clone_statistics(self, person_cloner, sample_person_data):
        """Test clone system statistics"""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock")
                
            person_data = PersonData(images=[img_path])
            
            stats = person_cloner.get_clone_statistics()
            assert stats["total_clones"] == 0
            assert stats["initialized"] is True
            
            await person_cloner.create_clone(
                "Test Person",
                person_data
            )
            
            stats = person_cloner.get_clone_statistics()
            assert stats["total_clones"] == 1
            
    @pytest.mark.asyncio
    async def test_person_data_validation(self):
        """Test PersonData initialization"""
        # Test with None values
        person_data = PersonData()
        assert person_data.images == []
        assert person_data.videos == []
        assert person_data.social_media_posts == []
        assert person_data.emails == []
        assert person_data.voice_notes == []
        assert person_data.personal_documents == []
        
        # Test with provided values
        person_data = PersonData(
            images=["img1.jpg"],
            videos=["vid1.mp4"],
            social_media_posts=[{"content": "test"}]
        )
        assert person_data.images == ["img1.jpg"]
        assert person_data.videos == ["vid1.mp4"]
        assert len(person_data.social_media_posts) == 1
        
    @pytest.mark.asyncio
    async def test_clone_profile_creation(self):
        """Test CloneProfile creation"""
        profile = CloneProfile(
            person_id="test123",
            name="Test Person",
            personality_traits={"openness": 0.8},
            speech_patterns={"tone": "friendly"},
            visual_features={"face_shape": "oval"},
            behavioral_data={"communication_style": "formal"},
            created_at="2024-01-01T12:00:00",
            last_updated="2024-01-01T12:00:00"
        )
        
        assert profile.person_id == "test123"
        assert profile.name == "Test Person"
        assert profile.personality_traits["openness"] == 0.8
        
    @pytest.mark.asyncio
    async def test_empty_person_data(self, person_cloner):
        """Test clone creation with empty person data"""
        person_data = PersonData()
        
        person_id = await person_cloner.create_clone(
            "Empty Person",
            person_data
        )
        
        assert person_id is not None
        clone = person_cloner.get_clone(person_id)
        assert clone.name == "Empty Person"
        
    @pytest.mark.asyncio
    async def test_clone_persistence(self, person_cloner):
        """Test clone persistence across sessions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock")
                
            person_data = PersonData(images=[img_path])
            
            # Create clone
            person_id = await person_cloner.create_clone(
                "Persistent Person",
                person_data
            )
            
            # Verify profile file exists
            profile_path = Path(person_cloner.storage_path) / "profiles" / f"{person_id}.json"
            assert profile_path.exists()
            
            # Load profile content
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
                assert profile_data["name"] == "Persistent Person"
                
    @pytest.mark.asyncio
    async def test_concurrent_clone_creation(self, person_cloner):
        """Test concurrent clone creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "test.jpg")
            with open(img_path, "w") as f:
                f.write("mock")
                
            person_data = PersonData(images=[img_path])
            
            # Create clones concurrently
            tasks = [
                person_cloner.create_clone(f"Person {i}", person_data)
                for i in range(3)
            ]
            
            person_ids = await asyncio.gather(*tasks)
            assert len(person_ids) == 3
            assert len(set(person_ids)) == 3  # All IDs should be unique
            
    @pytest.mark.asyncio
    async def test_clone_data_storage(self, person_cloner):
        """Test that person data is properly stored"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            files = {
                "image.jpg": "image data",
                "video.mp4": "video data",
                "voice.wav": "audio data",
                "doc.txt": "document content"
            }
            
            file_paths = {}
            for filename, content in files.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)
                file_paths[filename] = file_path
                
            person_data = PersonData(
                images=[file_paths["image.jpg"]],
                videos=[file_paths["video.mp4"]],
                voice_notes=[file_paths["voice.wav"]],
                personal_documents=[file_paths["doc.txt"]]
            )
            
            person_id = await person_cloner.create_clone(
                "Storage Test",
                person_data
            )
            
            # Verify files were copied
            data_path = Path(person_cloner.storage_path) / "data" / person_id
            assert (data_path / "images" / "image.jpg").exists()
            assert (data_path / "videos" / "video.mp4").exists()
            assert (data_path / "audio" / "voice.wav").exists()
            assert (data_path / "documents" / "doc.txt").exists()

if __name__ == "__main__":
    pytest.main([__file__])