# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Lưu Thành Mỹ
- Members: Vũ Trí Dũng
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL:

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì                            | Tool mới nhóm thêm? |
| -------- | -------------------------------------- | ------------------- |
| clarify  | hỏi lại người dùng khi thiếu thông tin | không               |
|          |                                        |                     |
|          |                                        |                     |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
| ------- | ---------------- | ---------- | ------------: | -----------: | -------- |
| v0      | baseline         | Đo hành vi chưa tối ưu trước khi sửa | - | 0.65 | `runs/v0_B_base_openrouter_20261110T101900316716.json` |
| v1      |                  |            |               |              |          |
| v2      |                  |            |               |              |          |
| v3      |                  |            |               |              |          |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
| ------- | ------------ | ----------------- | ----------- | --- |
| `R03_web_news_routing` | `wrong_tool` / `wrong_arg_value` | `lookup(query="AI news", topic="news", timeframe="day")` | `query: expected 'AI', got 'AI news'` — khi `topic="news"` đã bật, không được nhét thêm từ `"news"` vào `query` | Quy định rõ trong `tools.yaml` (`lookup.query`): chỉ giữ từ khóa chủ đề thuần túy (ví dụ `"AI"`), không kèm từ `"news"` hay `"tin tức"` |
| `R08_out_of_scope` | `out_of_scope` (`unexpected_tool_call`) | `send(text="Nguyên hàm của x^2 là...")` | `expected no tool call` — câu hỏi toán học ngoài phạm vi research nhưng model lại gọi `send` để gửi câu trả lời | Bỏ chỉ dẫn ép gọi tool ở `system_prompt.md`, thêm quy tắc từ chối/không gọi tool khi câu hỏi ngoài phạm vi research (toán, code, dịch thuật...) |
| `R10_missing_handle` | `missing_info` (`missing_tool_call`) | `timeline(screenname="sama")` | `missing tool call clarify; extra tool call timeline` — thiếu tên tài khoản nhưng `system_prompt.md` bảo đoán bừa `"Sam Altman"` | Xóa chỉ dẫn đoán bừa trong `system_prompt.md`; bắt buộc gọi `clarify(response_type="text")` khi thiếu `screenname` |
| `R11_missing_url` | `missing_info` (`missing_tool_call`) | `fetch(url="https://example.com/article")` | `missing tool call clarify; extra tool call fetch` — nói `"bài viết này"` không kèm URL nhưng `system_prompt.md` xúi tự bịa URL | Xóa chỉ dẫn tự đoán URL trong `system_prompt.md`; bắt buộc gọi `clarify(response_type="text")` khi thiếu URL |
| `R12_confirm_before_send` | `wrong_boundary` (`missing_tool_call`) | `send(text="Bản tin này")` | `missing tool call clarify; extra tool call send` — tự ý gọi `send` ngay mà không hỏi xác nhận vì `system_prompt.md` bảo `"just go ahead and do it"` | Sửa `system_prompt.md` và `tools.yaml`: trước khi gọi `send`, phải gọi `clarify(response_type="yes_no")` để xin xác nhận của user |
| `R13_parallel_web_and_tweets` | `wrong_tool` (`missing_tool_call`) | `lookup(query="AI", topic="news", timeframe="day")`, `timeline(screenname="sama", limit=5)` | `missing tool call social_search; extra tool call timeline` — phần `"tìm thêm tweet về AI"` là tìm theo chủ đề nhưng model lại gọi `timeline("sama")` | Phân biệt rõ trong `system_prompt.md` & `tools.yaml`: tìm tweet theo chủ đề/từ khóa → `social_search`; chỉ dùng `timeline` khi biết cụ thể tài khoản |
| `R14_out_of_scope_coding` | `out_of_scope` (`unexpected_tool_call`) | `send(text="Dưới đây là một hàm Python...")` | `expected no tool call` — yêu cầu viết code Python ngoài phạm vi research nhưng model lại gọi `send` | Thêm quy tắc out-of-scope trong `system_prompt.md` và mô tả rõ `send` trong `tools.yaml` chỉ dùng để đăng bài lên Telegram sau khi user xác nhận |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
| ------- | ------------- | ---------------------- | ------ |
|         |               |                        |        |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
| ---- | ------------ | ---------- | ---------------- | ------- |
|      |              |            |                  |         |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus                      | Evidence File   | What Worked | Risk / Guardrail |
| -------------------------- | --------------- | ----------- | ---------------- |
| send (Telegram)            |                 |             |                  |
| arXiv/company policy       |                 |             |                  |
| UI                         |                 |             |                  |
| Tool unit tests (`tests/`) | `pytest` output |             |                  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version  | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
| -------- | ---------------- | ------------ | ------------- | ------------ | -------- | --------- | -------- |
| v3       | (cloud)          | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v4-local |                  |              |               |              |          |           |          |
| v5-local |                  |              |               |              |          |           |          |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern                               | Count | Example Case | Fix Tried | Helped? |
| --------------------------------------------- | ----- | ------------ | --------- | ------- |
| wrong / hallucinated tool                     |       |              |           |         |
| invalid JSON args (`_invalid_json_arguments`) |       |              |           |         |
| no tool call / answered directly              |       |              |           |         |
| missed `clarify`                              |       |              |           |         |
| repeated / unnecessary calls                  |       |              |           |         |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
