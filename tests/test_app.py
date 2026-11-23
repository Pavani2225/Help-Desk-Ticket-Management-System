
def test_application_starts(app):
    assert app is not None


def test_login_page_loads(client):
    response = client.get("/auth/login")

    assert response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302


def test_valid_login(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_invalid_login(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "WrongPassword",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Incorrect username or password." in response.data


def test_authenticated_dashboard(logged_in_client):
    response = logged_in_client.get("/")

    assert response.status_code == 200
