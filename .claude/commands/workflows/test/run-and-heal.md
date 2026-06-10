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

1. Chạy **toàn bộ suite đúng 1 lần** — không dừng khi gặp fail:
   ```bash
   npx playwright test <file|dir> --headed --reporter=list
   ```

2. Đọc stdout output: dòng có `✗` chứa tên test fail → extract TC ID theo pattern `TC-[A-Z0-9-]+` → đưa vào danh sách cần heal. Dòng có `✓` → ghi ✅.

3. **Heal từng TC FAIL** (tuần tự, KHÔNG chạy lại toàn suite):
   - Đọc log → phân tích root cause → sửa code
   - Chạy lại **chỉ TC đó** bằng `--grep`:
     ```bash
     npx playwright test --headed --grep "TC-XX"
     ```
   - PASS → ✅, chuyển sang TC fail tiếp theo
   - Vẫn FAIL → sửa thêm → chạy lại lần 2 (tối đa **2 lần sửa/TC**)
   - Sau 2 lần vẫn FAIL → **mark FAILED vĩnh viễn, chuyển TC tiếp theo ngay**

4. **Khi mark FAILED:**
   - Ghi root cause ngắn gọn vào `task.md`
   - **Tiếp tục TC kế tiếp ngay** — không hỏi user, không dừng, không chạy lại suite

> **Hard cap:** Tổng tối đa **10 lần sửa code** trong toàn bộ workflow (đếm qua mọi TC). Vượt cap → mark toàn bộ TC còn lại là FAIL, chuyển sang Bước 4.

---

### Bước 3 — Verify Stability

Bỏ qua — **1 lần PASS là đủ**. Không chạy lại TC đã PASS.

---

### Bước 4 — Cleanup

Theo checklist Definition of Done trong `CLAUDE.md`:

- [ ] Xoá `print()` / `console.log()` / debug log tạm
- [ ] Xoá locator không dùng, commented-out code, unused imports
- [ ] Không còn `waitForTimeout` hardcoded
- [ ] Không hardcode test data (email/username/ID phải random + traceable)
- [ ] Xoá file debug tạm (`*_debug.txt`, `snapshot_*.md`, `dom_dump.txt`) trong `/tmp/`

---

### Bước 5 — Ghi kết quả vào file testcase `.md`

Đọc file `.md` từ `task.md` (mục Handoff), với mỗi TC:
- Tìm dòng `#### TC-XX`
- Thêm hoặc cập nhật marker kết quả inline:
  - PASS → `#### TC-XX: <tên> — **✅ PASS**`
  - FAIL → `#### TC-XX: <tên> — **❌ FAIL** — <root cause ngắn gọn>`
  - SKIP → `#### TC-XX: <tên> — **⏭️ SKIP**`
- Dùng `Edit` tool ghi thẳng vào file `.md`, **không tạo file mới**.

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
