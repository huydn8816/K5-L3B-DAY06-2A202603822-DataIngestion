# Benchmark — Luật 19/2023/QH15 (Bảo vệ quyền lợi người tiêu dùng)

Bước 2 của lab. Bộ câu hỏi được soạn và kiểm chứng **trước** khi chạy bất kỳ retrieval nào.

## Tệp

| File | Nội dung |
|---|---|
| `questions.jsonl` | 21 câu: 15 dev, 6 test. Mỗi dòng có `id`, `split`, `type`, `question`, `expected_answer`, `gold_article`, `evidence_quote`, `filter`. |
| `validate_benchmark.py` | Kiểm tra: điều gold tồn tại; `evidence_quote` nằm nguyên văn trong điều đó; filter khớp chương của điều gold; câu hỏi không nêu số điều; đủ số lượng tối thiểu. |

Chạy kiểm tra (từ thư mục gốc repo):

```bash
python -I benchmark/validate_benchmark.py
```

Kết quả lần chạy: `questions=21 dev=15 test=6 filtered=4 filtered_test=2`, toàn bộ kiểm tra đạt.

## Phân bố

- Loại câu: `direct` (trực tiếp), `paraphrase` (diễn đạt lại), `conditional` (điều kiện/ngoại lệ), `filter` (có ngữ cảnh lọc theo chương).
- Câu có filter: D13, D14 (dev); T03, T04 (test). Filter `{"chapter": "V"}` do câu hỏi cung cấp như ngữ cảnh người dùng, trước khi truy xuất. Câu hỏi không chứa số điều hay đáp án.
- Đơn vị gold là **điều** (article). Số điều gold được phân bố trên nhiều chương, không tập trung một điều.

## Khóa tập dev/test

- Ngày khóa: 2026-11-14, trước khi chạy retrieval lần nào.
- SHA-256 của `questions.jsonl` tại thời điểm khóa: `5bdf126fa62bc9ebdbb75ff56c96ad982f17dfcc7c519f050f6730da77010e4b`.
- Không được sửa test sau khi đã xem kết quả. Nếu buộc phải sửa, ghi rõ trong báo cáo và không coi đó là kiểm tra độc lập.

## Tiêu chí chọn cấu hình (chốt trước khi xem test)

1. Chọn cấu hình có **Evidence Hit@3 dev** cao nhất (A, B hoặc C).
2. Nếu hòa, chọn cấu hình có **Hit@1 dev** cao hơn.
3. Nếu vẫn hòa, chọn cấu hình có **coherence trung bình** cao hơn trên mẫu 10 vị trí (chấm thủ công).
4. Chi phí và thời gian chỉ dùng để phân xử khi các tiêu chí trên đều hòa.

Test chỉ dùng để báo cáo kết quả sau khi cấu hình đã được chọn bằng dev.

## Lưu ý về dữ liệu nguồn (phát hiện khi soạn benchmark)

File `data/raw/luat_19_2023_qh15.txt` lấy từ trang LuatVietnam, chưa đối chiếu với Công báo. Các vấn đề thấy được:

- Còn sót chú thích của trang web: các dòng như `Điều 32 được hướng dẫn bởi ...`, `Điều 47 được hướng dẫn bởi ...`, và đoạn `" data-href="...`. Những dòng này **không** phải nội dung luật. Bước `normalize_text` (bước 3) cần loại bỏ, và phải ghi lại số đoạn đã loại.
- Điều 15 khoản 1 có chú thích "Cụm từ ... bị thay thế bởi Điểm a Khoản 2 Điều 43 Luật số 116/2025/QH15". Đây là thông tin sửa đổi sau này, không phải nội dung gốc của điều.
- Điều 54 khoản 1 ghi "h) Hòa giải" trong khi thứ tự đúng là các điểm a, b, c, d. Đây có thể là lỗi chép từ nguồn. Không câu hỏi nào trích dẫn điểm này.
- Điều 56 khoản 3 có chú thích về Nghị định 146/2025/NĐ-CP, không thuộc nội dung luật.
- Phụ lục đính kèm không có trong file và không thuộc corpus.

Các lỗi trên là một phần của đánh giá chất lượng dữ liệu (bước 1/3), không che giấu trong báo cáo.
