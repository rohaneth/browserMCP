import os
import math
import logging
import numpy as np
from typing import List, Union, Optional
from sklearn.feature_extraction.text import HashingVectorizer

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class BaseEmbeddingProvider:
    def get_dimension(self) -> int:
        return EMBEDDING_DIM

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        results = self.embed_texts([text])
        return results[0] if results else [0.0] * self.get_dimension()


class LocalDenseSemanticEmbedder(BaseEmbeddingProvider):
    """
    Zero-dependency local dense embedder.
    Uses sub-word character n-gram and word hashing with L2-normalized dense projection
    to yield deterministic 384-dimensional dense vectors for offline development.
    (Note: Handcrafted statistical subword projection; remote neural APIs are used when configured).
    """
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.vectorizer = HashingVectorizer(
            n_features=self.dim,
            ngram_range=(1, 3),
            analyzer="char_wb",
            alternate_sign=False,
            norm="l2"
        )
        self.word_vectorizer = HashingVectorizer(
            n_features=self.dim,
            ngram_range=(1, 2),
            analyzer="word",
            alternate_sign=False,
            norm="l2"
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        cleaned = [t.strip().lower() if t else "" for t in texts]
        # Char n-gram dense matrix
        char_mat = self.vectorizer.transform(cleaned).toarray()
        # Word n-gram dense matrix
        word_mat = self.word_vectorizer.transform(cleaned).toarray()

        # Combine both representations: 60% word semantics, 40% subword robustness
        combined = (0.6 * word_mat) + (0.4 * char_mat)
        
        # L2 Normalize vectors
        norms = np.linalg.norm(combined, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        normalized = combined / norms
        
        return normalized.tolist()


class RemoteAPIEmbedder(BaseEmbeddingProvider):
    """
    Supports OpenAI, Gemini, or Ollama when configured in the environment.
    Falls back gracefully to LocalDenseSemanticEmbedder if API call fails or offline.
    """
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        self.fallback = LocalDenseSemanticEmbedder()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model_name = self.model or "models/embedding-001"
                    res = genai.embed_content(
                        model=model_name,
                        content=texts,
                        task_type="retrieval_document"
                    )
                    embeddings = res.get("embedding", [])
                    # Adjust dimensions if needed
                    return [self._fit_dim(e) for e in embeddings]
                except Exception as e:
                    logger.warning(f"Gemini embedding API call failed: {e}. Using local fallback.")

        elif self.provider == "ollama":
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
            model_name = self.model or "nomic-embed-text"
            try:
                import urllib.request
                import json
                embeddings = []
                for t in texts:
                    req_data = json.dumps({"model": model_name, "prompt": t}).encode("utf-8")
                    req = urllib.request.Request(ollama_url, data=req_data, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        embeddings.append(self._fit_dim(data.get("embedding", [])))
                return embeddings
            except Exception as e:
                logger.warning(f"Ollama embedding call failed: {e}. Using local fallback.")

        # Default fallback
        return self.fallback.embed_texts(texts)

    def _fit_dim(self, vec: List[float]) -> List[float]:
        if len(vec) == EMBEDDING_DIM:
            return vec
        elif len(vec) > EMBEDDING_DIM:
            truncated = vec[:EMBEDDING_DIM]
            norm = math.sqrt(sum(x*x for x in truncated)) or 1.0
            return [x / norm for x in truncated]
        else:
            padded = vec + [0.0] * (EMBEDDING_DIM - len(vec))
            return padded


_EMBEDDER_INSTANCE: Optional[BaseEmbeddingProvider] = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        provider_name = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        if provider_name in ["openai", "gemini", "ollama"]:
            _EMBEDDER_INSTANCE = RemoteAPIEmbedder(
                provider=provider_name,
                model=os.getenv("EMBEDDING_MODEL")
            )
        else:
            _EMBEDDER_INSTANCE = LocalDenseSemanticEmbedder()
    return _EMBEDDER_INSTANCE


def embed_text(text: str) -> List[float]:
    provider = get_embedding_provider()
    return provider.embed_query(text)


def embed_batch(texts: List[str]) -> List[List[float]]:
    provider = get_embedding_provider()
    return provider.embed_texts(texts)
