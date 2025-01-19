import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contacts_api.database import Base, get_db
from contacts_api.main import app

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def engine():
    test_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)

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
    assert test_db.bind is not None

@pytest.fixture
def test_db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    db = SessionLocal()
    yield db
    db.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def override_get_db(test_db):
    def _override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides[get_db] = None
