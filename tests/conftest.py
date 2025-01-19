import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contacts_api.database import Base, get_db
from contacts_api.models import User, Base
from contacts_api.utils import hash_password
from contacts_api.main import app

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    Base.metadata.create_all(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def test_db(test_engine):
    connection = test_engine.connect()
    Session = sessionmaker(bind=connection)
    db = Session()
    yield db
    db.close()
    connection.close()

@pytest.fixture
def override_get_db(db_session):
    def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = _get_db_override

@pytest.fixture
def test_user(db_session: Session):
    email = "testuser@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, password=hashed_password, full_name="Test User", is_verified=True)
    db_session.add(user)
    db_session.commit()
    return user
