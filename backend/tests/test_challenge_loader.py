"""
Unit tests for the Challenge Loader Service

Tests the functionality of loading challenge definitions from the filesystem
and populating the database.

Requirements: 7.1, 7.6
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.challenge_loader import ChallengeLoader
from app.models import Challenge


@pytest.fixture
def temp_challenges_dir():
    """Create a temporary challenges directory with test challenges"""
    temp_dir = tempfile.mkdtemp()
    challenges_path = Path(temp_dir)
    
    # Create test challenge 1
    challenge1_dir = challenges_path / "test-challenge-1"
    challenge1_dir.mkdir()
    metadata1 = {
        "id": "test-challenge-1",
        "title": "Test Challenge 1",
        "difficulty": "easy",
        "brief": "This is a test challenge",
        "hints": ["Hint 1", "Hint 2"]
    }
    with open(challenge1_dir / "metadata.json", 'w') as f:
        json.dump(metadata1, f)
    
    # Create test challenge 2
    challenge2_dir = challenges_path / "test-challenge-2"
    challenge2_dir.mkdir()
    metadata2 = {
        "id": "test-challenge-2",
        "title": "Test Challenge 2",
        "difficulty": "medium",
        "brief": "This is another test challenge"
    }
    with open(challenge2_dir / "metadata.json", 'w') as f:
        json.dump(metadata2, f)
    
    # Create invalid challenge (missing required fields)
    challenge3_dir = challenges_path / "invalid-challenge"
    challenge3_dir.mkdir()
    metadata3 = {
        "id": "invalid-challenge",
        "title": "Invalid Challenge"
        # Missing difficulty and brief
    }
    with open(challenge3_dir / "metadata.json", 'w') as f:
        json.dump(metadata3, f)
    
    # Create directory without metadata
    empty_dir = challenges_path / "empty-challenge"
    empty_dir.mkdir()
    
    yield str(challenges_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


class TestChallengeLoader:
    """Test suite for ChallengeLoader service"""
    
    def test_scan_challenges_success(self, temp_challenges_dir):
        """Test scanning challenges from filesystem"""
        loader = ChallengeLoader(temp_challenges_dir)
        challenges = loader.scan_challenges()
        
        # Should load only valid challenges (2 valid, 1 invalid, 1 empty)
        assert len(challenges) == 2
        
        # Verify challenge 1
        challenge1 = next(c for c in challenges if c['id'] == 'test-challenge-1')
        assert challenge1['title'] == 'Test Challenge 1'
        assert challenge1['difficulty'] == 'easy'
        assert challenge1['brief'] == 'This is a test challenge'
        assert 'hints' in challenge1
        
        # Verify challenge 2
        challenge2 = next(c for c in challenges if c['id'] == 'test-challenge-2')
        assert challenge2['title'] == 'Test Challenge 2'
        assert challenge2['difficulty'] == 'medium'
    
    def test_scan_challenges_nonexistent_directory(self):
        """Test scanning when challenges directory doesn't exist"""
        # Use a path that definitely doesn't exist and won't have a fallback
        loader = ChallengeLoader("/definitely/nonexistent/path/that/does/not/exist")
        # Override the fallback path to also be nonexistent
        loader.challenges_dir = Path("/definitely/nonexistent/path/that/does/not/exist")
        challenges = loader.scan_challenges()
        
        # Should return empty list without crashing
        assert len(challenges) == 0
    
    def test_load_challenges_to_db(self, temp_challenges_dir, db_session):
        """Test loading challenges into database"""
        loader = ChallengeLoader(temp_challenges_dir)
        count = loader.load_challenges_to_db(db_session)
        
        # Should load 2 valid challenges
        assert count == 2
        
        # Verify challenges in database
        db_challenges = db_session.query(Challenge).all()
        assert len(db_challenges) == 2
        
        # Verify challenge data
        challenge1 = db_session.query(Challenge).filter(
            Challenge.id == 'test-challenge-1'
        ).first()
        assert challenge1 is not None
        assert challenge1.title == 'Test Challenge 1'
        assert challenge1.difficulty == 'easy'
        assert challenge1.brief == 'This is a test challenge'
        assert challenge1.metadata is not None
        
        # Verify metadata is valid JSON
        metadata = json.loads(challenge1.metadata)
        assert metadata['id'] == 'test-challenge-1'
        assert 'hints' in metadata
    
    def test_load_challenges_updates_existing(self, temp_challenges_dir, db_session):
        """Test that reloading challenges updates existing records"""
        loader = ChallengeLoader(temp_challenges_dir)
        
        # First load
        count1 = loader.load_challenges_to_db(db_session)
        assert count1 == 2
        
        # Modify challenge metadata
        challenge1_dir = Path(temp_challenges_dir) / "test-challenge-1"
        metadata = {
            "id": "test-challenge-1",
            "title": "Updated Test Challenge 1",
            "difficulty": "hard",
            "brief": "This is an updated test challenge"
        }
        with open(challenge1_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        # Reload challenges
        loader2 = ChallengeLoader(temp_challenges_dir)
        count2 = loader2.load_challenges_to_db(db_session)
        assert count2 == 2
        
        # Verify update
        challenge1 = db_session.query(Challenge).filter(
            Challenge.id == 'test-challenge-1'
        ).first()
        assert challenge1.title == 'Updated Test Challenge 1'
        assert challenge1.difficulty == 'hard'
        
        # Should still have only 2 challenges, not 4
        db_challenges = db_session.query(Challenge).all()
        assert len(db_challenges) == 2
    
    def test_load_challenges_handles_empty_directory(self, db_session):
        """Test loading from empty challenges directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = ChallengeLoader(temp_dir)
            count = loader.load_challenges_to_db(db_session)
            
            assert count == 0
            db_challenges = db_session.query(Challenge).all()
            assert len(db_challenges) == 0
