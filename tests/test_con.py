import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, get_db
from app.models import Base
from app.security import get_current_account_claims

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False,)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def client(monkeypatch):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account_claims] = lambda: {"account_no": "A12345"}
    import app.main as main

    monkeypatch.setattr(main, "validate_account_exists", lambda account_no: None)
    monkeypatch.setattr(main, "generate_label_pdf", lambda con: None)

    # Need unique consignment numbers per create to avoid DB unique constraint
    con_counter = {"n": 1}

    async def fake_next_con_num(account_no: str) -> int:
        n = con_counter["n"]
        con_counter["n"] += 1
        return n

    async def fake_resolve_depot(county: str) -> int:
        return 31

    monkeypatch.setattr(main, "get_next_con_num", fake_next_con_num)
    monkeypatch.setattr(main, "resolve_depot_number", fake_resolve_depot)

    with TestClient(app) as c:
        yield c

    
    app.dependency_overrides.clear()



def con_payload(
    account_no="A12345",
    name="Anto",
    addressline1="50 Valleycourt",
    addressline2="Dublin Road",
    addressline3="Athlone",
    addressline4="Westmeath",
    weight=1,
):
    
    return {
        "account_no": account_no,
        "name": name,
        "addressline1": addressline1,
        "addressline2": addressline2,
        "addressline3": addressline3,
        "addressline4": addressline4,
        "weight": weight,
    }


# Tests
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_con_201(client):
    r = client.post("/api/consignment", json=con_payload())
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["account_no"] == "A12345"
    assert data["consignment_number"] == 1
    assert data["delivery_depot"] == 31


def test_get_con_by_consignment_number_200(client):
    client.post("/api/consignment", json=con_payload())
    r = client.get("/api/consignment/1")  
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["account_no"] == "A12345"
    assert data["name"] == "Anto"
    assert data["addressline1"] == "50 Valleycourt"
    assert data["addressline2"] == "Dublin Road"
    assert data["addressline3"] == "Athlone"
    assert data["addressline4"] == "Westmeath"
    assert data["weight"] == 1
    assert data["consignment_number"] == 1
    assert data["delivery_depot"] == 31


def test_get_con_not_found_404(client):
    r = client.get("/api/consignment/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Consignment not found"


def test_weight_limit_422(client):
    r = client.post("/api/consignment", json=con_payload(weight=151))
    assert r.status_code == 422


def test_edit_con_200(client):
    client.post("/api/consignment", json=con_payload())
    edit_payload = {
        "account_no": "A12345", 
        "name": "Conor",
    }
    r = client.patch("/api/consignment/1", json=edit_payload)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Conor"

    # confirm persisted
    r2 = client.get("/api/consignment/1")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Conor"


def test_edit_con_recalculates_depot_when_county_changes(client, monkeypatch):
    # Override depot resolver to prove the "addressline4 changed" 
    import app.main as main

    async def fake_resolve_depot(county: str) -> int:
        return 44

    monkeypatch.setattr(main, "resolve_depot_number", fake_resolve_depot)

    client.post("/api/consignment", json=con_payload(addressline4="Westmeath"))
    edit_payload = {
        "account_no": "A12345",
        "addressline4": "Offaly",
    }
    r = client.patch("/api/consignment/1", json=edit_payload)
    assert r.status_code == 200, r.text
    assert r.json()["delivery_depot"] == 44


def test_edit_con_not_found_404(client):
    r = client.patch("/api/consignment/999", json={"account_no": "A12345", "name": "Conor"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Consignment not found"


def test_delete_con_204(client):
    client.post("/api/consignment", json=con_payload())
    r = client.delete("/api/consignment/1")
    assert r.status_code == 204

    r2 = client.get("/api/consignment/1")
    assert r2.status_code == 404


def test_delete_con_not_found_404(client):
    r = client.delete("/api/consignment/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Consignment not found"


def test_auth_forbidden_when_token_account_differs(client):
    app.dependency_overrides[get_current_account_claims] = lambda: {"account_no": "A99999"}

    client.post("/api/consignment", json=con_payload(account_no="A12345"))
    r = client.get("/api/consignment/1")
    assert r.status_code == 403
    assert r.json()["detail"] == "Token not valid for this account"

