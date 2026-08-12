import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.fixture
def normal_user_token_headers(client: TestClient) -> dict:
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal@example.com",
        "password": "Password123!"
    })
    res = client.post("/api/auth/login", json={
        "email": "normal@example.com",
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superuser_token_headers(client: TestClient) -> dict:
    client.post("/api/auth/register", json={
        "name": "Super User",
        "email": "super@example.com",
        "password": "Password123!"
    })
    res = client.post("/api/auth/login", json={
        "email": "super@example.com",
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_repository_authenticated(client: TestClient, db: Session, normal_user_token_headers: dict):
    response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={
            "name": "test-repo",
            "url": "https://github.com/example/test-repo",
            "description": "A test repository"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-repo"
    assert data["url"] == "https://github.com/example/test-repo"
    assert data["provider"] == "github"
    assert "id" in data
    assert "created_at" in data

def test_create_repository_unauthenticated(client: TestClient, db: Session):
    response = client.post(
        "/api/repositories",
        json={
            "name": "test-repo",
            "url": "https://github.com/example/test-repo"
        }
    )
    assert response.status_code == 401

def test_create_repository_invalid_url(client: TestClient, db: Session, normal_user_token_headers: dict):
    response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={
            "name": "test-repo",
            "url": "https://gitlab.com/example/test-repo"
        }
    )
    assert response.status_code == 422
    
    response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={
            "name": "test-repo",
            "url": "https://github.com/example"
        }
    )
    assert response.status_code == 422

def test_list_repositories(client: TestClient, db: Session, normal_user_token_headers: dict):
    client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo1", "url": "https://github.com/ex/repo1"}
    )
    client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo2", "url": "https://github.com/ex/repo2"}
    )
    
    response = client.get("/api/repositories", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert len(data["repositories"]) >= 2
    names = [r["name"] for r in data["repositories"]]
    assert "repo1" in names
    assert "repo2" in names

def test_get_repository(client: TestClient, db: Session, normal_user_token_headers: dict):
    create_response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo3", "url": "https://github.com/ex/repo3"}
    )
    repo_id = create_response.json()["id"]
    
    response = client.get(f"/api/repositories/{repo_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "repo3"

def test_get_another_user_repository(
    client: TestClient, 
    db: Session, 
    normal_user_token_headers: dict, 
    superuser_token_headers: dict
):
    create_response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo4", "url": "https://github.com/ex/repo4"}
    )
    repo_id = create_response.json()["id"]
    
    response = client.get(f"/api/repositories/{repo_id}", headers=superuser_token_headers)
    assert response.status_code == 404

def test_update_repository(client: TestClient, db: Session, normal_user_token_headers: dict):
    create_response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo5", "url": "https://github.com/ex/repo5"}
    )
    repo_id = create_response.json()["id"]
    
    update_response = client.patch(
        f"/api/repositories/{repo_id}",
        headers=normal_user_token_headers,
        json={"name": "repo5-updated", "description": "New description"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "repo5-updated"
    assert update_response.json()["description"] == "New description"
    assert update_response.json()["url"] == "https://github.com/ex/repo5"

def test_delete_repository(client: TestClient, db: Session, normal_user_token_headers: dict):
    create_response = client.post(
        "/api/repositories",
        headers=normal_user_token_headers,
        json={"name": "repo6", "url": "https://github.com/ex/repo6"}
    )
    repo_id = create_response.json()["id"]
    
    delete_response = client.delete(f"/api/repositories/{repo_id}", headers=normal_user_token_headers)
    assert delete_response.status_code == 200
    
    get_response = client.get(f"/api/repositories/{repo_id}", headers=normal_user_token_headers)
    assert get_response.status_code == 404
