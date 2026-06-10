---
description: Chạy automation scripts, auto-heal đến PASS ổn định, cleanup và delivery. Dùng sau workflow `/generate-automation-from-testcases` hoặc khi cần chạy lại scripts đã có sẵn. Dùng khi user nói "chạy test", "run và heal", "chạy automation", "thực thi test cases".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Chạy Test & Auto-heal

> Đọc `CLAUDE.md` trước (Browser Rules, Rule E3, Definition of Done). Workflow này nhận scripts đã sinh → chạy → tự heal đến PASS ổn định → cleanup → delivery.

## Input cần thu thập

| Input | Cách lấy | Ưu tiên |
|---|---|---|
| Path file test hoặc thư mục | User cung cấp hoặc đọc từ `task.md` (mục Handoff) | ⭐ Bắt buộc |
| Tech stack / lệnh chạy | Đọc từ `task.md` (mục Handoff) hoặc user chỉ định | ⭐ Bắt buộc |
| File TC gốc (.xlsx) để ghi P/F | Đọc từ `task.md` (mục Handoff) hoặc user cung cấp | Tùy chọn |

**Ưu tiên đọc `task.md`** nếu có (do `/generate-automation-from-testcases` để lại). Thiếu input bắt buộc → hỏi user trước khi chạy.

---

## Các bước

### Bước 1 — Đọc context từ task.md

1. Tìm và đọc `task.md` trong project directory.
2. Lấy từ mục **Handoff**:
   - Tech stack và lệnh chạy
   - Danh sách file test cần chạy
   - Path file TC gốc (để ghi P/F)
   - TC nào đang tạm SKIP (thiếu file/điều kiện)
3. Nếu không có `task.md` → hỏi user cung cấp path file test và tech stack.
4. Xác nhận nhanh với user: *"Tôi sẽ chạy N file test: [danh sách]. Tiếp tục?"* — **chỉ hỏi 1 lần**, không hỏi thêm trong quá trình chạy.

---

### Bước 2 — Chạy Test

1. Chạy từng TC (hoặc từng file) bằng Playwright TypeScript:
   ```bash
   npx playwright test <file> --headed
   ```

2. **PASS** → ghi nhận ✅, chuyển sang TC tiếp theo.

3. **FAIL** → retry tối đa **2 lần** (không sửa code giữa các lần):
   ```bash
   npx playwright test <file> --headed   # lần 1 (đã fail)
   npx playwright test <file> --headed   # retry 1
   npx playwright test <file> --headed   # retry 2
   ```
   - Retry PASS → ghi ✅, tiếp tục.
   - Sau 2 retry vẫn FAIL → **mark FAILED, chạy TC tiếp theo** (không dừng toàn bộ).

4. **Khi mark FAILED:**
   - Chụp screenshot tại bước fail (nếu chưa có) → lưu `evidence/<TC_ID>/FAIL_<step>.png`
   - Ghi root cause ngắn gọn vào `task.md`:
     ```
     ❌ XTBV_42: Assertion fail — status trả về "Chờ duyệt" thay vì "Đã từ chối"
     ```
   - Ghi **FAIL** vào cột kết quả file Excel (Bước 5)
   - **Tiếp tục chạy TC kế tiếp ngay** — không hỏi user, không dừng.

---

### Bước 3 — Verify Stability

Với mỗi TC đã PASS, chạy thêm 1 lần nữa để xác nhận không flaky:

```bash
npx playwright test <file> --headed
```

- PASS → ✅ stable
- FAIL → áp dụng lại quy trình Bước 2 (retry 2 lần → nếu vẫn FAIL thì mark FAILED)

---

### Bước 4 — Cleanup

Theo checklist Definition of Done trong `CLAUDE.md`:

- [ ] Xoá `print()` / `console.log()` / debug log tạm
- [ ] Xoá locator không dùng, commented-out code, unused imports
- [ ] Không còn `waitForTimeout` hardcoded
- [ ] Không hardcode test data (email/username/ID phải random + traceable)
- [ ] Xoá file debug tạm (`*_debug.txt`, `snapshot_*.md`, `dom_dump.txt`) trong `/tmp/`

---

### Bước 5 — Ghi P/F vào file TC gốc

Nếu có file `.xlsx` từ `task.md` (mục Handoff):

1. Mở bằng `exceljs` (TypeScript), tìm cột kết quả theo TC ID.
2. Ghi: **PASS** / **FAIL** / **SKIP** + link evidence.
3. **KHÔNG đổi data/format khác**, chỉ ghi đúng cột kết quả.
4. Save lại file gốc. Báo rõ đã ghi N dòng.

---

### Bước 6 — Delivery Report

Cập nhật `task.md`: tick ✅ B6 và B7, thêm bảng kết quả cuối.

Báo cáo cho user:

```
## Kết quả chạy test
| TC ID | Tên | Kết quả | Vòng heal | Evidence |
|---|---|---|---|---|
| TC_01 | Login thành công | ✅ PASS | 0 | evidence/TC_01/ |
| TC_02 | Upload ảnh | ✅ PASS | 2 | evidence/TC_02/ |
| TC_03 | So sánh Figma | ⏭️ SKIP | — | Visual-only |

**Tổng: X PASS / Y FAIL / Z SKIP**

Files đã tạo/sửa: [danh sách]
Evidence: evidence/<TC_ID>/
Known issues: [nếu có]
Cảnh báo locator low-confidence: [nếu có]
```

## Output
- Test files đã PASS stable (≥ 2 lần)
- `task.md` cập nhật đầy đủ
- File TC gốc (.xlsx) đã ghi P/F
- Evidence screenshots (`evidence/<TC_ID>/`)
- Báo cáo PASS/FAIL/SKIP

---

## Bước tiếp theo

**Khi dùng độc lập** (user gọi `/run-and-heal` trực tiếp): Hỏi user có muốn deliver lên Drive không trước khi invoke `workflows:test:deliver-to-drive`.

**Khi trong `/full-pipeline`**: Workflow cha (full-pipeline) sẽ gọi Phase 4 deliver. **KHÔNG tự gọi deliver-to-drive** — tránh double-delivery.
