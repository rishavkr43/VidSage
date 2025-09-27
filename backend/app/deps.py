# backend/app/deps.py
import os
from typing import Any, List
from dotenv import load_dotenv

load_dotenv()

# Important: set GOOGLE_API_KEY in backend/.env or in your environment BEFORE running
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)
USE_DUMMY = os.environ.get("USE_DUMMY_PROVIDER", "false").lower() in ("1", "true", "yes")

# We'll create simple wrappers that try to use Google Generative AI (Gemini) via the
# official google.generativeai package when available. If not installed or key missing,
# a dummy provider is used for quick local dev/testing.

class EmbeddingsProvider:
    """Abstract interface for embeddings provider."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class LLMProvider:
    """Abstract interface for chat/LLM provider."""
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


# Try to load google generative ai if user requested Gemini
if not USE_DUMMY:
    try:
        import google.generativeai as genai  # pip install google-generativeai
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY not set in env; set it before running.")
        genai.configure(api_key=GOOGLE_API_KEY)

        class GeminiEmbeddings(EmbeddingsProvider):
            def __init__(self, model_name: str = "models/text-embedding-004"):
                # Updated to use the correct embedding model name
                # Options: "models/text-embedding-004" or "models/embedding-001"
                self.model_name = model_name

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                # Use the correct API for embeddings
                embeddings = []
                for text in texts:
                    result = genai.embed_content(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document"  # or "retrieval_query" for queries
                    )
                    embeddings.append(result['embedding'])
                return embeddings

        class GeminiLLM(LLMProvider):
            def __init__(self, model_name: str = "gemini-2.0-flash"):
                # Updated model name - use "gemini-1.5-flash" or "gemini-1.5-pro"
                self.model = genai.GenerativeModel(model_name)

            def generate(self, prompt: str) -> str:
                # Use the correct generate_content method
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    print(f"Error generating response: {e}")
                    return "I encountered an error generating a response."

        EMB_PROVIDER: EmbeddingsProvider = GeminiEmbeddings()
        LLM_PROVIDER: LLMProvider = GeminiLLM()
        print(f"Successfully initialized Gemini providers with API key")

    except Exception as e:
        # If any error occurs (missing package, missing key, etc.) fall back to dummy
        print(f"Warning: Could not initialize Gemini providers: {e}")
        USE_DUMMY = True

if USE_DUMMY:
    # Simple dummy implementations for fast local dev – not production or accurate.
    # These allow the backend to run so you can integrate the extension UI and test flows.
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        class DummyEmbeddings(EmbeddingsProvider):
            def __init__(self):
                self._vectorizer = None
                self._fitted = False

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                if not self._fitted:
                    self._vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
                    self._vectorizer.fit(texts)
                    self._fitted = True
                
                # Transform texts to embeddings
                mat = self._vectorizer.transform(texts).toarray()
                # Pad or truncate to fixed size (384 dimensions to match typical embedding size)
                embeddings = []
                for row in mat:
                    if len(row) < 384:
                        # Pad with zeros if needed
                        padded = np.pad(row, (0, 384 - len(row)), 'constant')
                        embeddings.append(padded.tolist())
                    else:
                        embeddings.append(row[:384].tolist())
                return embeddings

        class DummyLLM(LLMProvider):
            def generate(self, prompt: str) -> str:
                # Very naive response for dev
                if "CONTEXT:" in prompt:
                    context = prompt.split("CONTEXT:")[1].split("HISTORY:")[0] if "HISTORY:" in prompt else prompt.split("CONTEXT:")[1]
                    # Extract question if present
                    if "Question:" in prompt:
                        question = prompt.split("Question:")[-1].strip()
                        # Provide slightly more intelligent dummy responses
                        if any(word in question.lower() for word in ["what", "explain", "describe"]):
                            return "Based on the video content, this topic was discussed but I'm running in dummy mode so cannot provide specific details."
                        elif any(word in question.lower() for word in ["when", "where", "who"]):
                            return "The video mentions this, but specific details require the full AI model."
                        elif any(word in question.lower() for word in ["is", "are", "does", "can"]):
                            return "According to the video, yes - but I'm in dummy mode so cannot elaborate."
                return "I don't have enough information from the video to answer that question."

        EMB_PROVIDER = DummyEmbeddings()
        LLM_PROVIDER = DummyLLM()
        print("Using dummy providers (no API key or package missing)")
        
    except ImportError:
        print("Warning: scikit-learn not installed. Install it for dummy provider: pip install scikit-learn")
        # Ultra-simple fallback
        class UltraSimpleEmbeddings(EmbeddingsProvider):
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                # Return random embeddings of fixed size
                import random
                return [[random.random() for _ in range(384)] for _ in texts]
        
        class UltraSimpleLLM(LLMProvider):
            def generate(self, prompt: str) -> str:
                return "I'm running in ultra-simple mode. Please set up Google API key for proper responses."
        
        EMB_PROVIDER = UltraSimpleEmbeddings()
        LLM_PROVIDER = UltraSimpleLLM()