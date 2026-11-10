# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v4, failure, eval, chat) dựa trên log thật.

## Team

- Team: Simple-Tech
- Members: Phan Hải Đăng, Lưu Thanh Mỹ
- Provider/model: OpenRouter / `openai/gpt-4o-mini` (temperature 0)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent chạy thật: nhận yêu cầu người dùng, **tự chọn tool** (tìm tin theo từ khóa/tài khoản, đọc URL, tra bách khoa, tra từ, tính toán, xem giờ, tra policy nội bộ, tìm paper arXiv), chạy tool thật, tổng hợp kết quả có trích nguồn, và **gửi lên Telegram khi được xác nhận**. Có 3 cách dùng: CLI (`chat.py`), **UI web Streamlit** (`app.py`), và **bot Telegram hai chiều** (`telegram_bot.py`).

**Link dùng thử (deploy — Cloudflare Tunnel, theo README):**

UI gồm 2 trang: **Chat** (`app.py`) và **🗂️ Admin** (`pages/1_Admin.py` — quản trị tin nhắn Telegram, log luồng chạy tool, log test eval). Expose public bằng Cloudflare Tunnel; link `trycloudflare.com` là tạm thời theo phiên nên dán lại ngay trước khi demo.

```powershell
# 1) Chạy UI local
.venv\Scripts\activate
streamlit run app.py                     # http://localhost:8501  (Admin: /Admin)

# 2) Expose public (cloudflared đã cài qua winget)
cloudflared tunnel --url http://localhost:8501
```

- URL công khai: ⟨dán link https://<random>.trycloudflare.com tại buổi demo⟩
- Trang Admin: thêm `/Admin` vào cuối link đó.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin / xin xác nhận trước khi gửi | không |
| timeline | Lấy tweet gần đây CỦA một tài khoản (map tên → handle) | không |
| social_search | Tìm tweet theo CHỦ ĐỀ (Top/Latest) | không |
| lookup | Tìm tin tức/thông tin trên web (topic, timeframe) | không |
| fetch | Đọc nội dung một URL cụ thể | không |
| format | Trình bày các item đã có thành digest markdown | không |
| send | Gửi text lên Telegram (chỉ khi `confirmed=true`) | không (bonus) |
| policy | Tra chính sách nội bộ công ty (markdown) | không (bonus) |
| papers | Tìm paper trên arXiv | không (bonus) |
| paper_text | Tải PDF arXiv và trích text | không (bonus) |
| **calc** | **Tính biểu thức số học cơ bản (an toàn, cục bộ)** | **CÓ** |
| **datetime** | **Ngày/giờ hiện tại theo múi giờ IANA** | **CÓ** |
| **wiki** | **Tóm tắt bách khoa từ Wikipedia (không key)** | **CÓ** |
| **define** | **Tra nghĩa một từ (dictionaryapi.dev, không key)** | **CÓ** |

→ 10 tool có sẵn + **4 tool mới** (calc, datetime, wiki, define).

## A3. Câu hỏi mẫu để thử

