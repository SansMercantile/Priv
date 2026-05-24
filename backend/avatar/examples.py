"""
Usage examples for the avatar system
"""
import asyncio
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any

from .avatar_engine import (
    PhotorealisticAvatarEngine,
    AvatarConfig,
    AvatarGender,
    AvatarEthnicity,
    AvatarBodyType,
    AvatarAnimation
)
from .person_cloner import (
    PersonCloner,
    PersonData
)

class AvatarExamples:
    """Comprehensive usage examples for the avatar system"""
    
    def __init__(self):
        self.avatar_engine = PhotorealisticAvatarEngine()
        self.person_cloner = PersonCloner()
        
    async def initialize(self):
        """Initialize all systems"""
        await self.avatar_engine.initialize()
        await self.person_cloner.initialize()
        
    async def basic_avatar_creation(self):
        """Basic avatar creation example"""
        print("=== Basic Avatar Creation ===")
        
        # Create a basic avatar configuration
        config = AvatarConfig(
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
        
        # Create the avatar
        avatar_id = await self.avatar_engine.create_avatar(config, "business_woman")
        
        print(f"Created avatar: {avatar_id}")
        print(f"Avatar config: {config}")
        
        return avatar_id
        
    async def custom_avatar_creation(self):
        """Custom avatar creation with specific traits"""
        print("\n=== Custom Avatar Creation ===")
        
        # Create a custom avatar
        config = AvatarConfig(
            gender=AvatarGender.MALE,
            ethnicity=AvatarEthnicity.AFRICAN,
            body_type=AvatarBodyType.MUSCULAR,
            age=35,
            height=1.85,
            face_shape="square",
            eye_color="green",
            hair_color="dark_brown",
            hair_style="short",
            skin_tone="dark",
            outfit="athletic",
            accessories=["headband", "fitness_tracker"]
        )
        
        avatar_id = await self.avatar_engine.create_avatar(config, "athlete")
        
        print(f"Created custom avatar: {avatar_id}")
        print(f"Configuration: {json.dumps(config.__dict__, indent=2)}")
        
        return avatar_id
        
    async def avatar_animation_example(self):
        """Avatar animation example"""
        print("\n=== Avatar Animation ===")
        
        # Create avatar first
        config = AvatarConfig(gender=AvatarGender.NEUTRAL, age=25)
        avatar_id = await self.avatar_engine.create_avatar(config, "animated_avatar")
        
        # Create animation
        animation = AvatarAnimation(
            animation_type="greeting",
            duration=2.0,
            keyframes=[
                {"time": 0, "pose": "standing", "expression": "neutral"},
                {"time": 1.0, "pose": "waving", "expression": "happy"},
                {"time": 2.0, "pose": "standing", "expression": "neutral"}
            ],
            loop=False
        )
        
        result = await self.avatar_engine.animate_avatar(avatar_id, animation)
        
        print(f"Animated avatar {avatar_id} with greeting animation")
        print(f"Animation result: {result}")
        
    async def facial_expression_example(self):
        """Facial expression animation example"""
        print("\n=== Facial Expression Animation ===")
        
        # Create avatar
        config = AvatarConfig(gender=AvatarGender.FEMALE, age=30)
        avatar_id = await self.avatar_engine.create_avatar(config, "expressive_avatar")
        
        # Animate expressions
        expressions = ["happy", "sad", "surprised", "angry", "neutral"]
        
        for expression in expressions:
            result = await avatar_engine.animate_facial_expression(
                avatar_id, 
                expression, 
                intensity=0.8
            )
            print(f"Expression '{expression}': {result}")
            
    async def lip_sync_example(self):
        """Lip sync animation example"""
        print("\n=== Lip Sync Animation ===")
        
        # Create avatar
        config = AvatarConfig(gender=AvatarGender.MALE, age=40)
        avatar_id = await self.avatar_engine.create_avatar(config, "speaker_avatar")
        
        # Create sample audio data (sine wave)
        duration = 3.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Generate lip sync
        result = await self.avatar_engine.lip_sync(
            avatar_id, 
            audio_data, 
            "Hello, this is a test of the lip sync system."
        )
        
        print(f"Generated lip sync for avatar {avatar_id}")
        print(f"Lip sync result: {result}")
        
    async def avatar_rendering_example(self):
        """Avatar rendering example"""
        print("\n=== Avatar Rendering ===")
        
        # Create avatar
        config = AvatarConfig(gender=AvatarGender.FEMALE, age=25)
        avatar_id = await self.avatar_engine.create_avatar(config, "render_avatar")
        
        # Render with default settings
        image = await self.avatar_engine.render_avatar(avatar_id)
        
        print(f"Rendered avatar {avatar_id}")
        print(f"Image shape: {image.shape}")
        print(f"Image dtype: {image.dtype}")
        
        # Render with custom camera
        camera_config = {
            "position": [0, 0, 3],
            "rotation": [0, 0, 0],
            "fov": 60
        }
        
        lighting_config = {
            "ambient": [0.4, 0.4, 0.4],
            "directional": [[1, 1, 1], [0.8, 0.8, 0.8]]
        }
        
        image_custom = await self.avatar_engine.render_avatar(
            avatar_id,
            camera_config=camera_config,
            lighting_config=lighting_config
        )
        
        print(f"Rendered avatar with custom settings")
        print(f"Custom image shape: {image_custom.shape}")
        
    async def basic_clone_creation(self):
        """Basic person cloning example"""
        print("\n=== Basic Person Cloning ===")
        
        # Create sample person data
        person_data = PersonData(
            images=["/path/to/image1.jpg", "/path/to/image2.jpg"],
            videos=["/path/to/video1.mp4"],
            social_media_posts=[
                {
                    "platform": "twitter",
                    "content": "Just finished a great workout! Feeling energized.",
                    "timestamp": "2024-01-15T09:00:00",
                    "engagement": {"likes": 15, "shares": 3}
                },
                {
                    "platform": "linkedin",
                    "content": "Excited to share insights on AI and personal development.",
                    "timestamp": "2024-01-14T14:30:00",
                    "engagement": {"likes": 45, "comments": 8}
                }
            ],
            emails=[
                {
                    "subject": "Weekly team update",
                    "body": "Team, here are this week's accomplishments...",
                    "timestamp": "2024-01-12T16:00:00"
                }
            ],
            voice_notes=["/path/to/voice1.wav"],
            personal_documents=["/path/to/resume.pdf", "/path/to/blog_post.txt"]
        )
        
        # Create clone
        person_id = await self.person_cloner.create_clone(
            "Jane Smith",
            person_data,
            "jane.smith@example.com"
        )
        
        print(f"Created clone for Jane Smith: {person_id}")
        
        return person_id
        
    async def advanced_clone_creation(self):
        """Advanced cloning with comprehensive data"""
        print("\n=== Advanced Person Cloning ===")
        
        # Create comprehensive person data
        person_data = PersonData(
            images=[
                "/photos/profile_pic.jpg",
                "/photos/vacation_2023.jpg",
                "/photos/family_gathering.jpg",
                "/photos/work_event.jpg"
            ],
            videos=[
                "/videos/presentation.mp4",
                "/videos/family_vacation.mp4",
                "/videos/birthday_celebration.mp4"
            ],
            social_media_posts=[
                {
                    "platform": "instagram",
                    "content": "Beautiful sunset at the beach today! Nature never fails to amaze.",
                    "timestamp": "2024-01-10T18:30:00",
                    "engagement": {"likes": 120, "comments": 15}
                },
                {
                    "platform": "twitter",
                    "content": "Just finished reading 'Atomic Habits' - game changer for productivity!",
                    "timestamp": "2024-01-08T20:15:00",
                    "engagement": {"likes": 25, "retweets": 8}
                },
                {
                    "platform": "linkedin",
                    "content": "Reflecting on 5 years in tech leadership. Key lesson: empathy drives innovation.",
                    "timestamp": "2024-01-05T09:00:00",
                    "engagement": {"likes": 200, "comments": 35}
                }
            ],
            emails=[
                {
                    "subject": "Project milestone celebration",
                    "body": "Team, I'm thrilled to announce we've exceeded our Q1 targets...",
                    "timestamp": "2024-01-15T10:00:00"
                },
                {
                    "subject": "Mentorship program launch",
                    "body": "Dear team, we're launching our internal mentorship program...",
                    "timestamp": "2024-01-10T14:00:00"
                }
            ],
            voice_notes=[
                "/audio/meeting_notes_2024_01_15.wav",
                "/audio/idea_recording_2024_01_12.wav",
                "/audio/birthday_message.wav"
            ],
            personal_documents=[
                "/documents/career_goals_2024.txt",
                "/documents/personal_manifesto.md",
                "/documents/fitness_tracker_data.csv"
            ]
        )
        
        # Create advanced clone
        person_id = await self.person_cloner.create_clone(
            "Alex Johnson",
            person_data,
            "alex.johnson@example.com"
        )
        
        print(f"Created advanced clone for Alex Johnson: {person_id}")
        
        # Get clone profile
        clone = self.person_cloner.get_clone(person_id)
        if clone:
            print(f"Clone personality traits:")
            for trait, value in clone.personality_traits.items():
                print(f"  {trait}: {value}")
                
            print(f"Clone creation time: {clone.created_at}")
            
        return person_id
        
    async def clone_integration_example(self):
        """Example of integrating clone with avatar"""
        print("\n=== Clone-Avatar Integration ===")
        
        # Create clone
        person_data = PersonData(
            images=["/photos/profile.jpg"],
            social_media_posts=[{
                "platform": "twitter",
                "content": "Love outdoor activities and photography!",
                "timestamp": "2024-01-01T12:00:00"
            }]
        )
        
        person_id = await self.person_cloner.create_clone(
            "Sarah Wilson",
            person_data,
            "sarah.wilson@example.com"
        )
        
        # Get clone profile
        clone = self.person_cloner.get_clone(person_id)
        
        if clone:
            # Create avatar based on clone profile
            config = AvatarConfig(
                gender=AvatarGender.FEMALE,
                ethnicity=AvatarEthnicity.CAUCASIAN,
                body_type=AvatarBodyType.ATHLETIC,
                age=28,
                outfit="casual",
                accessories=["camera", "backpack"]
            )
            
            avatar_id = await self.avatar_engine.create_avatar(
                config, 
                f"avatar_{clone.name.lower().replace(' ', '_')}"
            )
            
            print(f"Created avatar {avatar_id} based on clone {person_id}")
            print(f"Clone: {clone.name}")
            print(f"Avatar: {avatar_id}")
            
            return {"clone_id": person_id, "avatar_id": avatar_id}
            
    async def batch_operations_example(self):
        """Example of batch operations"""
        print("\n=== Batch Operations ===")
        
        # Create multiple avatars
        avatar_configs = [
            AvatarConfig(gender=AvatarGender.MALE, age=25, outfit="business"),
            AvatarConfig(gender=AvatarGender.FEMALE, age=30, outfit="casual"),
            AvatarConfig(gender=AvatarGender.NEUTRAL, age=35, outfit="athletic")
        ]
        
        avatar_tasks = [
            self.avatar_engine.create_avatar(config, f"batch_{i}")
            for i, config in enumerate(avatar_configs)
        ]
        
        avatar_ids = await asyncio.gather(*avatar_tasks)
        print(f"Created {len(avatar_ids)} avatars: {avatar_ids}")
        
        # Create multiple clones
        clone_configs = [
            ("John Doe", "john@example.com"),
            ("Jane Smith", "jane@example.com"),
            ("Mike Johnson", "mike@example.com")
        ]
        
        clone_tasks = []
        for name, email in clone_configs:
            person_data = PersonData(
                images=[f"/photos/{name.lower().replace(' ', '_')}.jpg"]
            )
            clone_tasks.append(
                self.person_cloner.create_clone(name, person_data, email)
            )
        
        clone_ids = await asyncio.gather(*clone_tasks)
        print(f"Created {len(clone_ids)} clones: {clone_ids}")
        
        return {"avatars": avatar_ids, "clones": clone_ids}
        
    async def run_all_examples(self):
        """Run all usage examples"""
        print("Starting Avatar System Usage Examples...")
        await self.initialize()
        
        # Run examples
        await self.basic_avatar_creation()
        await self.custom_avatar_creation()
        await self.avatar_animation_example()
        await self.facial_expression_example()
        await self.lip_sync_example()
        await self.avatar_rendering_example()
        await self.basic_clone_creation()
        await self.advanced_clone_creation()
        await self.clone_integration_example()
        await self.batch_operations_example()
        
        print("\n=== System Statistics ===")
        avatar_stats = self.avatar_engine.get_statistics()
        clone_stats = self.person_cloner.get_clone_statistics()
        
        print("Avatar System:", json.dumps(avatar_stats, indent=2))
        print("Clone System:", json.dumps(clone_stats, indent=2))
        
        print("\nAll examples completed successfully!")

# CLI interface
async def main():
    """Main CLI interface"""
    examples = AvatarExamples()
    await examples.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())