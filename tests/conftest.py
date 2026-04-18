"""Shared pytest fixtures.

The global Flask `app` is a module-level singleton created at import time,
so SQLAlchemy's engine is cached across tests. To get per-test isolation
we dispose the engine, point it at a fresh tempfile database, and
recreate the schema inside each test's application context.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as _app  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    _app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SECRET_KEY='test-secret-key',
    )

    with _app.app_context():
        # Dispose any cached engine so SQLAlchemy picks up the new URI.
        db.engine.dispose()
        db.drop_all()
        db.create_all()

    with _app.test_client() as test_client:
        yield test_client

    with _app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    os.close(db_fd)
    os.unlink(db_path)
