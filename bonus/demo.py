"""Demo script executing 5 representative queries on HybridMemoryAgent."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from bonus.agent import HybridMemoryAgent

def main() -> int:
    print("=================================================================")
    print("  Day 19 Bonus Challenge — Hybrid Memory Agent POC Demo")
    print("=================================================================\n")

    feast_dir = ROOT / "app" / "feast_repo"
    agent = HybridMemoryAgent(repo_path=feast_dir)

    # Seed initial memories for user u_001
    memories_u1 = [
        "Đã đọc bài viết giới thiệu kiến trúc Kubernetes Cluster và quản lý container pod.",
        "Ghi chú dự án: Cần triển khai autoscaling HPA và cân bằng tải Ingress trên AWS EKS.",
        "Tìm hiểu về mô hình bảo mật Zero Trust và xác thực hai yếu tố 2FA trong Cloud Computing.",
        "Đang nghiên cứu tối ưu chi phí hạ tầng cloud bằng spot instances và reserved nodes.",
    ]
    for text in memories_u1:
        agent.remember(text, user_id="u_001")

    # Seed a memory for user u_002 to prove tenant privacy isolation
    agent.remember("Dữ liệu tài chính bí mật của công ty ACME quý 3 là 4.2 tỷ VND", user_id="u_002")

    queries = [
        ("1. Hỏi đơn giản (Episodic Recall)", "Tôi đã đọc gì về Kubernetes?"),
        ("2. Hỏi cần Profile Context", "Recommend đọc gì tiếp theo?"),
        ("3. Hỏi cần Fresh Activity Context", "Tôi đang quan tâm gì gần đây?"),
        ("4. Hỏi dạng Paraphrase (Vector Semantic Match)", "Tài liệu về tự động mở rộng hạ tầng?"),
        ("5. Hỏi dạng Mixed (Episodic + Profile Summary)", "Cho tôi summary cloud security."),
    ]

    for idx, (title, q) in enumerate(queries, 1):
        print(f"[{title}]")
        print(f"User Question: \"{q}\"")
        context = agent.recall(q, user_id="u_001")
        print("Generated Grounding Context:")
        print(context)
        print("-" * 65 + "\n")

    print("Privacy Sanity Check: Thử truy vấn dữ liệu nhạy cảm của u_002 từ tài khoản u_001:")
    leak_check = agent.recall("Dữ liệu tài chính bí mật của công ty ACME", user_id="u_001")
    print(leak_check)
    print("\n✓ DEMO COMPLETED SUCCESSFULLY WITH EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
