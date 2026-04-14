from __future__ import annotations

from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorMemory:
	def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
		self.model = SentenceTransformer(model_name)
		self.dimension = self.model.get_sentence_embedding_dimension()
		# Cosine similarity with normalized vectors via inner product.
		self.index = faiss.IndexFlatIP(self.dimension)
		self.messages: list[str] = []

	def _encode(self, text):
		vec = self.model.encode([text], convert_to_numpy=True).astype("float32")
		faiss.normalize_L2(vec)
		return vec

	def upsert(self, text: str) -> None:
		if not text or not text.strip():
			return
		vector = self._encode(text.strip())
		self.index.add(vector)
		self.messages.append(text.strip())

	def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
		if self.index.ntotal == 0:
			return []
		if not query or not query.strip():
			return []

		k = max(1, min(int(top_k), self.index.ntotal))
		q_vec = self._encode(query.strip())
		scores, indices = self.index.search(q_vec, k)

		results: list[dict[str, Any]] = []
		for score, idx in zip(scores[0], indices[0]):
			if idx < 0:
				continue
			results.append(
				{
					"message": self.messages[idx],
					"score": float(score),
				}
			)
		return results
