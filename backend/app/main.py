# backend/app/main.py
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os;
from app.models.schemas import IngestResponse, QueryRequest, QueryResponse
from app.services import transcript, sessions, rag
from app.deps import EMB_PROVIDER, LLM_PROVIDER

app = FastAPI(title="VidSage Backend", version="0.1.0")

# Allow local testing from the extension. In production restrict origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only. Replace with extension domain or specific origin in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


@app.post("/ingest/{video_id}", response_model=IngestResponse)
def ingest_video(video_id: str):
    """
    Ingest a video: fetch its transcript, split, embed and index.
    Idempotent: re-running will overwrite the in-memory index for that video.
    """
    try:
        text = transcript.fetch_transcript_text(video_id, languages=["en"])
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch transcript: {e}")

    try:
        num_chunks = rag.ingest_video_to_index(video_id, text, EMB_PROVIDER, rag.INDEXES)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {e}")

    return IngestResponse(status="ok", video_id=video_id, chunks=num_chunks)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    Query the ingested video. Must have ingested the video first.
    session_id is used to keep conversational context.
    """
    if req.video_id not in rag.INDEXES:
        raise HTTPException(status_code=404, detail="Video not ingested. Call /ingest/{video_id} first.")

    # Retrieve session history & append question
    history = sessions.get_history(req.session_id)

    try:
        answer, snippets = rag.answer_question(req.video_id, history, req.question, EMB_PROVIDER, LLM_PROVIDER, rag.INDEXES)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {e}")

    # append turns (persist conversation history)
    sessions.append_turn(req.session_id, "user", req.question)
    sessions.append_turn(req.session_id, "assistant", answer)

    return QueryResponse(answer=answer, source_chunks=snippets)


@app.get("/health")
def health():
    return {"status": "ok", "provider_dummy": getattr(EMB_PROVIDER, "__class__", None).__name__}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # for deployment on cloud environment.
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
