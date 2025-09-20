# backend/tests/test_api.py
import uuid
from fastapi.testclient import TestClient
import app.main as main_mod


class FakeEmb:
    def embed_documents(self, texts):
        # produce a simple fixed-length embedding for each chunk
        return [[0.1] * 8 for _ in texts]


class FakeLLM:
    def generate(self, prompt: str) -> str:
        # obey our system instruction: if "fusion" in CONTEXT -> say yes; else "I don't know."
        if "fusion" in prompt.lower():
            return "Yes — nuclear fusion was mentioned in the transcript."
        return "I don't know."


def test_ingest_and_query_flow(monkeypatch):
    # 1) Monkeypatch transcript.fetch_transcript_text to avoid network calls
    sample_transcript = "This transcript mentions nuclear fusion and experimental reactors."
    monkeypatch.setattr(main_mod.transcript, "fetch_transcript_text", lambda video_id, languages=None: sample_transcript)

    # 2) Replace providers with fakes so indexing/LLM don't need external APIs
    monkeypatch.setattr(main_mod, "EMB_PROVIDER", FakeEmb())
    monkeypatch.setattr(main_mod, "LLM_PROVIDER", FakeLLM())
    # Also ensure rag.INDEXES is fresh empty dict
    from app import services
    services.rag.INDEXES.clear()

    client = TestClient(main_mod.app)

    video_id = "test_vid_api_1"
    # call ingest
    resp = client.post(f"/ingest/{video_id}")
    assert resp.status_code == 200, resp.text
    j = resp.json()
    assert j["status"] == "ok"
    assert j["video_id"] == video_id
    assert j["chunks"] > 0

    # now query
    session_id = str(uuid.uuid4())
    payload = {"session_id": session_id, "video_id": video_id, "question": "Was fusion discussed?"}
    qresp = client.post("/query", json=payload)
    assert qresp.status_code == 200, qresp.text
    data = qresp.json()
    assert "answer" in data
    assert "fusion" in data["answer"].lower() or data["answer"].lower() == "i don't know."
