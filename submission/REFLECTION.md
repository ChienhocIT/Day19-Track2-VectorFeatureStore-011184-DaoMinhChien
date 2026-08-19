# Reflection — Lab 19

**Tên:** Đào Minh Chiến (011184)
**Cohort:** A20 Cohort 2026 - Track 2
**Path đã chạy:** lite (fastembed + Qdrant in-memory + Feast SQLite)

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

- **Exact queries:** BM25 thắng hoặc hòa Hybrid vì từ khóa kỹ thuật khớp chính xác nguyên văn trong corpus (sparse match vượt trội).
- **Paraphrase queries:** Vector search chiếm ưu thế khi câu hỏi diễn đạt lại bằng từ đồng nghĩa/ngữ cảnh mà không chứa từ khóa nguyên bản (đặc biệt khi nâng cấp lên model đa ngữ `bge-m3`).
- **Mixed queries:** **Hybrid (RRF $k=60$) thắng áp đảo** (~100% Precision@10) nhờ kết hợp tín hiệu từ khóa chính xác và ngữ nghĩa mở rộng.

**Khi không dùng Hybrid:**
1. *Dùng Pure BM25:* Khi tìm kiếm mã lỗi cụ thể (error code), ID định danh (`user_id`, UUID), tên biến chính xác trong code, hoặc hệ thống ràng buộc SLA độ trễ cực thấp (< 5ms) không có GPU/CPU budget cho embedding.
2. *Dùng Pure Vector:* Khi hệ thống tìm kiếm đa phương thức (image-to-text), đa ngôn ngữ không đồng nhất (cross-lingual query không có từ vựng chung), hoặc dữ liệu đầu vào chứa nhiều từ ngữ trừu tượng, cảm xúc.

---

## Điều ngạc nhiên nhất khi làm lab này

Cái bẫy recall của post-filtering (NB5) khi độ chọn lọc filter cao (~4%) khiến recall sập về 0.00 mà không hề báo lỗi, và việc target encoding sai thứ tự (NB8) tạo ra 0.99 AUC ảo offline nhưng sụp đổ hoàn toàn online.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/ARCHITECTURE.md`, `bonus/agent.py`, `bonus/demo.py`)
- [ ] Pair work với: _N/A_

