# backend/app/services/rag.py
from typing import Dict, Any, List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

# In-memory store mapping video_id -> FAISS index wrapper
INDEXES: Dict[str, Any] = {}


class EmbeddingsAdapter:
    """
    Adapter that exposes:
      - embed_documents(list[str]) -> list[list[float]]  (used when indexing documents)
      - __call__(text: str) -> list[float]               (used when embedding a query)
    Delegates to common method names on the provided embeddings provider:
      - embed_documents, embed_texts, embed_query, or the provider being callable.
    """

    def __init__(self, inner: Any):
        self.inner = inner

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Preferred methods
        if hasattr(self.inner, "embed_documents"):
            return self.inner.embed_documents(texts)
        if hasattr(self.inner, "embed_texts"):
            return self.inner.embed_texts(texts)
        # If the inner is callable and expects a list, try calling it
        if callable(self.inner):
            out = self.inner(texts)
            # If it returns a single vector for a string, this may be wrong shape; assume the provider knows what it does
            return out
        raise TypeError("Embedding provider must implement 'embed_documents' or 'embed_texts' or be callable")

    def __call__(self, text: str) -> list[float]:
        # Preferred dedicated query embedding
        if hasattr(self.inner, "embed_query"):
            return self.inner.embed_query(text)
        # If only embed_texts exists, use it with a single-element list
        if hasattr(self.inner, "embed_texts"):
            vecs = self.inner.embed_texts([text])
            return vecs[0]
        if hasattr(self.inner, "embed_documents"):
            vecs = self.inner.embed_documents([text])
            return vecs[0]
        # If inner is callable and can handle a single string, call it
        if callable(self.inner):
            out = self.inner(text)
            # If provider returned list-of-vectors for list input earlier, here it may return a vector or list; try to normalize
            if isinstance(out, list) and len(out) and isinstance(out[0], (list, tuple)):
                return out[0]
            return out
        raise TypeError("Embedding provider does not support query embedding (no embed_query/embed_texts/embed_documents/callable)")

    def __repr__(self):
        return f"EmbeddingsAdapter(inner={type(self.inner)})"


def _split_text_to_docs(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = splitter.create_documents([text])
    return docs


def ingest_video_to_index(video_id: str, text: str, embeddings_provider: Any, existing_indexes: Dict[str, Any]) -> int:
    """
    Splits transcript text into chunks, embeds and indexes using FAISS via LangChain wrapper.
    Stores index in existing_indexes dict under video_id.
    Returns number of chunks.
    """
    docs = _split_text_to_docs(text)
    if not docs:
        raise ValueError("No docs created from transcript")

    adapter = EmbeddingsAdapter(embeddings_provider)

    logger.info("Indexing %d docs for video %s", len(docs), video_id)
    index = FAISS.from_documents(docs, adapter)
    # Sanity-check: ensure FAISS has a callable embedding function for queries
    try:
        if not callable(getattr(index, "embedding_function", adapter)):
            logger.warning("FAISS index.embedding_function is not callable; adapter=%s", adapter)
    except Exception:
        # ignore sanity-check failures
        pass

    existing_indexes[video_id] = index
    return len(docs)


def _sync_invoke_retriever(retriever: Any, question: str, k: int) -> List[Document]:
    """
    Synchronously get relevant documents from a retriever, trying modern and legacy APIs.
    """
    try:
        # Modern preferred sync API
        if hasattr(retriever, "invoke"):
            return retriever.invoke(question)
        # If only async exists, try to run it (but warn if running inside an event loop)
        if hasattr(retriever, "ainvoke"):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                raise RuntimeError("Retriever only supports async 'ainvoke'; call retrieve_docs_for_question_async from async context.")
            else:
                return asyncio.run(retriever.ainvoke(question))

        # Some retrievers are callable (older styles)
        if callable(retriever):
            return retriever(question)

        # Old API fallback
        if hasattr(retriever, "get_relevant_documents"):
            return retriever.get_relevant_documents(question)

        # Try __call__ explicitly
        try:
            return retriever.__call__(question)
        except Exception:
            pass

        raise AttributeError("Retriever has no known invocation method (invoke/ainvoke/get_relevant_documents/callable).")
    except Exception:
        logger.exception("Failed to fetch documents from retriever for question=%s", question)
        raise


async def _async_invoke_retriever(retriever: Any, question: str, k: int) -> List[Document]:
    """
    Async variant: prefer ainvoke, otherwise call invoke in thread or fallback to sync methods.
    """
    try:
        if hasattr(retriever, "ainvoke"):
            return await retriever.ainvoke(question)
        if hasattr(retriever, "invoke"):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: retriever.invoke(question))
        if callable(retriever):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: retriever(question))
        if hasattr(retriever, "get_relevant_documents"):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: retriever.get_relevant_documents(question))
        raise AttributeError("Retriever has no known invocation method (ainvoke/invoke/get_relevant_documents/callable).")
    except Exception:
        logger.exception("Async: Failed to fetch documents from retriever for question=%s", question)
        raise


