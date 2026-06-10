---
description: Dựng khung (scaffold) một automation framework có khả năng scale cho project. Sinh project structure, base classes, driver management, wait utils, config, reporting. Dùng khi user nói "tạo framework automation", "scaffold project Playwright".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Dựng Automation Framework

> Đọc `CLAUDE.md` trước. Workflow này tạo *khung* để các workflow khác (from-testcases, from-ui-flow) sinh code vào đúng chỗ.

## Tech stack bắt buộc

| Hạng mục | Giá trị |
|---|---|
| Ngôn ngữ | TypeScript |
| UI Automation | Playwright |
| Test Framework | Playwright Test |
| Design Pattern | Page Object Model |
| Report | Playwright HTML Report |
| Logs | Playwright trace |

## Framework phải gồm

- **Driver/Browser management** — khởi tạo & teardown
- **Base test class / fixtures** — setup chung, login fixture
- **Page object structure** — thư mục `pages/`, `BasePage`
- **Wait utilities** — smart wait helpers (KHÔNG hard-sleep)
- **Configuration management** — 1 file `config/test.config.json` (env/account/URL) + `.env` cho secret, xem `.claude/commands/rules/config_management.md`
- **Reusable utilities** — `DataGenerator`, `WaitHelper`...
- **Test reporting** — HTML/Allure + screenshot-on-fail
- **CI config** — chạy headless mặc định (theo Browser Rules trong `CLAUDE.md`)

## Output
1. Project structure đề xuất (cây thư mục)
2. Các class khung chính
3. Base class ví dụ
4. Best practices bảo trì (đặt tên, tách concern — xem `.claude/commands/rules/automation_rules.md`)
