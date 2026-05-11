from __future__ import annotations

import re
import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.chunk import CodeChunk


MODEL_NAME = "all-MiniLM-L6-v2"
FALLBACK_DIMENSION = 384


_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,64}")


class EmbeddingModel:
    def __init__(self):
        self.embedding_dimension = FALLBACK_DIMENSION
        self._backend = "hashed"
        self.model: SentenceTransformer | None = None

        print(f"Loading embedding model: {MODEL_NAME}")

        try:
            # Prefer a real sentence-transformers model when available.
            # In restricted/offline environments (CI/sandboxes), this can fail
            # due to blocked downloads; we fall back to deterministic hashing.
            self.model = SentenceTransformer(MODEL_NAME)
            self.embedding_dimension = (
                int(getattr(self.model, "get_sentence_embedding_dimension")())
                if hasattr(self.model, "get_sentence_embedding_dimension")
                else FALLBACK_DIMENSION
            )
            self._backend = "sentence_transformers"
            print("Embedding model loaded")
        except Exception as error:
            self.model = None
            self.embedding_dimension = FALLBACK_DIMENSION
            self._backend = "hashed"
            print(
                "Embedding model unavailable; using hashed embeddings. "
                f"Reason: {error}"
            )

    def _hashed_embedding(
        self,
        text: str,
        *,
        dimension: int = FALLBACK_DIMENSION,
    ) -> list[float]:
        """
        Deterministic, dependency-free embedding for offline environments.

        This is not meant to match the quality of a transformer embedding;
        it exists to keep ingestion/search functional without network access.
        """
        tokens = _TOKEN_RE.findall(text.lower())
        vec = np.zeros(dimension, dtype=np.float32)

        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "little") % dimension
            sign = 1.0 if (digest[2] % 2 == 0) else -1.0
            vec[idx] += sign

        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm

        return vec.astype(np.float32).tolist()

    def embed_text(self, text: str) -> list[float]:
        if self.model is None:
            return self._hashed_embedding(text)

        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_chunks(
        self,
        chunks: list[CodeChunk],
    ) -> list[list[float]]:
        texts = [chunk.content for chunk in chunks]

        if self.model is None:
            return [
                self._hashed_embedding(text)
                for text in texts
            ]

        embeddings = self.model.encode(texts)
        return embeddings.tolist()