# Chạy pipeline trên máy không có Docker

Đây là cách đã dùng để tạo kết quả trong báo cáo (Windows, Python 3.14, CPU). Không cần PostgreSQL: vector store là Chroma chạy local.

## 1. Cài đặt

Chạy từ thư mục `starter/`:

```powershell
python -m pip install -r requirements.txt
python -m pip install chromadb==1.5.9 sentence-transformers==6.3.0
# torch CPU (cài trước nếu muốn tránh bản CUDA lớn):
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Model embedding `intfloat/multilingual-e5-small` (revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`) được tự tải từ Hugging Face lần chạy đầu, khoảng 470 MB. Không cần API key.

## 2. Chuẩn bị dữ liệu

Corpus và văn bản đã làm sạch nằm sẵn trong repo:

- `../data/raw/luat_19_2023_qh15.txt`: văn bản luật (nguồn LuatVietnam, chưa đối chiếu với Công báo).
- `../data/manifest.json`: nguồn, giấy phép, danh sách 80 điều.
- `../benchmark/questions.jsonl`: 21 câu hỏi (15 dev, 6 test), SHA-256 khóa trong `../benchmark/README.md`.

## 3. Thứ tự chạy

```powershell
python -m src.build_chunks        # làm sạch, chunk A và B -> results/chunks_*.jsonl, chunk_stats.json
python -m src.index_chunks        # embed và nạp Chroma (chạy 2 lần để kiểm tra không trùng)
python -m src.retrieve            # top-3 cho A, B, C -> results/traces_*.jsonl, retrieval_summary.json
python -m src.prepare_manual_sheets   # sheet chấm thủ công (đã ẩn tên cấu hình) -> results/manual/
```

Kiểm tra benchmark (từ thư mục gốc repo):

```powershell
python -I ..\benchmark\validate_benchmark.py
```

## 4. Kết quả đầu ra

- `../results/chunk_stats.json`: số chunk, độ dài, số lần làm sạch chú thích.
- `../results/index_summary.json`: kết quả nạp hai lần, chứng minh không trùng.
- `../results/retrieval_summary.json`: Hit@1 và Evidence Hit@3 theo dev/test.
- `../results/manual/`: sheet chấm thủ công, và `manual_summary.json` tổng hợp nhãn. Nhãn trong `labels_ai_assisted.json` do AI chấm, cần người chấm kiểm tra lại.
- `../results/manual/KEY_do_not_open_until_labelled.json`: ánh xạ mã ẩn sang cấu hình. Mở sau khi chấm xong.

## 5. Lưu ý

- Không commit `.env`, API key, hay thư mục `../results/chroma/` (dữ liệu vector, có thể rất lớn).
- Chạy lại `index_chunks` sau khi đổi chunk sẽ xóa chunk cũ không còn trong nguồn (xem `store.py`).
- Mọi số liệu trong báo cáo lấy từ các file trên; nếu chạy lại mà số khác thì phải cập nhật báo cáo.
