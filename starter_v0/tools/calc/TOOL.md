---
name: calc
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [expression]
outputs: [result]
side_effect: false
requires_confirmation: false
---

# calc

Máy tính số học cục bộ, không gọi mạng. Nhận một biểu thức như `12*(3+4)`
và trả về `result`.

**Khi nào dùng:** người dùng yêu cầu một phép tính số học rõ ràng
(cộng/trừ/nhân/chia/luỹ thừa/chia lấy dư) trên các con số cụ thể.

**Khi nào KHÔNG dùng:** giải tích/đại số ký hiệu (nguyên hàm, đạo hàm, giải
phương trình chữ), câu hỏi nghiên cứu/tin tức, hay bất cứ thứ gì cần dữ liệu
ngoài — những việc đó dùng tool khác hoặc từ chối.

An toàn: không dùng `eval()`; chỉ duyệt AST các toán tử số học được phép nên
không thể thực thi mã tuỳ ý. Lỗi (biểu thức rỗng/sai, chia cho 0) trả về
dict lỗi, không raise.
