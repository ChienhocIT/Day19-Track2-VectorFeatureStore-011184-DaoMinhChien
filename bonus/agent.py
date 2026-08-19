"""Hybrid Memory Agent combining Episodic Vector Store and Feast Feature Store."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.embeddings import Embedder

COLLECTION_NAME = "agent_memories"


class HybridMemoryAgent:
    """Personal AI Memory Agent combining Episodic Vector Memory and Feast Feature Store."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self.embedder = Embedder()
        self.client = QdrantClient(":memory:")
        self._point_id = 0

        # Initialize Qdrant collection for episodic memories
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=self.embedder.dim, distance=Distance.COSINE),
        )

        # Initialize Feast Feature Store if available
        self.fs = None
        if repo_path is not None and Path(repo_path).exists():
            try:
                from feast import FeatureStore

                self.fs = FeatureStore(repo_path=str(repo_path))
            except Exception:
                self.fs = None

    def remember(self, text: str, user_id: str = "u_001", metadata: dict[str, Any] | None = None) -> None:
        """Add a new piece of episodic memory for a specific user."""
        vec = next(self.embedder.embed([text])).tolist()
        payload = {
            "user_id": user_id,
            "text": text,
            "timestamp": time.time(),
            **(metadata or {}),
        }
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=self._point_id, vector=vec, payload=payload)],
        )
        self._point_id += 1

    def recall(self, query: str, user_id: str = "u_001", top_k: int = 3) -> str:
        """Retrieve top-K memories + user profile features and return assembled context string."""
        # 1. Fetch user profile + recent activity from Feast Feature Store
        profile_info = {
            "reading_speed_wpm": 200,
            "preferred_language": "vi",
            "topic_affinity": "cloud",
            "queries_last_hour": 5,
        }

        if self.fs is not None:
            try:
                features = self.fs.get_online_features(
                    features=[
                        "user_profile_features:reading_speed_wpm",
                        "user_profile_features:preferred_language",
                        "user_profile_features:topic_affinity",
                        "query_velocity_features:queries_last_hour",
                    ],
                    entity_rows=[{"user_id": user_id}],
                ).to_dict()
                if features.get("user_id"):
                    profile_info["reading_speed_wpm"] = features.get("reading_speed_wpm", [200])[0] or 200
                    profile_info["preferred_language"] = features.get("preferred_language", ["vi"])[0] or "vi"
                    profile_info["topic_affinity"] = features.get("topic_affinity", ["cloud"])[0] or "cloud"
                    profile_info["queries_last_hour"] = features.get("queries_last_hour", [5])[0] or 5
            except Exception:
                pass

        # 2. Hybrid / Vector Search filtered strictly by user_id in Qdrant (prevent multi-tenant leak)
        q_vec = next(self.embedder.embed([query])).tolist()
        user_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])

        search_res = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            query_filter=user_filter,
            limit=top_k,
        ).points

        memories = [f"- {p.payload['text']} (score: {p.score:.3f})" for p in search_res]

        # 3. Assemble personalized context string for LLM grounding
        context_lines = [
            f"=== USER CONTEXT ({user_id}) ===",
            f"• Profile: Ngôn ngữ '{profile_info['preferred_language']}', Tốc độ đọc {profile_info['reading_speed_wpm']} wpm, Lĩnh vực quan tâm '{profile_info['topic_affinity']}'.",
            f"• Trạng thái hoạt động: {profile_info['queries_last_hour']} truy vấn trong 1 giờ qua.",
            "",
            f"=== EPISODIC MEMORIES (Top {len(memories)} kết quả cho câu hỏi: '{query}') ===",
        ]
        if memories:
            context_lines.extend(memories)
        else:
            context_lines.append("(Không tìm thấy ký ức liên quan phù hợp với người dùng này)")

        return "\n".join(context_lines)
