# backend/tests/test_rag.py
from app.services import rag
from typing import List


class SimpleEmbeddingProvider:
    # returns fixed-length vectors (floats) for each text
    def embed_documents(self, texts: List[str]):
        # vector length 8, simple deterministic embedding for tests
        return [[float(len(t) % 10) for _ in range(8)] for t in texts]


def test_ingest_and_retrieve(tmp_path):
    video_id = "vid_test_123"
    # create a long-ish text so the splitter produces chunks
    text = "word " * 1500

    indexes_map = {}
    emb = SimpleEmbeddingProvider()

    num_chunks = rag.ingest_video_to_index(video_id, text, emb, indexes_map)
    assert num_chunks > 0
    assert video_id in indexes_map

    # retrieve documents for a question
    docs = rag.retrieve_docs_for_question(video_id, "any question", indexes_map, k=2)
    assert isinstance(docs, list)
    assert len(docs) <= 2
    # each doc should be a langchain Document-like object with .page_content
    assert hasattr(docs[0], "page_content")
