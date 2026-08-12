import uuid
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, name: str = "Test User") -> dict:
    """Register a user, log in, and return Authorization headers."""
    client.post("/api/auth/register", json={
        "name": name,
        "email": email,
        "password": "SecurePassword123!"
    })
    response = client.post("/api/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_repository(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {
        "name": "backend-api",
        "url": "https://github.com/example/backend-api",
        "provider": "github",
        "default_branch": "main",
        "description": "Backend API"
    }
    payload.update(overrides)
    response = client.post("/api/repositories", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Repository Creation
# ---------------------------------------------------------------------------

class TestRepositoryCreation:
    def test_authenticated_user_can_create_repository(self, client: TestClient):
        headers = register_and_login(client, "creator@example.com")
        data = create_repository(client, headers)
        assert data["name"] == "backend-api"
        assert data["url"] == "https://github.com/example/backend-api"
        assert data["provider"] == "github"
        assert data["default_branch"] == "main"
        assert data["description"] == "Backend API"
        assert data["is_active"] is True
        assert data["last_scan_at"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "user_id" not in data

    def test_unauthenticated_user_cannot_create_repository(self, client: TestClient):
        response = client.post("/api/repositories", json={
            "name": "backend-api",
            "url": "https://github.com/example/backend-api"
        })
        assert response.status_code == 401

    def test_valid_github_url_accepted(self, client: TestClient):
        headers = register_and_login(client, "validurl@example.com")
        data = create_repository(client, headers, url="https://github.com/my-org/my.repo_name")
        assert data["url"] == "https://github.com/my-org/my.repo_name"

    def test_trailing_slash_url_normalized(self, client: TestClient):
        headers = register_and_login(client, "trailing@example.com")
        data = create_repository(client, headers, url="https://github.com/example/repo/")
        assert data["url"] == "https://github.com/example/repo"

    def test_invalid_url_rejected(self, client: TestClient):
        headers = register_and_login(client, "invalidurl@example.com")
        invalid_urls = [
            "not-a-url",
            "http://github.com/example/repo",           # http not allowed
            "https://gitlab.com/example/repo",          # wrong host
            "https://github.com/onlyowner",             # missing repo segment
            "https://github.com@evil.com/example/repo", # credential trick
            "https://github.com:8080/example/repo",     # port not allowed
            "https://github.com/example/repo?a=b",      # query string
            "ftp://github.com/example/repo",
            "https://evilgithub.com/example/repo",
        ]
        for url in invalid_urls:
            response = client.post("/api/repositories", json={
                "name": "repo",
                "url": url
            }, headers=headers)
            assert response.status_code == 422, f"URL should be rejected: {url}"

    def test_missing_name_rejected(self, client: TestClient):
        headers = register_and_login(client, "noname@example.com")
        response = client.post("/api/repositories", json={
            "url": "https://github.com/example/repo"
        }, headers=headers)
        assert response.status_code == 422

    def test_empty_name_rejected(self, client: TestClient):
        headers = register_and_login(client, "emptyname@example.com")
        for name in ["", "   "]:
            response = client.post("/api/repositories", json={
                "name": name,
                "url": "https://github.com/example/repo"
            }, headers=headers)
            assert response.status_code == 422

    def test_name_too_long_rejected(self, client: TestClient):
        headers = register_and_login(client, "longname@example.com")
        response = client.post("/api/repositories", json={
            "name": "a" * 101,
            "url": "https://github.com/example/repo"
        }, headers=headers)
        assert response.status_code == 422

    def test_name_whitespace_trimmed(self, client: TestClient):
        headers = register_and_login(client, "trimname@example.com")
        data = create_repository(client, headers, name="  my-repo  ")
        assert data["name"] == "my-repo"

    def test_missing_url_rejected(self, client: TestClient):
        headers = register_and_login(client, "nourl@example.com")
        response = client.post("/api/repositories", json={
            "name": "repo"
        }, headers=headers)
        assert response.status_code == 422

    def test_invalid_provider_rejected(self, client: TestClient):
        headers = register_and_login(client, "badprovider@example.com")
        response = client.post("/api/repositories", json={
            "name": "repo",
            "url": "https://github.com/example/repo",
            "provider": "bitbucket"
        }, headers=headers)
        assert response.status_code == 422

    def test_defaults_applied(self, client: TestClient):
        headers = register_and_login(client, "defaults@example.com")
        response = client.post("/api/repositories", json={
            "name": "repo",
            "url": "https://github.com/example/repo"
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "github"
        assert data["default_branch"] == "main"
        assert data["description"] is None


# ---------------------------------------------------------------------------
# Repository Listing
# ---------------------------------------------------------------------------

class TestRepositoryListing:
    def test_user_can_list_own_repositories(self, client: TestClient):
        headers = register_and_login(client, "lister@example.com")
        create_repository(client, headers, name="repo-one", url="https://github.com/example/repo-one")
        create_repository(client, headers, name="repo-two", url="https://github.com/example/repo-two")

        response = client.get("/api/repositories", headers=headers)
        assert response.status_code == 200
        repos = response.json()["repositories"]
        assert len(repos) == 2
        names = {r["name"] for r in repos}
        assert names == {"repo-one", "repo-two"}

    def test_empty_list_works(self, client: TestClient):
        headers = register_and_login(client, "emptylist@example.com")
        response = client.get("/api/repositories", headers=headers)
        assert response.status_code == 200
        assert response.json()["repositories"] == []

    def test_user_cannot_see_other_users_repositories(self, client: TestClient):
        headers_a = register_and_login(client, "owner-a@example.com")
        headers_b = register_and_login(client, "owner-b@example.com")
        create_repository(client, headers_a, name="a-repo", url="https://github.com/a/a-repo")

        response = client.get("/api/repositories", headers=headers_b)
        assert response.status_code == 200
        assert response.json()["repositories"] == []

    def test_unauthenticated_cannot_list(self, client: TestClient):
        response = client.get("/api/repositories")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Repository Retrieval
# ---------------------------------------------------------------------------

class TestRepositoryRetrieval:
    def test_user_can_retrieve_own_repository(self, client: TestClient):
        headers = register_and_login(client, "getter@example.com")
        created = create_repository(client, headers)

        response = client.get(f"/api/repositories/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]
        assert response.json()["name"] == "backend-api"

    def test_unknown_repository_returns_404(self, client: TestClient):
        headers = register_and_login(client, "unknown@example.com")
        response = client.get(f"/api/repositories/{uuid.uuid4()}", headers=headers)
        assert response.status_code == 404

    def test_other_users_repository_returns_404(self, client: TestClient):
        headers_a = register_and_login(client, "priv-a@example.com")
        headers_b = register_and_login(client, "priv-b@example.com")
        created = create_repository(client, headers_a)

        response = client.get(f"/api/repositories/{created['id']}", headers=headers_b)
        assert response.status_code == 404
        assert response.json()["detail"] == "Repository not found"

    def test_unauthenticated_cannot_retrieve(self, client: TestClient):
        response = client.get(f"/api/repositories/{uuid.uuid4()}")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Repository Update
# ---------------------------------------------------------------------------

class TestRepositoryUpdate:
    def test_user_can_update_own_repository(self, client: TestClient):
        headers = register_and_login(client, "updater@example.com")
        created = create_repository(client, headers)

        response = client.patch(f"/api/repositories/{created['id']}", json={
            "name": "renamed-repo",
            "default_branch": "develop",
            "description": "Updated description",
            "is_active": False
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "renamed-repo"
        assert data["default_branch"] == "develop"
        assert data["description"] == "Updated description"
        assert data["is_active"] is False
        assert data["url"] == created["url"]

    def test_partial_update(self, client: TestClient):
        headers = register_and_login(client, "partial@example.com")
        created = create_repository(client, headers)

        response = client.patch(f"/api/repositories/{created['id']}", json={
            "name": "only-name-changed"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "only-name-changed"
        assert data["default_branch"] == created["default_branch"]
        assert data["description"] == created["description"]

    def test_user_cannot_update_other_users_repository(self, client: TestClient):
        headers_a = register_and_login(client, "upd-a@example.com")
        headers_b = register_and_login(client, "upd-b@example.com")
        created = create_repository(client, headers_a)

        response = client.patch(f"/api/repositories/{created['id']}", json={
            "name": "hijacked"
        }, headers=headers_b)
        assert response.status_code == 404

        # Verify owner's repository is untouched
        response = client.get(f"/api/repositories/{created['id']}", headers=headers_a)
        assert response.json()["name"] == "backend-api"

    def test_invalid_values_rejected(self, client: TestClient):
        headers = register_and_login(client, "badvalues@example.com")
        created = create_repository(client, headers)

        for payload in [
            {"name": ""},
            {"name": "   "},
            {"name": "a" * 101},
            {"default_branch": ""},
            {"is_active": "not-a-bool"},
        ]:
            response = client.patch(
                f"/api/repositories/{created['id']}",
                json=payload,
                headers=headers
            )
            assert response.status_code == 422, f"Payload should be rejected: {payload}"

    def test_url_is_immutable(self, client: TestClient):
        headers = register_and_login(client, "immutable@example.com")
        created = create_repository(client, headers)

        response = client.patch(f"/api/repositories/{created['id']}", json={
            "url": "https://github.com/evil/other-repo"
        }, headers=headers)
        assert response.status_code == 422

        response = client.get(f"/api/repositories/{created['id']}", headers=headers)
        assert response.json()["url"] == created["url"]

    def test_protected_fields_cannot_be_changed(self, client: TestClient):
        headers = register_and_login(client, "protected@example.com")
        created = create_repository(client, headers)

        for payload in [
            {"id": str(uuid.uuid4())},
            {"user_id": str(uuid.uuid4())},
            {"created_at": "2020-01-01T00:00:00Z"},
        ]:
            response = client.patch(
                f"/api/repositories/{created['id']}",
                json=payload,
                headers=headers
            )
            assert response.status_code == 422, f"Payload should be rejected: {payload}"

    def test_unauthenticated_cannot_update(self, client: TestClient):
        response = client.patch(f"/api/repositories/{uuid.uuid4()}", json={"name": "x"})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Repository Delete
# ---------------------------------------------------------------------------

class TestRepositoryDelete:
    def test_user_can_delete_own_repository(self, client: TestClient):
        headers = register_and_login(client, "deleter@example.com")
        created = create_repository(client, headers)

        response = client.delete(f"/api/repositories/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Repository deleted successfully"

    def test_user_cannot_delete_other_users_repository(self, client: TestClient):
        headers_a = register_and_login(client, "del-a@example.com")
        headers_b = register_and_login(client, "del-b@example.com")
        created = create_repository(client, headers_a)

        response = client.delete(f"/api/repositories/{created['id']}", headers=headers_b)
        assert response.status_code == 404

        # Repository still exists for owner
        response = client.get(f"/api/repositories/{created['id']}", headers=headers_a)
        assert response.status_code == 200

    def test_deleted_repository_cannot_be_retrieved(self, client: TestClient):
        headers = register_and_login(client, "gone@example.com")
        created = create_repository(client, headers)

        client.delete(f"/api/repositories/{created['id']}", headers=headers)

        response = client.get(f"/api/repositories/{created['id']}", headers=headers)
        assert response.status_code == 404

        response = client.get("/api/repositories", headers=headers)
        assert response.json()["repositories"] == []

    def test_unauthenticated_cannot_delete(self, client: TestClient):
        response = client.delete(f"/api/repositories/{uuid.uuid4()}")
        assert response.status_code == 401
