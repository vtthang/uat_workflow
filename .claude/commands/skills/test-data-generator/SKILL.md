---
name: test-data-generator
description: Sinh test data có cấu trúc, unique, traceable cho automation (positive/negative/boundary/edge). Dùng khi cần tạo data cho test case, payload API, hoặc data-driven test. Auto-invoke khi đang sinh test cần input data.
allowed-tools: Read, Write, Bash
---

# Test Data Generator

Sinh data tin cậy cho automation test.

## Data rules

Mọi data phải: **Unique** (không trùng trong suite), **Deterministic** (cùng seed → cùng data khi cần), **Traceable** (nhìn ra test nào tạo).

## Unique pattern
```
<prefix>_<testName>_<timestamp>
```
Ví dụ: `auto_register_20260402133000`, `auto_login_1712024100@test.com`.

## Data types thường dùng
- Email: `auto_<testName>_<timestamp>@test.com`
- Username: `user_<testName>_<timestamp>`
- Phone: random 10 chữ số, prefix hợp lệ (`0912345678`)
- Password: trộn hoa/thường/số/ký tự đặc biệt (`Test@12345`)

## Data categories
- **Positive** — format hợp lệ, trong ràng buộc, đủ field bắt buộc
- **Negative** — thiếu field, sai format, ký tự không hợp lệ, giá trị đã tồn tại
- **Boundary** — min/max length, min+1, max-1, empty vs null, 0, số âm
- **Edge** — unicode/ký tự đặc biệt, chuỗi rất dài, HTML tag, whitespace đầu/cuối, mẫu SQL injection (cho security test)

## Constraints
- Tôn trọng validation từ DOM inspection (format date/phone...)
- Tránh trùng giữa các lần chạy
- KHÔNG chứa PII thật

## Output (JSON có cấu trúc)
```json
{
  "positive": [{ "email": "auto_tc01_20260402@test.com", "password": "Test@12345" }],
  "negative": [{ "email": "", "password": "Test@12345", "expectedError": "Email is required" }],
  "boundary": [{ "email": "a@b.co", "password": "12345678", "note": "Min length" }]
}
```

Chi tiết: `.claude/commands/rules/automation_rules.md` (Section 2).
