import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, get_db
from app.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False,)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # hand the client to the test
        yield c


def con_payload(name="Anthony", addressline1="50 Valleycourt", addressline2= "Dublin Road",
                addressline3= "Athlone", addressline4="Westmeath", weight=1):
    return{
        "name": name,
        "addressline1": addressline1,
        "addressline2": addressline2,
        "addressline3": addressline3,
        "addressline4": addressline4,
        "weight": weight
    }

def test_create_con(client):
    r = client.post("/api/consignment", json=con_payload())
    assert r.status_code==201

def test_get_con_by_id(client):
    r = client.post("/api/consignment", json=con_payload())
    r = client.get("/api/consignment/1")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Anthony"
    assert data["addressline1"] == "50 Valleycourt"
    assert data["addressline2"] == "Dublin Road"
    assert data["addressline3"] == "Athlone"
    assert data["addressline4"] == "Westmeath"
    assert data["weight"] == 1

def test_weight_limit(client):
    r = client.post("/api/consignment", json=con_payload(weight=151))
    assert r.status_code == 422

def test_edit_con(client):
    r = client.post("/api/consignment", json=con_payload())
    r = client.patch("/api/consignment/2", json=con_payload(name="Conor"))
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Conor"
    r = client.get("/api/consignment/2")
    data = r.json()
    assert data["name"] == "Conor"

def test_edit_con_not_found(client):
    r = client.patch("/api/consignment/999", json=con_payload(name="Conor"))
    assert r.status_code == 404

def test_delete_con(client):
    r = client.post("/api/consignment", json=con_payload())
    r = client.delete("/api/consignment/3")
    assert r.status_code == 204
    r = client.get("/api/consignment/3")
    assert r.status_code == 404

def test_delete_con_not_found(client):
    r = client.delete("/api/consignment/999")
    assert r.status_code == 404