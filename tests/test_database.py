import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contacts_api.database import Base, get_db

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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

def test_db():
    engine = create_engine(DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()