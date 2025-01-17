import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contacts_api.database import Base, get_db
from contacts_api.models import User
from contacts_api.utils import hash_password

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def override_get_db(db_session):
    def _override():
        yield db_session
    return _override

@pytest.fixture
def test_user(db_session: Session):
    email = "testuser@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, password=hashed_password, full_name="Test User", is_verified=True)
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    yield session
    transaction.rollback()
    connection.close()
