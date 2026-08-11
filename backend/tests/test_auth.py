from datetime import timedelta
from fastapi.testclient import TestClient
from app.core.security import create_access_token


def test_register_user_success(client: TestClient):
    """Test successful user registration."""
    payload = {
        "name": "Guardrail Admin",
        "email": "admin@guardrail.security",
        "password": "SecurePassword123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully"


def test_register_user_duplicate_email(client: TestClient):
    """Test registration rejection for duplicate email."""
    payload = {
        "name": "Test User",
        "email": "dup@example.com",
        "password": "Password123!"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_user_invalid_email(client: TestClient):
    """Test registration rejection for invalid email format."""
    payload = {
        "name": "Invalid Email",
        "email": "not-an-email",
        "password": "Password123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_register_user_weak_password(client: TestClient):
    """Test registration rejection for password under 8 characters."""
    payload = {
        "name": "Short Pass",
        "email": "short@example.com",
        "password": "123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client: TestClient):
    """Test login with valid credentials."""
    reg_payload = {
        "name": "Login User",
        "email": "login@example.com",
        "password": "ValidPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_payload = {
        "email": "login@example.com",
        "password": "ValidPassword123!"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Test login failure with incorrect password."""
    reg_payload = {
        "name": "Login User",
        "email": "wrongpass@example.com",
        "password": "ValidPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@example.com",
        "password": "WrongPassword123!"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_unknown_email(client: TestClient):
    """Test login failure for unknown email."""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user_authenticated(client: TestClient):
    """Test getting profile for authenticated user with valid JWT."""
    reg_payload = {
        "name": "Profile User",
        "email": "profile@example.com",
        "password": "ValidPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post("/api/auth/login", json={"email": "profile@example.com", "password": "ValidPassword123!"})
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["name"] == "Profile User"
    assert data["email"] == "profile@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_unauthenticated(client: TestClient):
    """Test rejection when no Authorization header is provided."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_jwt(client: TestClient):
    """Test rejection when invalid JWT is provided."""
    headers = {"Authorization": "Bearer invalid.token.value"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_get_current_user_expired_jwt(client: TestClient):
    """Test rejection when expired JWT is provided."""
    reg_payload = {
        "name": "Expired User",
        "email": "expired@example.com",
        "password": "ValidPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)
    login_res = client.post("/api/auth/login", json={"email": "expired@example.com", "password": "ValidPassword123!"})
    
    # Generate expired token
    me_res = client.get("/api/auth/me", headers={"Authorization": "Bearer " + login_res.json()["access_token"]})
    user_id = me_res.json()["id"]

    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
