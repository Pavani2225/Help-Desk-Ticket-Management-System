
import pytest

from werkzeug.security import generate_password_hash

from helpdesk import create_app
from helpdesk.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test.sqlite"

    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DATABASE": str(database_path),
        "SECRET_KEY": "test-secret-key",
    })

    with app.app_context():
        init_db()

        database = get_db()

        database.execute(
            """
            INSERT INTO users (
                username, password_hash, full_name, email, role
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "admin",
                generate_password_hash("Admin@123"),
                "Test Admin",
                "admin@test.com",
                "admin",
            ),
        )

        database.execute(
            """
            INSERT INTO users (
                username, password_hash, full_name, email, role
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "technician",
                generate_password_hash("Tech@123"),
                "Test Technician",
                "tech@test.com",
                "technician",
            ),
        )

        database.commit()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "Admin@123",
        },
    )

    return client
