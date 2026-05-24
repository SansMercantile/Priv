"""
Comprehensive unit tests for the avatar engine
"""
import pytest
import pytest_asyncio
import asyncio
import numpy as np
from unittest.mock import AsyncMock, patch
import tempfile
import os

from avatar_engine import (
    PhotorealisticAvatarEngine,
    AvatarConfig,
    AvatarGender,
    AvatarEthnicity,
    AvatarBodyType,
    AvatarAnimation
)

@pytest_asyncio.fixture
async def avatar_engine():
    """Fixture for avatar engine"""
    engine = PhotorealisticAvatarEngine()
    await engine.initialize()
    return engine

@pytest.fixture
def avatar_config():
    """Fixture for avatar configuration"""
    return AvatarConfig(
        gender=AvatarGender.FEMALE,
        ethnicity=AvatarEthnicity.ASIAN,
        body_type=AvatarBodyType.ATHLETIC,
        age=28,
        height=1.68,
        face_shape="oval",
        eye_color="brown",
        hair_color="black",
        hair_style="long",
        skin_tone="medium",
        outfit="business",
        accessories=["glasses", "watch"]
    )

class TestAvatarEngine:
    """Test suite for Avatar Engine"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, avatar_engine):
        """Test engine initialization"""
        assert avatar_engine.initialized is True
        assert avatar_engine.rendering_engine is not None
        assert avatar_engine.physics_engine is not None
        assert len(avatar_engine.avatars) == 0
        
    @pytest.mark.asyncio
    async def test_create_avatar(self, avatar_engine, avatar_config):
        """Test avatar creation"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        assert avatar_id == "test_avatar"
        assert avatar_id in avatar_engine.avatars
        
        avatar_data = avatar_engine.avatars[avatar_id]
        assert avatar_data["config"] == avatar_config
        assert "data" in avatar_data
        assert "created_at" in avatar_data
        
    @pytest.mark.asyncio
    async def test_create_avatar_without_name(self, avatar_engine, avatar_config):
        """Test avatar creation without custom name"""
        avatar_id = await avatar_engine.create_avatar(avatar_config)
        
        assert avatar_id.startswith("avatar_")
        assert avatar_id in avatar_engine.avatars
        
    @pytest.mark.asyncio
    async def test_customize_avatar(self, avatar_engine, avatar_config):
        """Test avatar customization"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        customization = {
            "age": 35,
            "hair_color": "blonde",
            "outfit": "formal"
        }
        
        updated_id = await avatar_engine.customize_avatar(avatar_id, customization)
        assert updated_id == avatar_id
        
        updated_avatar = avatar_engine.avatars[avatar_id]
        assert updated_avatar["config"].age == 35
        assert updated_avatar["config"].hair_color == "blonde"
        assert updated_avatar["config"].outfit == "formal"
        
    @pytest.mark.asyncio
    async def test_get_avatar(self, avatar_engine, avatar_config):
        """Test getting avatar data"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        avatar_data = avatar_engine.get_avatar(avatar_id)
        assert avatar_data is not None
        assert avatar_data["config"] == avatar_config
        
    @pytest.mark.asyncio
    async def test_get_nonexistent_avatar(self, avatar_engine):
        """Test getting non-existent avatar"""
        avatar_data = avatar_engine.get_avatar("nonexistent")
        assert avatar_data is None
        
    @pytest.mark.asyncio
    async def test_list_avatars(self, avatar_engine, avatar_config):
        """Test listing avatars"""
        avatar_id1 = await avatar_engine.create_avatar(avatar_config, "avatar1")
        avatar_id2 = await avatar_engine.create_avatar(avatar_config, "avatar2")
        
        avatar_list = avatar_engine.list_avatars()
        assert len(avatar_list) == 2
        assert avatar_id1 in avatar_list
        assert avatar_id2 in avatar_list
        
    @pytest.mark.asyncio
    async def test_animate_avatar(self, avatar_engine, avatar_config):
        """Test avatar animation"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        animation = AvatarAnimation(
            animation_type="walk",
            duration=2.5,
            keyframes=[{"time": 0, "pose": "start"}, {"time": 2.5, "pose": "end"}],
            loop=True
        )
        
        result = await avatar_engine.animate_avatar(avatar_id, animation)
        
        assert result is not None
        assert "frames" in result
        assert "duration" in result
        assert result["duration"] == 2.5
        
    @pytest.mark.asyncio
    async def test_animate_nonexistent_avatar(self, avatar_engine):
        """Test animating non-existent avatar"""
        animation = AvatarAnimation(
            animation_type="walk",
            duration=1.0,
            keyframes=[],
            loop=False
        )
        
        with pytest.raises(ValueError, match="Avatar not found"):
            await avatar_engine.animate_avatar("nonexistent", animation)
            
    @pytest.mark.asyncio
    async def test_animate_facial_expression(self, avatar_engine, avatar_config):
        """Test facial expression animation"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        result = await avatar_engine.animate_facial_expression(
            avatar_id, 
            "happy", 
            intensity=0.8
        )
        
        assert result is not None
        assert result["expression"] == "happy"
        assert result["intensity"] == 0.8
        
    @pytest.mark.asyncio
    async def test_lip_sync(self, avatar_engine, avatar_config):
        """Test lip sync generation"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        # Create dummy audio data
        audio_data = np.random.rand(44100)  # 1 second of audio
        
        result = await avatar_engine.lip_sync(avatar_id, audio_data, "Hello world")
        
        assert result is not None
        assert "phonemes" in result
        assert "timing" in result
        
    @pytest.mark.asyncio
    async def test_render_avatar(self, avatar_engine, avatar_config):
        """Test avatar rendering"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        image = await avatar_engine.render_avatar(avatar_id)
        
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert image.shape == (1080, 1920, 3)  # Default resolution
        
    @pytest.mark.asyncio
    async def test_render_avatar_with_config(self, avatar_engine, avatar_config):
        """Test avatar rendering with custom config"""
        avatar_id = await avatar_engine.create_avatar(avatar_config, "test_avatar")
        
        camera_config = {
            "position": [0, 0, 5],
            "rotation": [0, 0, 0],
            "fov": 60
        }
        
        lighting_config = {
            "ambient": [0.5, 0.5, 0.5],
            "directional": [[1, 1, 1], [0.8, 0.8, 0.8]]
        }
        
        image = await avatar_engine.render_avatar(
            avatar_id, 
            camera_config=camera_config,
            lighting_config=lighting_config
        )
        
        assert image is not None
        
    @pytest.mark.asyncio
    async def test_get_statistics(self, avatar_engine, avatar_config):
        """Test engine statistics"""
        stats = avatar_engine.get_statistics()
        
        assert stats["initialized"] is True
        assert stats["total_avatars"] == 0
        assert stats["rendering_engine"] is True
        assert stats["physics_engine"] is True
        assert stats["animation_system"] is True
        
        # Create an avatar and check stats again
        await avatar_engine.create_avatar(avatar_config)
        stats = avatar_engine.get_statistics()
        assert stats["total_avatars"] == 1
        
    @pytest.mark.asyncio
    async def test_avatar_config_validation(self):
        """Test avatar configuration validation"""
        config = AvatarConfig()
        
        # Test default values
        assert config.gender == AvatarGender.NEUTRAL
        assert config.ethnicity == AvatarEthnicity.CAUCASIAN
        assert config.body_type == AvatarBodyType.AVERAGE
        assert config.age == 30
        assert config.accessories == []
        
        # Test custom values
        config = AvatarConfig(
            gender=AvatarGender.MALE,
            ethnicity=AvatarEthnicity.AFRICAN,
            body_type=AvatarBodyType.MUSCULAR,
            age=45,
            accessories=["hat", "glasses"]
        )
        
        assert config.gender == AvatarGender.MALE
        assert config.ethnicity == AvatarEthnicity.AFRICAN
        assert config.body_type == AvatarBodyType.MUSCULAR
        assert config.age == 45
        assert config.accessories == ["hat", "glasses"]

@pytest.mark.asyncio
async def test_multiple_avatars():
    """Test creating multiple avatars"""
    engine = PhotorealisticAvatarEngine()
    await engine.initialize()
    
    configs = [
        AvatarConfig(gender=AvatarGender.MALE, age=25),
        AvatarConfig(gender=AvatarGender.FEMALE, age=35),
        AvatarConfig(gender=AvatarGender.NEUTRAL, age=40)
    ]
    
    avatar_ids = []
    for i, config in enumerate(configs):
        avatar_id = await engine.create_avatar(config, f"avatar_{i}")
        avatar_ids.append(avatar_id)
        
    assert len(avatar_ids) == 3
    assert len(engine.list_avatars()) == 3
    
@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent avatar operations"""
    engine = PhotorealisticAvatarEngine()
    await engine.initialize()
    
    config = AvatarConfig()
    
    # Create multiple avatars concurrently
    tasks = [
        engine.create_avatar(config, f"concurrent_{i}")
        for i in range(5)
    ]
    
    avatar_ids = await asyncio.gather(*tasks)
    assert len(avatar_ids) == 5
    assert len(engine.list_avatars()) == 5

if __name__ == "__main__":
    pytest.main([__file__])