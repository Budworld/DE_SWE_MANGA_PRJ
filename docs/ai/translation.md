# AI Translation Draft

## Pipeline

1. Extract text từ metadata hoặc OCR từ ảnh nếu cần.
2. Normalize text, tách hội thoại và ngữ cảnh.
3. Translate theo target language.
4. Apply glossary cho tên nhân vật, địa danh, thuật ngữ.
5. Quality check và human review trước khi publish.

## Notes

- Lưu cả source text và translated text để audit.
- Version prompt/model để có thể tái tạo kết quả.
- Với manga scan ảnh, OCR và bubble detection có thể là module riêng.
