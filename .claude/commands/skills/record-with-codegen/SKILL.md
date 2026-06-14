---
name: record-with-codegen
description: Thu thập locator cho màn hình MỚI/PHỨC TẠP bằng cách user record thao tác thật qua Playwright Codegen, rồi tinh chỉnh selector theo chuẩn kit và ghi vào file repository. Dùng khi auto-recon khó liệt kê đủ element (flow nhiều bước, cần hover/state nghiệp vụ), hoặc khi user muốn tự dẫn.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Record với Playwright Codegen (recon có người dẫn)

> Đọc `CLAUDE.md` + `.claude/commands/rules/locator_repository.md` trước. Chế độ này KHÔNG thay auto-recon — nó là một nguồn nạp khác cho file repository, mạnh ở màn phức tạp.
> **Chỉ chạy trên máy có màn hình** (Codegen mở cửa sổ browser tương tác). Không dùng trên CI/headless.

## Khi nào dùng

- Màn hình mới, khó liệt kê đủ element bằng snapshot tự động.
- Flow nhiều bước / cần state nghiệp vụ (giỏ hàng có hàng mới hiện checkout, hover mới ra submenu).
- Auto-recon đã sót hoặc fail.
- User muốn tự thao tác để chắc chắn đúng element.

## Quy trình

### Bước 1 — Khởi động Codegen (user thao tác)
Hướng dẫn user chạy lệnh trong terminal (KHÔNG tự chạy thay user — đây là phiên tương tác):
```bash
npx playwright codegen <url> -o /tmp/recording.spec.ts
# tuỳ chọn: --viewport-size="1920,1080"  | --target python  | --save-storage=auth.json (giữ login)
```
- User thực hiện đúng flow của test case trên cửa sổ browser.
- Trong Inspector: chuột phải → đổi selector quá rộng sang semantic (getByRole/getByLabel).
- Đóng browser → Codegen ghi file `/tmp/recording.spec.ts`.

### Bước 2 — Đọc & trích element
- `Read` file recording.
- Từ chuỗi hành động (`click`/`fill`/`check`...), **trích danh sách element duy nhất** (gộp các thao tác lặp trên cùng element).
- Map mỗi element → `action` (`type`/`click`/`check`/`assert`).

### Bước 3 — Tinh chỉnh locator (BẮT BUỘC — không nuốt thẳng)
Codegen output là **bản nháp**. Với mỗi element, áp skill `smart-locator`:
- Selector quá rộng (`#root`, `div > div`) hoặc css/nth-child → sinh lại theo priority `locator_strategy.md`.
- Chấm `stability` (high/medium/low) theo `locator_repository.md` mục 4.
- Sinh `fallback`.

### Bước 4 — Ghi vào repository
- Ghi/merge vào `output/locators/<screen>.screen.json` theo format trong `locator_repository.md`.
- Gắn `verifiedStates` theo state lúc record (vd nếu record sau khi submit sai → `after-invalid-login`).
- Cập nhật `lastVerified`.

### Bước 5 — Dọn
- Xoá `/tmp/recording.spec.ts` (file tạm).

## Giới hạn Codegen (báo user nếu gặp)

Recorder KHÔNG sinh được: hover menu, drag & drop, context menu (chuột phải), upload/download, browser dialog, keyboard shortcut, chuyển tab/cửa sổ. Với các thao tác này → bổ sung bằng auto-recon (`ui-debug-agent`) hoặc thêm element thủ công vào repository.