def retrieve_docs_for_question(video_id: str, question: str, existing_indexes: Dict[str, Any], k: int = 4) -> List[Document]:
    """
    Retrieve top-k documents for a given question using the stored index.
    This is a synchronous helper — if you are in an async FastAPI endpoint, consider
    calling retrieve_docs_for_question_async instead.
    """
    if video_id not in existing_indexes:
        raise KeyError("No index found for video_id: " + video_id)

    index = existing_indexes[video_id]
    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})

    docs = _sync_invoke_retriever(retriever, question, k)
    return docs


async def retrieve_docs_for_question_async(video_id: str, question: str, existing_indexes: Dict[str, Any], k: int = 4) -> List[Document]:
    """
    Async version to be used inside async endpoints.
    """
    if video_id not in existing_indexes:
        raise KeyError("No index found for video_id: " + video_id)

    index = existing_indexes[video_id]
    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})

    docs = await _async_invoke_retriever(retriever, question, k)
    return docs


def build_prompt(retrieved_docs: List[Document], convo_history: List[dict], question: str) -> str:
    """
    Build the final prompt for the LLM. We follow the requirement:
    - Answer ONLY from the provided transcript context.
    - If the context is insufficient, say 'I don't know.'
    We include a short recent conversation history.
    """
    system = (
        "You are VidSage — a helpful assistant that answers strictly from the provided transcript CONTEXT. "
        "If the transcript context is insufficient to answer, respond with exactly: \"I don't know.\" "
        "Keep answers concise and factual."
    )

    context_text = "\n\n".join([d.page_content for d in retrieved_docs]) if retrieved_docs else ""
    history_text = ""
    if convo_history:
        pairs = []
        for h in convo_history[-6:]:
            role = h.get("role", "user")
            text = h.get("text", "")
            pairs.append(f"{role.upper()}: {text}")
        history_text = "\n\n".join(pairs)

    prompt = f"{system}\n\nCONTEXT:\n{context_text}\n\nHISTORY:\n{history_text}\n\nQUESTION:\n{question}\n\nAnswer:"
    return prompt


def _extract_answer_from_llm_result(result: Any) -> str:
    """
    Extract a human-readable answer from different LLM provider return shapes.
    Handles:
      - plain string
      - objects with .generations (LangChain generate)
      - objects with .text or .content
      - fallback to str(result)
    """
    try:
        if isinstance(result, str):
            return result
        if hasattr(result, "generations"):
            gens = getattr(result, "generations")
            try:
                first = gens[0][0]
                return getattr(first, "text", str(first))
            except Exception:
                return str(result)
        if hasattr(result, "text"):
            return getattr(result, "text")
        if hasattr(result, "content"):
            return getattr(result, "content")
        return str(result)
    except Exception:
        logger.exception("Failed to extract text from llm_provider result: %s", type(result))
        return str(result)


def answer_question(video_id: str, session_history: List[dict], question: str, embeddings_provider: Any, llm_provider: Any, indexes_map: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Retrieve context and ask the LLM to answer. Returns answer text and list of source snippets.
    Synchronous version.
    """
    retrieved = retrieve_docs_for_question(video_id, question, indexes_map, k=4)
    prompt = build_prompt(retrieved, session_history, question)

    try:
        result = llm_provider.generate(prompt)
    except Exception:
        logger.exception("LLM provider failed to generate for prompt (truncated): %.200s", prompt)
        raise

    answer = _extract_answer_from_llm_result(result)

    snippets = [ (d.page_content[:400] + ("..." if len(d.page_content) > 400 else "")) for d in retrieved ]
    return answer, snippets
