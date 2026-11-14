"""
Challenge Loader Service

Loads challenge definitions from the filesystem into the database.
Scans /challenges directory for metadata.json files and populates the challenges table.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""
import json
import os
from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Challenge


class ChallengeLoader:
    """Service for loading challenge definitions from filesystem"""
    
    def __init__(self, challenges_dir: str = "/challenges"):
        """
        Initialize the challenge loader.
        
        Args:
            challenges_dir: Path to the challenges directory
        """
        self.challenges_dir = Path(challenges_dir)
        
        # For development, if /challenges doesn't exist, try relative path
        if not self.challenges_dir.exists():
            self.challenges_dir = Path(__file__).parent.parent.parent.parent / "challenges"
    
    def scan_challenges(self) -> List[Dict]:
        """
        Scan the challenges directory for challenge definitions.
        
        Returns:
            List of challenge metadata dictionaries
            
        Requirements: 7.6 - Load all challenge definitions on startup
        """
        challenges = []
        
        if not self.challenges_dir.exists():
            print(f"Warning: Challenges directory not found at {self.challenges_dir}")
            return challenges
        
        # Iterate through subdirectories in challenges directory
        for challenge_dir in self.challenges_dir.iterdir():
            if not challenge_dir.is_dir():
                continue
                
            metadata_file = challenge_dir / "metadata.json"
            
            if not metadata_file.exists():
                print(f"Warning: No metadata.json found in {challenge_dir.name}")
                continue
            
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Validate required fields
                required_fields = ['id', 'title', 'difficulty', 'brief']
                if not all(field in metadata for field in required_fields):
                    print(f"Warning: Missing required fields in {challenge_dir.name}/metadata.json")
                    continue
                
                challenges.append(metadata)
                print(f"Loaded challenge: {metadata['id']} - {metadata['title']}")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing {challenge_dir.name}/metadata.json: {e}")
                continue
            except Exception as e:
                print(f"Error loading challenge {challenge_dir.name}: {e}")
                continue
        
        return challenges
    
    def load_challenges_to_db(self, db: Session) -> int:
        """
        Load all challenges from filesystem into the database.
        
        This method:
        1. Scans the challenges directory
        2. Creates or updates challenge records in the database
        3. Stores metadata as JSON string
        
        Args:
            db: Database session
            
        Returns:
            Number of challenges loaded
            
        Requirements: 7.6 - Platform SHALL load all challenge definitions on startup
        """
        challenges = self.scan_challenges()
        count = 0
        
        for challenge_data in challenges:
            # Check if challenge already exists
            existing = db.query(Challenge).filter(Challenge.id == challenge_data['id']).first()
            
            # Serialize full metadata to JSON for storage
            metadata_json = json.dumps(challenge_data)
            
            if existing:
                # Update existing challenge
                existing.title = challenge_data['title']
                existing.difficulty = challenge_data['difficulty']
                existing.brief = challenge_data['brief']
                existing.metadata = metadata_json
            else:
                # Create new challenge
                new_challenge = Challenge(
                    id=challenge_data['id'],
                    title=challenge_data['title'],
                    difficulty=challenge_data['difficulty'],
                    brief=challenge_data['brief'],
                    metadata=metadata_json
                )
                db.add(new_challenge)
            
            count += 1
        
        db.commit()
        print(f"Successfully loaded {count} challenges into database")
        return count


def load_challenges(db: Session) -> int:
    """
    Convenience function to load challenges using default loader.
    
    Args:
        db: Database session
        
    Returns:
        Number of challenges loaded
    """
    loader = ChallengeLoader()
    return loader.load_challenges_to_db(db)