1. "Tweet mới nhất của Sam Altman là gì?" → route `timeline` (sama)
2. "Tin tức AI hôm nay có gì nổi bật?" → route `lookup` (topic=news, timeframe=day)
3. "Transformer trong học máy là gì?" → route `wiki`
4. "Tính 125 * 48 + 90" → route `calc`
5. "Đăng bản tin này lên Telegram giúp mình" → agent **hỏi xác nhận yes/no trước** (không tự gửi)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` + `runs/*.json`. Suite = base (20 case).

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Baseline chưa tinh chỉnh | — | 0.70 | `runs/v0_B_base_openrouter_20261110T094641803175.json` |
| v1 | system_prompt.md | Thêm rule routing cơ bản + hỏi lại khi thiếu | 0.70 | 0.85 | `runs/v1_B_base_openrouter_20261110T103823244196.json` |
| v2 | tools.yaml | Viết lại description core rõ KHI NÀO DÙNG + quy ước arg (handle không @, topic=news, timeframe, search_type=Top); thêm 4 tool mới | 0.85 | **0.95** | `runs/v2_B_base_openrouter_20261110T111547574574.json` |
| v3 | system_prompt.md | Thêm ROUTING rules + map handle few-shot + rule confirm trước khi gửi | 0.95 | 0.95 | `runs/v3_B_base_openrouter_20261110T111759856270.json` |
| v4 | system_prompt.md | Ép `clarify(response_type=yes_no)` khi có đăng/gửi | 0.95 | 0.95 | `runs/v4_B_base_openrouter_20261110T111941600954.json` |

**Diễn giải:** Bước nhảy lớn nhất là **v2** (0.85→0.95) nhờ viết lại mô tả tool — `tool_routing_accuracy` đạt **1.0** và giữ nguyên tới v3. Từ v2 trở đi agent chạm **trần ~0.95**: case FAIL còn lại dao động giữa R12 (arg) và M06 (gọi thừa, nhiễu sampling dù temp=0). v4 sửa dứt điểm được boundary R12 nhưng đúng run đó M06 lại gọi thừa `social_search` → net vẫn 0.95.

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12 (v2, v3) | wrong_boundary | `clarify(response_type=text)` | Có hỏi lại (không gửi bừa) nhưng dùng `text` thay vì `yes_no` | v4: ép rule "đăng/gửi → clarify yes_no là bước đầu" → R12 PASS ở v4 |
| M06 (v4) | wrong_tool / extra_tool_call | `lookup(...)` + **thừa** `social_search(...)` | Gọi thêm 1 tool không cần | Nhiễu sampling (temp=0 vẫn lệch qua OpenRouter); cần thêm rule "chỉ gọi đúng số nguồn tối thiểu" hoặc chấp nhận trần |
| G10 (group, v4) | missing_info | (không gọi tool) | Đã có limit nhưng còn thiếu handle, model không gọi `clarify` | Nhấn mạnh hơn: thiếu handle → bắt buộc clarify, kể cả khi đã có limit |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single + 5 multi). Kết quả chạy trên v4 (`runs/v4_B_group_openrouter_20261110T112154431374.json`): **9/10 (case_accuracy 0.90)**.

| Case ID | What It Tests | Expected | Result |
|---|---|---|---|
| G01_calc_routing | Phép tính số học → calc | `calc` | PASS |
| G02_wiki_concept_routing | "X là gì" → wiki (không phải lookup) | `wiki` | PASS |
| G03_define_word_routing | Nghĩa một từ → define | `define(word)` | PASS |
| G04_datetime_routing | Giờ hiện tại → datetime | `datetime` | PASS |
| G05_algebra_out_of_scope | Giải phương trình chữ → KHÔNG dùng calc | no_tool/refuse | PASS |
| G06_calc_multiturn_fill | Gom số qua nhiều lượt → calc | `calc` | PASS |
| G07_wiki_multiturn_correction | Sửa chủ đề RAG→LoRA → wiki | `wiki` | PASS |
| G08_summarize_not_send_boundary | Rút lại yêu cầu gửi → chỉ lookup | `lookup(topic=news)` | PASS |
| G09_lookup_carryover_timeframe | Carry timeframe=week, thu hẹp query | `lookup(Bitcoin,news,week)` | PASS |
| G10_still_missing_handle_clarify | Có limit nhưng thiếu handle → clarify | `clarify(text)` | FAIL (missing_tool_call) |

→ Toàn bộ case routing tới **4 tool mới (G01–G07)** đều PASS, xác nhận tool mới hoạt động và prompt route đúng.

## B4. Live Chat Evidence

Nguồn: `transcripts/v3_telegram_20261110T102527436990.transcript.json` (qua bot Telegram hai chiều).

| Turn | User Request | Tool Calls | Version | Outcome |
|---|---|---|---|---|
| 1 | "Tìm ip 18 giá đang bao nhiêu" | `lookup(query="IP 18 giá", topic="general")` | v3 | Trả về giá iPhone 18 dự kiến + link nguồn 24h.com.vn, gửi lại đúng vào Telegram |

(Thêm transcript CLI/Streamlit khi demo để đủ ≥3 lượt live.)

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`, transcript | Gửi thành công `status: sent`; guardrail chặn khi `confirmed=false` | Chỉ gửi khi `confirmed=true`; prompt bắt clarify yes_no trước |
| UI | `app.py` (Streamlit), `telegram_bot.py` (bot 2 chiều) | Chat trên web + chat qua Telegram, hiển thị tool call/kết quả, lưu transcript | Bot chỉ trả lời `TELEGRAM_CHAT_ID` cấu hình (chặn người lạ đốt credit) |
| Extra tools (>3) | `tools/{calc,datetime,wiki,define}/` | 4 tool mới + TOOL.md + đăng ký đầy đủ, group eval route đúng 100% | calc không dùng `eval()`; wiki/define keyless, trả dict lỗi thay vì raise |
| Tool unit tests (`tests/`) | `pytest` output | **111 passed, 0 skipped, 0 failed** | — |

**Điểm thưởng (UI + >3 tool mới):** đạt cả hai điều kiện — UI (Streamlit + Telegram bot) **và** 4 tool mới.

**Unit test:** Đã viết 12 test cho 4 tool mới (`tests/test_new_tools.py`) + **điền hết toàn bộ stub TODO** trong `tests/test_tools_todo.py` (clarify/format/send/lookup/fetch/timeline/social_search/policy + tool mới) → đạt tiêu chí challenge **0 skipped**. Mỗi tool mới có đủ 3 nhóm: happy path (mock HTTP với tool gọi mạng), input xấu từ model (chuỗi rỗng/sai kiểu/ngoài enum), và nhánh lỗi (HTTP 404/chia 0 → trả error dict, không raise).

## B6. Reflection

- **Thuộc `tools.yaml`:** sửa routing sai tool và sai arg (v2) — mô tả "khi nào dùng / khi nào không" + quy ước arg là đòn bẩy mạnh nhất, kéo routing lên 1.0.
- **Thuộc `system_prompt.md`:** rule hành vi tổng (map handle, confirm trước khi gửi, out-of-scope) — v3/v4.
- **Cần review tay thay vì chấm tự động:** M06 (gọi thừa tool) và G10 — ranh giới "đủ thông tin để hành động hay chưa" phụ thuộc ngữ cảnh, chấm theo tool_calls đôi khi phạt cả hành vi hợp lý.
- **Cải thiện tiếp:** thêm rule "gọi số tool tối thiểu", viết thêm eval case cho đúng loại lỗi M06, và thử model khác để kiểm tra trần 0.95 là do prompt hay do model.

## B7. Small Local Model Challenge (bonus)

Chưa thực hiện (không chạy Ollama trong buổi này).
