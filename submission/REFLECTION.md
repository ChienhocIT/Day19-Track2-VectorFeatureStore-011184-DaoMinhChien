# Reflection — Lab 19

**Tên:** Đào Minh Chiến (011184)
**Cohort:** A20 Cohort 2026 - Track 2
**Path đã chạy:** lite (fastembed + Qdrant in-memory + Feast SQLite)

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Thực nghiệm đo trên golden set 50 queries ghi nhận:
- **Mixed (20 queries):** **Hybrid (RRF $k=60$) thắng áp đảo đạt 100.0% Precision@10** (vượt trội so với BM25 97.0% và Vector 98.5%) nhờ kết hợp tín hiệu từ khóa và mở rộng ngữ nghĩa.
- **Exact (15 queries):** **BM25 và Hybrid cùng đạt 96.7%** vì từ khóa kỹ thuật khớp nguyên văn trong văn bản gốc.
- **Paraphrase (15 queries):** BM25 đạt 33.3%, Hybrid 32.0%, Vector 24.0% (trên model `bge-small` CPU; vector sẽ phát huy vượt trội hơn khi nâng cấp lên model đa ngữ `bge-m3`).

**Khi không dùng Hybrid:**
1. **Dùng Pure BM25:** Khi tìm kiếm mã định danh chính xác (`user_id`, UUID, log trace), mã lỗi kỹ thuật (`ERR_404`), tên hàm/biến trong code, hoặc hệ thống có SLA độ trễ siêu khắt khe (< 5ms) không có budget tài nguyên cho embedding.
2. **Dùng Pure Vector:** Khi tìm kiếm đa phương thức (image-to-text), đa ngôn ngữ không chung từ vựng (cross-lingual), hoặc truy vấn trừu tượng về cảm xúc/ý niệm không có từ khóa cố định.

---

## Điều ngạc nhiên nhất khi làm lab này

1. **Cái bẫy recall của Post-filtering (NB5):** Khi bộ lọc có độ chọn lọc cao (~4%), post-filter khiến recall sập thẳng về 0.00 mà hệ thống không hề báo lỗi (silent failure), trong khi Filtered-ANN vẫn duy trì recall 1.00 ổn định.
2. **Hiện tượng Target Leakage (NB8):** Việc target encoding toàn bộ tập dữ liệu tạo ra chỉ số AUC ảo 0.99 offline nhưng sụp đổ hoàn toàn khi gặp dữ liệu thực tế, khẳng định tầm quan trọng của in-fold encoding và Point-in-Time join trong Feast.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/ARCHITECTURE.md`, `bonus/agent.py`, `bonus/demo.py`)
- [ ] Pair work với: _N/A_


