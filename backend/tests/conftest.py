"""
Pytest configuration for all tests
Sets up environment variables before any imports
"""
import os
import pytest


def pytest_configure(config):
    """Configure pytest - runs before any tests"""
    # Load API key from .env if not already set
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        try:
            env_path = os.path.join(os.path.dirname(__file__), "../../.env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ANTHROPIC_API_KEY="):
                            key = line.split("=", 1)[1].strip()
                            os.environ["ANTHROPIC_API_KEY"] = key
                            print(f"✅ Loaded ANTHROPIC_API_KEY from .env")
                            break
                        elif line.startswith("OPENAI_API_KEY="):
                            key = line.split("=", 1)[1].strip()
                            os.environ["OPENAI_API_KEY"] = key
                            print(f"✅ Loaded OPENAI_API_KEY from .env")
                            break
        except Exception as e:
            print(f"⚠️  Could not load API key from .env: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment - runs once per test session"""
    # Ensure API key is available
    has_key = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
    
    if not has_key:
        pytest.exit("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
    
    print(f"\n✅ Test environment ready")
    print(f"   API Provider: {'Anthropic' if os.getenv('ANTHROPIC_API_KEY') else 'OpenAI'}")
    
    yield
    
    print(f"\n✅ Test session completed")


@pytest.fixture(scope="function")
def db():
    """Create a database session for testing"""
    from backend.app.database.session import get_db, engine
    from backend.app.database.models import Base
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Get DB session
    db_session = next(get_db())
    
    yield db_session
    
    # Cleanup
    db_session.close()


@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database"""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.main import app
    from backend.app.database.models import Base
    from backend.app.database.session import get_db
    
    # Test database
    TEST_DATABASE_URL = "sqlite:///./test_categories.db"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestClient(app)
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("test_categories.db"):
        os.remove("test_categories.db")


@pytest.fixture(scope="function")
def auth_headers(client):
    """Create test user and return auth headers"""
    # Register test user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
