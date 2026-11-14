# Báo cáo cá nhân — Day 6

**Họ và tên:** Đặng Nhật Huy  **MSSV:** 2A202603822  **Lớp:** L3B

Cách kiểm tra: script `benchmark/validate_benchmark.py`, `starter/src/build_chunks.py` và các file trace trong `results/`.

## Dữ liệu và pipeline

- **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:** Luật Bảo vệ quyền lợi người tiêu dùng số 19/2023/QH15 (hiệu lực 01/07/2024). Nguồn: trang LuatVietnam, lấy ngày 14/11/2026 ([data/manifest.json](../../data/manifest.json)). Văn bản quy phạm pháp luật không thuộc đối tượng bảo hộ bản quyền theo Luật Sở hữu trí tuệ. Văn bản không có số trang, nên đơn vị truy vết là **điều**: 80 điều, mỗi điều kèm chương chứa nó. Phụ lục đính kèm không đưa vào corpus.
- **Chuẩn hóa, lỗi và giới hạn:** Loại 162 dòng chú thích của trang web (ví dụ "Khoản 9 Điều 3 được hướng dẫn bởi…", "Điều 44 Nghị định 146/2025/NĐ-CP", mã liên kết HTML); giữ phần chữ của 7 đoạn sửa đổi kiểu `"> …` (xem `starter/src/ingestion.py`). Lỗi còn lại: Điều 15 khoản 1 vẫn giữ cụm từ đã được thay thế bởi Luật 116/2025/QH15; Điều 54 khoản 1 ghi "h) Hòa giải" (thứ tự đúng là b); tiêu đề Mục nằm trong nội dung điều đứng trước. **Chưa đối chiếu với Công báo chính thức.**
- **Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:** `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, chạy local (sentence-transformers 6.3.0, torch CPU), 384 chiều, vector chuẩn hóa; tiền tố `passage: ` cho chunk và `query: ` cho câu hỏi. Vector store: Chroma 1.5.9 local, collection cho từng chiến lược, metric cosine. Không dùng Docker/PostgreSQL vì máy không có Docker. Lệnh chạy: xem [starter/RUN_LOCAL.md](../../starter/RUN_LOCAL.md). Chi phí API: 0. Thời gian nạp chunk chưa đo riêng.
- **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:** `document_id`, `source`, `article_from`, `article_to` (vị trí truy vết), `chapter`, `split_level`, `khoan`. Trường lọc: `chapter` (7 giá trị La Mã I–VII), lấy từ dòng tiêu đề "Chương X" của văn bản, không tự suy ra. Chọn chương vì phân biệt rõ phạm vi (quy định chung, trách nhiệm, giải quyết tranh chấp, quản lý nhà nước…).

## Cấu hình và benchmark

- **A / B / C:**
  - **A:** chunk cố định 500 ký tự, overlap 50, trên toàn văn bản (không theo ranh giới điều). Metadata gắn theo vị trí; 237 chunk, 81 chunk trải trên nhiều điều, 7 chunk trải trên nhiều chương.
  - **B:** chunk theo cấu trúc. Điều là đơn vị; điều dài hơn 1.500 ký tự tách theo khoản (gom khoản liền nhau không vượt 1.500); khoản quá dài tách theo câu; điều ngắn hơn 400 ký tự cùng chương được gộp, không vượt 1.500. 119 chunk (48 điều nguyên, 51 theo khoản, 17 theo câu, 3 gộp).
  - **C:** cùng chunk với B; khác B ở chỗ áp dụng filter `chapter` khi câu hỏi có ngữ cảnh chương. Câu không có filter chạy không lọc.
  - Khác biệt A–B là chunking (một yếu tố thay đổi, nhưng kích thước và cơ chế cắt khác nhau cùng lúc). Khác biệt B–C chỉ là filter.
- **≥20 câu: phân chia dev/test, câu metadata filter và cách kiểm chứng evidence:** 21 câu: **15 dev, 6 test** (yêu cầu tối thiểu 15/5; test lấy 6 thay vì 5). Loại câu: trực tiếp, diễn đạt lại, điều kiện/ngoại lệ, có ngữ cảnh chương. **4 câu có filter**: D13, D14 (dev), T03, T04 (test). Mỗi câu có điều gold, đáp án, và trích dẫn evidence. Script `benchmark/validate_benchmark.py` kiểm tra trích dẫn nằm nguyên văn trong điều gold, filter khớp chương, và câu hỏi không nêu số điều. Tập câu hỏi khóa bằng SHA-256 `5bdf126f…010e4b` trước khi chạy retrieval ([benchmark/README.md](../../benchmark/README.md)).
- **Tiêu chí chọn chiến lược đã chốt trước khi xem test:** (1) Evidence Hit@3 dev cao nhất; (2) Hit@1 dev; (3) coherence trung bình chấm thủ công; (4) chi phí và thời gian, chỉ dùng khi các tiêu chí trên hòa. Ghi trong [benchmark/README.md](../../benchmark/README.md) trước khi chạy retrieval.
  - *Lưu ý trung thực:* kết quả test được tính trong cùng lần chạy với dev, và tác giả có xem đầu ra của cả hai. Không có bước tinh chỉnh nào dựa vào test; quyết định chọn cấu hình chỉ dùng tiêu chí đã ghi.

## Kết quả

Hit là định nghĩa theo GUIDE: chunk chứa điều gold và chứa nguyên văn trích dẫn evidence. Hit@1: top-1 là hit. Evidence Hit@3: ít nhất một hit trong top-3. Số liệu từ [results/retrieval_summary.json](../../results/retrieval_summary.json).

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian (trung bình/câu hỏi) | Chi phí |
|---|---|---|---|---|---|---|
| A | dev | 7/15 | 7/15 | 237 | 11,1 ms (cả hai split) | 0 |
| A | test | 5/6 | 6/6 | 237 | (như trên) | 0 |
| B | dev | 9/15 | 11/15 | 119 | 7,8 ms (cả hai split) | 0 |
| B | test | 4/6 | 4/6 | 119 | (như trên) | 0 |
| C | dev | 9/15 | 11/15 | 119 (dùng chunk B) | 3,6 ms (cả hai split) | 0 |
| C | test | 4/6 | 5/6 | 119 (dùng chunk B) | (như trên) | 0 |

Thời gian là độ trễ truy vấn trên một lần chạy, nên có nhiễu lớn; không phải benchmark hiệu năng.

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| A | 1,10 (10) | 18/18 (kiểm tra bằng script) | N/A | 0/0/6, trung bình 2,00 |
| B | 2,00 (10) | 18/18 (kiểm tra bằng script) | N/A | 2/0/4, trung bình 1,33 |
| C | dùng chunk B: 2,00 | 18/18 (kiểm tra bằng script) | 6/6 | 1/0/5, trung bình 1,67 |

- **Nhãn coherence và grounding:** Thực hiện chấm thủ công và có gợi ý bởi AI. 
- **Metadata:** kiểm tra tự động xác nhận mọi chunk là chuỗi con của đúng các điều trong khoảng metadata và chương khớp. Cột kiểm tra thủ công (nguồn, điều, chương) chưa được tác giả đọc từng bản ghi.
- **Đường dẫn trace:** `results/traces_A.jsonl`, `traces_B.jsonl`, `traces_C.jsonl`. Sheet chấm: `results/manual/`. Ánh xạ mã ẩn: `KEY_do_not_open_until_labelled.json`.

## Phân tích và kết luận

- **So sánh A–B:** B vượt A ở Evidence Hit@3 dev (11/15 so với 7/15) và ở coherence (2,00 so với 1,10). Chunk cố định cắt ngang khoản và câu, làm trích dẫn bị tách. Hai ví dụ sai:
  - **D01** (định nghĩa người tiêu dùng, Điều 3): A trả về chunk có Điều 3 nhưng trích dẫn bị cắt qua ranh giới cửa sổ; B có chunk B-0002 chứa đúng trích dẫn nhưng không đưa vào top-3 (chunk này gộp khoản 1–3 nên lẫn với nội dung khác, và truy vấn gần với Điều 6, 8, 1).
  - **T04** (án phí của tổ chức xã hội, Điều 71 khoản 3): B không đưa Điều 71 vào top-3 (top-3 là Điều 50, 73, 72); C đưa Điều 71 lên hạng 3 nhờ filter chương V.
  - **B–C:** chỉ khác ở filter. Dev không đổi (11/15). Test cải thiện ở T04 (4/6 → 5/6). Filter hữu ích khi câu hỏi có ngữ cảnh chương rõ, nhưng với T03 (nghĩa vụ chứng minh, Điều 69) cả B và C đều trượt.
- **Chiến lược được chọn:** C. Theo quy tắc đã chốt, B và C hòa ở Hit@1 dev (9/15), Evidence Hit@3 dev (11/15) và coherence (2,00, vì dùng chung chunk). Quyết định cuối cùng dựa vào thời gian truy vấn (3,6 ms so với 7,8 ms). Điều này rất yếu: chênh lệch vài mili giây trên một lần chạy, không nên coi là bằng chứng chất lượng. Điều kiện áp dụng: khi người dùng cung cấp được chương, C là lựa chọn an toàn hơn; khi không có ngữ cảnh chương, C và B tương đương.
- **Đánh đổi:** A đơn giản nhưng chất lượng chunk thấp. B cho chunk đúng ngữ nghĩa nhưng dài không đều (86–1.500 ký tự) và một số chunk khoản quá ngắn. C tăng độ chính xác khi có filter, nhưng phụ thuộc vào việc người dùng cung cấp đúng chương.
- **Hạn chế:**
  - Test chỉ 6 câu, dev 15 câu: mỗi câu thay đổi 1/6 hoặc 1/15 điểm. Không thể kết luận chiến lược tốt nhất tổng quát.
  - Nguồn chưa đối chiếu với Công báo; văn bản có lỗi chép và phần sửa đổi trộn lẫn.
  - Thiên lệch tác giả: tác giả soạn cả câu hỏi lẫn đáp án.
  - Chỉ một lần chạy, chưa đo nhiễu của thời gian.
  - Hit định nghĩa nghiêm ngặt: phải chứa đúng nguyên văn trích dẫn, nên một chunk đúng ý nhưng khác chữ bị tính là trượt.
- **Nếu làm lại hoặc mở rộng:**
  1. Đối chiếu corpus với Công báo và sửa các lỗi còn lại (Điều 15, Điều 54).
  2. Tăng số câu test (ít nhất 20) và có người chấm độc lập cho coherence và grounding.
  3. Đo thời gian nạp và truy vấn nhiều lần, báo cáo trung vị.
  4. Thử hybrid retrieval (BM25 + dense) như phần mở rộng trong GUIDE, với tiêu chí chọn trên dev.
