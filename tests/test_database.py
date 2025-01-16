import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contacts_api.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_db(test_db):
    result = list(get_db())
    assert len(result) == 1
    assert result[0].bind == test_db.bind
