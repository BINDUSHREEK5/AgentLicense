"""Test suite for AgentLicense backend - real x402 integration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.models import Base
from app.db.database import get_db
from app.licensing.license_service import create_license
from app.agents.decision_engine import select_best_license
from app.models import LicenseOption, AgentRequirement


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture
def db_session(test_engine):
    """Create database session for tests."""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """Create test client."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# === Health & Status Tests ===

class TestHealth:
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "environment" in data
        assert "database" in data


class TestX402Status:
    def test_x402_status_endpoint(self, client):
        """Test x402 status reporting endpoint."""
        response = client.get("/x402/status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "facilitator_url" in data
        assert "network" in data
        assert "tiers" in data


# === Resource Discovery Tests ===

class TestResources:
    def test_list_resources(self, client):
        """Test listing resources."""
        response = client.get("/resources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_resource(self, client):
        """Test getting specific resource."""
        response = client.get("/resources/market-dataset-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "market-dataset-001"

    def test_get_license_options(self, client):
        """Test getting license options for resource."""
        response = client.get("/resources/market-dataset-001/licenses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least single, multi, commercial

    def test_preview_resource(self, client):
        """Test previewing resource (no license required)."""
        response = client.get("/resources/market-dataset-001/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["requires_license"] is True


# === License Tests ===

class TestLicenses:
    def test_create_license(self, db_session):
        """Test creating a license."""
        license_obj = create_license(
            db=db_session,
            resource_id="test-resource",
            buyer="test-buyer",
            seller="test-seller",
            price=0.01,
            usage_limit=5,
        )
        assert license_obj.id is not None
        assert license_obj.uses_remaining == 5

    def test_test_fixture_license(self, client):
        """Test creating a test-fixture license via API."""
        response = client.post(
            "/licenses/market-dataset-001/create-test-fixture",
            json={"usage_limit": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "license_id" in data
        assert data["uses_remaining"] == 3
        assert "TESTFIXTURE" in data.get("note", "")

    def test_agent_decision_no_compatible(self, client):
        """Test agent decision when no compatible license exists."""
        response = client.post(
            "/licenses/market-dataset-001/select",
            json={
                "task": "Test task",
                "budget": 0.001,  # Too low
                "required_uses": 100,
                "commercial_use_required": True,
            },
        )
        assert response.status_code == 400

    def test_agent_decision_compatible(self, client):
        """Test agent decision when compatible license exists."""
        response = client.post(
            "/licenses/market-dataset-001/select",
            json={
                "task": "Test task",
                "budget": 0.25,
                "required_uses": 5,
                "commercial_use_required": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "selected_license_id" in data
        assert data["confidence"] == 1.0


# === Protected Resource Tests ===

class TestProtectedResources:
    def test_access_without_license_returns_402(self, client):
        """Test accessing protected resource without license returns 402."""
        response = client.get("/resources/market-dataset-001/access")
        assert response.status_code == 402
        data = response.json()
        assert "license_required" in data["status"]
        assert "purchase_endpoint" in data

    def test_access_with_invalid_license_returns_403(self, client):
        """Test accessing with invalid license returns 403."""
        response = client.get(
            "/resources/market-dataset-001/access",
            headers={"license-id": "invalid-license-id"},
        )
        assert response.status_code == 403

    def test_access_with_valid_license_works(self, client, db_session):
        """Test accessing resource with valid license."""
        # Create a real license
        lic = create_license(
            db=db_session,
            resource_id="market-dataset-001",
            buyer="test-agent",
            seller="test-provider",
            price=0.01,
            usage_limit=2,
        )

        # Access resource
        response = client.get(
            "/resources/market-dataset-001/access",
            headers={"license-id": lic.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["uses_remaining"] == 1  # One usage consumed

    def test_usage_exhaustion(self, client, db_session):
        """Test license exhaustion after all uses consumed."""
        # Create license with 1 use
        lic = create_license(
            db=db_session,
            resource_id="market-dataset-001",
            buyer="test-agent",
            seller="test-provider",
            price=0.01,
            usage_limit=1,
        )

        # First access succeeds
        response1 = client.get(
            "/resources/market-dataset-001/access",
            headers={"license-id": lic.id},
        )
        assert response1.status_code == 200
        assert response1.json()["uses_remaining"] == 0

        # Second access fails (exhausted)
        response2 = client.get(
            "/resources/market-dataset-001/access",
            headers={"license-id": lic.id},
        )
        assert response2.status_code == 403


# === Agent Decision Engine Tests ===

class TestAgentEngine:
    def test_license_compatibility_check(self):
        """Test license compatibility evaluation."""
        from app.agents.decision_engine import evaluate_license_compatibility

        license_opt = LicenseOption(
            license_id="test",
            name="Test",
            description="",
            price=0.05,
            usage_limit=10,
            commercial_use=True,
            redistribution_allowed=False,
            training_allowed=False,
        )

        requirement = AgentRequirement(
            task="Test",
            budget=0.10,
            required_uses=5,
            commercial_use_required=True,
        )

        compatible, reasons = evaluate_license_compatibility(license_opt, requirement)
        assert compatible is True

    def test_license_selection(self):
        """Test agent selects cheapest compatible license."""
        licenses = [
            LicenseOption(
                license_id="expensive",
                name="Expensive",
                description="",
                price=0.15,
                usage_limit=10,
                commercial_use=True,
                redistribution_allowed=False,
                training_allowed=False,
            ),
            LicenseOption(
                license_id="cheap",
                name="Cheap",
                description="",
                price=0.05,
                usage_limit=10,
                commercial_use=True,
                redistribution_allowed=False,
                training_allowed=False,
            ),
        ]

        requirement = AgentRequirement(
            task="Test",
            budget=0.20,
            required_uses=5,
            commercial_use_required=True,
        )

        decision, _ = select_best_license(licenses, requirement)
        assert decision is not None
        assert decision.selected_license_id == "cheap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])