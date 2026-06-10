---
description: Thực thi một chuỗi UI steps mô tả bằng lời (không có file TC sẵn) trên browser thật, thu thập locator và sinh automation scripts (POM + Test). Dùng khi user nói "automate UI flow này", "sinh script từ các bước thao tác".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Sinh Automation từ UI Flow

> Đọc `CLAUDE.md` trước. Khác `generate-automation-from-testcases` ở chỗ: **chưa có file TC** — agent tự khám phá bằng cách chạy thật trên browser.

## So sánh với from-testcases

| | from-ui-flow (workflow này) | from-testcases |
|---|---|---|
| Input | Mô tả UI steps bằng lời / chỉ URL | File TC có cấu trúc |
| Đã có TC | ❌ Chưa — tự khám phá | ✅ Có sẵn — đọc & convert |
| Approach | Chạy thật → thu thập → sinh code | Đọc TC → verify UI → sinh code |

## Tech stack

Bắt buộc **Playwright + TypeScript**.

## Các bước

1. **Phân tích UI flow**: parse các bước user mô tả thành chuỗi action + expected. Đọc `config/test.config.json` (môi trường + account, xem `config_management.md`). Xác định page đi qua. Tạo `task.md`.
2. **Khảo sát & thực thi UI** (delegate `ui-debug-agent` qua `Task`, cache-first): đọc `locators/<screen>.screen.json` trước; thiếu thì chạy step trên browser thu thập + ghi repository. Màn phức tạp → skill `record-with-codegen` (user tự record).
3. **Thiết kế POM**: mỗi page → 1 Page class, locator từ bước 2. Locator mới → `smart-locator`.
4. **Test data**: dùng `test-data-generator` cho field unique (traceable format).
5. **Sinh scripts**: Arrange-Act-Assert, smart wait, test độc lập. Theo `.claude/commands/rules/test_execution_rules.md`: exact text cho message, fill hợp lệ field khác, bắt request/response cho API, bắt request cho trim, evidence theo bước.
6. **Chạy & Auto-heal (Rule E3)**: như from-testcases — FAIL → phân loại → lỗi locator delegate `locator-healer`, tự sửa, tối đa 5 vòng, verify PASS 2 lần liên tiếp.
7. **Cleanup & Delivery**: theo Definition of Done trong `CLAUDE.md`, gồm đánh P/F vào file testcase gốc (không đổi data khác) + đường dẫn evidence.

## Output
- `task.md`, Page Object classes, Test classes, Test data utilities, Bảng Locator Collection, báo cáo PASS/FAIL/SKIP.
