# Day 06 · Data Ingestion Engineering

**Lab cá nhân** · **4 giờ** · **Dữ liệu tự chọn**

Biến tài liệu thành kho tri thức có thể truy xuất cho AI agent, rồi đo xem cách chuẩn bị dữ liệu nào hiệu quả nhất.

| 📄 Dữ liệu | 🧩 Chiến lược | 🎯 Benchmark |
|---|---|---|
| Tối thiểu **30 trang nội dung** | Tối thiểu **3 cấu hình** | Tối thiểu **20 câu hỏi** |

## Bắt đầu nhanh

Dùng [starter PostgreSQL + pgvector](starter/README.md) để dựng database và hoàn thiện các hàm TODO, hoặc tự chọn vector store tương đương. Starter chỉ là khung: **bạn tự hiện thực pipeline và benchmark**.

## 1. Xây pipeline

![Đọc tài liệu, chuẩn hóa, chia chunk, tạo vector, lưu và kiểm tra](assets/ingestion-pipeline.svg)

Chọn tài liệu được phép sử dụng; giữ **ID tài liệu, nguồn, trang/vị trí** và metadata phù hợp. Dùng embedding model thật qua API hoặc chạy local; lưu và truy xuất bằng pgvector, Qdrant, Chroma hoặc một store tương đương.

## 2. So sánh và đánh giá

![Ba chiến lược được đánh giá trên cùng corpus và benchmark dev/test](assets/benchmark-workflow.svg)

Dùng cùng dữ liệu, model và câu hỏi cho cả ba cấu hình. Tách **15 câu dev / 5 câu test** trước khi chạy; chọn cấu hình trên dev, rồi đánh giá test sau khi cố định. Mỗi câu hỏi cần có đoạn bằng chứng và trang nguồn; thiết kế bộ câu hỏi và đánh giá theo [BENCHMARK.md](BENCHMARK.md).

Đánh giá theo năm khía cạnh: **độ chính xác truy xuất**, **tính mạch lạc của chunk**, **tính hữu dụng của metadata**, **chất lượng grounding** và **tác động của chiến lược dữ liệu**. Giải thích lựa chọn bằng kết quả, ví dụ lỗi và các đánh đổi.

## 3. Chuẩn bị bài nộp

1. Chạy pipeline và lưu cấu hình, kết quả top-3, trace cùng nhãn đánh giá thủ công.
2. Điền [thông tin học viên](STUDENT.md), [nhật ký thí nghiệm](artifacts/experiment_log.csv) và bản sao [mẫu báo cáo cá nhân](report/individual/MSSV_HoTen.md).
3. Kiểm tra mã nguồn, cách chạy, manifest dữ liệu và checklist trong [SUBMISSION.md](SUBMISSION.md).

## Tài liệu hướng dẫn

| Bạn cần tìm | Tài liệu |
|---|---|
| Setup baseline PostgreSQL + pgvector | [starter/README.md](starter/README.md) |
| Các bước làm và cách tính chỉ số | [GUIDE.md](GUIDE.md) |
| Tiến độ trong 4 giờ | [CHECKPOINTS.md](CHECKPOINTS.md) |
| Năm tiêu chí benchmark và bộ câu hỏi | [BENCHMARK.md](BENCHMARK.md) |
| Tiêu chí chấm điểm | [RUBRIC.md](RUBRIC.md) |
| Quy tắc sử dụng dữ liệu, AI và API | [RULES.md](RULES.md) |
| Cách nộp bài | [SUBMISSION.md](SUBMISSION.md) |

[data/format-example.json](data/format-example.json) chỉ minh họa định dạng, không phải corpus đủ điều kiện. Phần xử lý và benchmark do bạn tự hiện thực; không bắt buộc xây chatbot.

---

## Bài làm cá nhân: cài đặt, chạy và đường dẫn

Chi tiết lệnh chạy trên máy không có Docker: [starter/RUN_LOCAL.md](starter/RUN_LOCAL.md).

**Cài đặt** (từ thư mục `starter/`): `python -m pip install -r requirements.txt`, sau đó cài torch CPU và các phiên bản trong RUN_LOCAL.md. Không cần API key; embedding chạy local.

**Chạy theo thứ tự** (từ `starter/`):
1. `python -m src.build_chunks`: làm sạch văn bản, chunk A và B.
2. `python -m src.index_chunks`: embed và nạp vào Chroma local.
3. `python -m src.retrieve`: truy xuất top-3 cho 21 câu hỏi, tính Hit@1 và Evidence Hit@3.
4. `python -m src.prepare_manual_sheets`: tạo sheet chấm thủ công (đã ẩn tên cấu hình).

Hoặc chạy bước 1–3 bằng một lệnh: `python -m src.run`. Thêm `--with-manual` để tạo lại sheet chấm (lệnh này đổi mã ẩn, chỉ dùng khi chấm lại).

Kiểm tra benchmark (từ thư mục gốc): `python -I benchmark/validate_benchmark.py`.

**Đường dẫn dữ liệu và kết quả:**
- Văn bản luật: `data/raw/luat_19_2023_qh15.txt`; bản đã làm sạch: `data/processed/luat_19_2023_qh15.normalized.txt`.
- Manifest (nguồn, giấy phép, danh sách 80 điều): `data/manifest.json`.
- Benchmark (21 câu, 15 dev / 6 test) và giải thích: `benchmark/questions.jsonl`, `benchmark/README.md`.
- Nhật ký thí nghiệm: `artifacts/experiment_log.csv`.
- Kết quả, trace, chỉ số, sheet chấm: `results/` (chi tiết trong `results/` và RUN_LOCAL.md). Dữ liệu vector `results/chroma/` không nộp, tái tạo bằng bước 2.
- Báo cáo cá nhân: `report/individual/` (tên file theo `<MSSV>_<HoTen>.md`).
- Thông tin học viên: `STUDENT.md`.
