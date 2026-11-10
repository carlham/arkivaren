import pytest
from sqlalchemy.orm import Session

from app.db import engine


@pytest.fixture
def db():
    """A session whose changes are rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()
