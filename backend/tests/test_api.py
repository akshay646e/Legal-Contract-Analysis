import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Legal Contract Analysis" in data["service"]

def test_upload_and_analyze_contract():
    # 1. Upload sample NDA
    with open("sample_contracts/nda_mutual.txt", "rb") as f:
        res = client.post(
            "/api/contracts/upload",
            files={"file": ("nda_mutual.txt", f, "text/plain")}
        )
    assert res.status_code == 201
    contract = res.json()
    contract_id = contract["id"]
    assert contract["filename"] == "nda_mutual.txt"
    assert contract["status"] == "INDEXED"

    # 2. Run analysis pipeline
    analysis_res = client.post(f"/api/analysis/{contract_id}/full-pipeline")
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()
    assert "summary" in analysis
    assert "clauses" in analysis
    assert "risks" in analysis

    # 3. Ask RAG Question with citation
    chat_res = client.post(
        "/api/chat",
        json={
            "contract_id": contract_id,
            "message": "What is the governing law of this agreement?",
            "include_citations": True
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["reply"]) > 0
    assert len(chat_data["citations"]) > 0

    # 4. Check stats
    stats_res = client.get("/api/contracts/stats/overview")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_contracts"] >= 1
