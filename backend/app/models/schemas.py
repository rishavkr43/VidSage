# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional


class IngestResponse(BaseModel):
    status: str
    video_id: str
    chunks: int = Field(..., description="Number of text chunks created for this video")


class QueryRequest(BaseModel):
    session_id: str
    video_id: str
    question: str


class QueryResponse(BaseModel):
    answer: str
    source_chunks: Optional[list] = Field(None, description="Optional list of context snippets used")
