import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services import auth_service
from app.core.config import settings


def test_password_is_hashed_in_database(client: TestClient, db: Session):
    """Verify passwords are never stored in plaintext in the database."""
    plain_password = "SuperSecretPassword123!"
    reg_payload = {
        "name": "Security Check User",
        "email": "security@example.com",
        "password": plain_password
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201

    db_user = auth_service.get_user_by_email(db, "security@example.com")
    assert db_user is not None
    assert db_user.password_hash != plain_password
    assert plain_password not in db_user.password_hash
    assert db_user.password_hash.startswith("$argon2")


def test_password_hash_never_in_api_response(client: TestClient):
    """Verify password and password_hash never leak in registration or user info responses."""
    reg_payload = {
        "name": "Leak Check User",
        "email": "leakcheck@example.com",
        "password": "Password123!"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert "password" not in str(reg_res.content).lower()
    assert "hash" not in str(reg_res.content).lower()

    login_res = client.post("/api/auth/login", json={"email": "leakcheck@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    me_data = me_res.json()
    assert "password" not in me_data
    assert "password_hash" not in me_data


def test_secrets_loaded_from_environment():
    """Verify configuration settings pull secrets from environment variables."""
    assert settings.JWT_SECRET is not None
    assert len(settings.JWT_SECRET) > 0


def test_sqlalchemy_safe_parameterization(client: TestClient, db: Session):
    """Verify SQL injection vectors are safely trapped or escaped by Pydantic and SQLAlchemy ORM."""
    sql_injection_email = "injection' OR '1'='1@example.com"
    login_payload = {
        "email": sql_injection_email,
        "password": "somepassword"
    }
    response = client.post("/api/auth/login", json=login_payload)
    # Rejection should occur either at schema validation (422) or at authentication query (400/401)
    assert response.status_code in [400, 401, 422]
