# RUNBOOK — các lệnh chạy sau khi đã cài dependency + điền key trong `.env`

## 0. Cài 1 lần duy nhất

```bash
cd starter_v0
pip install -r requirements.txt
```

`.env` đã được tạo sẵn ở `starter_v0/.env` — chỉ cần điền:

- `OPENROUTER_API_KEY` (provider chính)
- `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY` (tool lookup / fetch / twitter)
- (tuỳ chọn) `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` nếu muốn demo send

## 1. Kiểm tra

```bash
pytest -v                          # mục tiêu: 0 failed, 0 skipped
python scripts/preflight_provider.py --provider openrouter
```

## 2. Baseline v0 — PHẢI dùng bản starter gốc (đã backup sẵn)

Bản starter gốc được giữ tại `artifacts/system_prompt_v0_starter.md` + `artifacts/tools_v0_starter.yaml`.
Baseline v0 PHẢI chạy bằng 2 file này (đúng nghĩa baseline trước khi nhóm sửa gì):

```bash
python run_eval.py --provider openrouter --version v0 --suite base `
  --eval-cases data/eval_base.json `
  --system-prompt artifacts/system_prompt_v0_starter.md --tools artifacts/tools_v0_starter.yaml
```

Đọc run JSON trong `runs/`: mất bao nhiêu case, sai loại gì (`observed_mismatch`, `failures`).

*(Lưu ý: sống sót PowerShell dùng backtick `; chạy Bash dùng `\` như trong README.)*

## 3. v1 → v2 → v3 (mỗi version một giả thuyết, sửa nên một thứ)

- **v1** — sửa `artifacts/system_prompt.md` (đã có bản tối ưu sẵn): giả thuyết "prompt starter xúi agent đoán và gửi không xác nhận làm route sai".
- **v2** — viết lại `artifacts/tools.yaml` (đã có bản tối ưu sẵn): giả thuyết "description mơ hồ làm model nhầm timeline/social_search/lookup và sai convention args".
- **v3** — tinh chỉnh cả 2 dựa trên lỗi còn lại của v1/v2.

Điền mỗi run vào `artifacts/version_log.csv` theo cột đã có: lấy `artifact_version`, `prompt_hash`, `tools_hash`, các metric từ run JSON (`summary.case_accuracy`, `tool_routing_accuracy`, `argument_accuracy`, `multiturn_accuracy`) — metric_before của v1 = metric của v0...

## 4. Eval nhóm (suite group, 10 case mới)

```bash
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

## 5. Chat live — cần 3 lượt (transcripts/*.transcript.json)

```bash
python chat.py --provider openrouter --version v3
```

3 lượt chuẩn: (1) request research bình thường; (2) request thiếu handle/URL — agent phải `clarify`; (3) request "đăng lên Telegram" — quan sát hỏi lại trước hay gửi ngay.

## 6. UI

```bash
streamlit run app.py          # mở http://localhost:8501
```

Expose link public (nếu cần khi demo):

```bash
cloudflared tunnel --url http://localhost:8501
```

Copy URL vào `artifacts/REPORT.md` Phần A (mục "Link dùng thử").

## 7. Nộp bài checklist nhanh

- [ ] `runs/*.json` (v0..v3 + group)
- [ ] `artifacts/version_log.csv` ≥ 4 dòng
- [ ] `artifacts/REPORT.md` Phần A trước 16:30 (phần link URL còn trống ▸ điền khi deploy)
- [ ] `transcripts/*.transcript.json` ≥ 3 lượt chat live
- [ ] `pytest` 0 failed, 0 skipped
- [ ] KHÔNG nộp `.env` / key
