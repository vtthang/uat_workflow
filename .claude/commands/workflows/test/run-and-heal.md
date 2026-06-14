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
| File testcase `.md` để ghi P/F | Đọc từ `task.md` (mục Handoff) | Tùy chọn |

**Ưu tiên đọc `task.md`** nếu có (do `/generate-automation-from-testcases` để lại). Thiếu input bắt buộc → hỏi user trước khi chạy.

---

## Các bước

### Bước 1 — Đọc context từ task.md

1. Tìm và đọc `task.md` trong project directory.
2. Lấy từ mục **Handoff**:
   - Tech stack và lệnh chạy
   - Danh sách file test cần chạy
   - Path file testcase `.md` (để ghi P/F)
   - TC nào đang tạm SKIP (thiếu file/điều kiện)
3. Nếu không có `task.md` → hỏi user cung cấp path file test và tech stack.
4. Xác nhận nhanh với user: *"Tôi sẽ chạy N file test: [danh sách]. Tiếp tục?"* — **chỉ hỏi 1 lần**, không hỏi thêm trong quá trình chạy.

---

### Bước 2 — Chạy Test

1. Chạy **toàn bộ suite đúng 1 lần** — không dừng khi gặp fail:
   ```bash
   npx playwright test <file|dir> --headed --reporter=list
   ```
   - Suite bao gồm cả `output/tests/_common/permission.spec.ts` (TC-PERM) nếu có — chạy cùng, heal như TC thường.
   - **Round mặc định = tiếng Việt.** KHÔNG tự chạy `test:en`; chỉ chạy `LOCALE=en npx playwright test` khi user yêu cầu kiểm tra tiếng Anh.

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

> **Ngoại lệ RULE 15 — sửa shared-code:** nếu fix chạm **code dùng chung** (POM, util, fixture, `isMainApi`/predicate, config) → KHÔNG chỉ re-run TC fail mà **re-run mọi TC phụ thuộc code đó** (cùng spec/POM). Lý do: fix có thể làm evidence của TC đang PASS trở nên sai/thiếu mà không báo lỗi. (Đã từng: sửa predicate API nhưng TC PASS cũ giữ evidence sai.)

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
| TC_01 | Login thành công | ✅ PASS | 0 | output/evidence/TC_01/ |
| TC_02 | Upload ảnh | ✅ PASS | 2 | output/evidence/TC_02/ |
| TC_03 | So sánh Figma | ⏭️ SKIP | — | Visual-only |

**Tổng: X PASS / Y FAIL / Z SKIP**

Files đã tạo/sửa: [danh sách]
Evidence: output/evidence/<TC_ID>/
Known issues: [nếu có]
Cảnh báo locator low-confidence: [nếu có]
```

## Output
- Test files đã PASS stable (≥ 2 lần)
- `task.md` cập nhật đầy đủ
- File testcase `.md` đã ghi P/F
- Evidence screenshots (`output/evidence/<TC_ID>/`)
- Báo cáo PASS/FAIL/SKIP

---

### Bước 5.5 — Evidence Completeness Gate (BẮT BUỘC trước report)

Theo `report_rules.md` §5: với **mỗi TC PASS**, verify đủ evidence (`api-calls.json` + `responseBody` main API + `data-mapping`/`search-count`/`filter-count` theo loại TC). **Thiếu → re-run TC đó dù đang PASS** (ngoại lệ RULE 15). Chỉ qua Bước tiếp theo khi gate xanh.

---

## Bước tiếp theo — sinh HTML report (local, KHÔNG Drive)

Sau khi gate xanh, **sinh HTML report tại local** từ evidence theo `html_report_rules.md`. Report PHẢI render đủ: screenshots · count-box · **Data Mapping** · API Calls (main highlight) · **Full response body** (collapsible):
- Output: `output/reports/{TenTinhNang}_report_{YYYY-MM-DD}.html` (tự chứa, ảnh embed base64)

**KHÔNG upload Drive** (đã bỏ). Khi trong `/full-pipeline`: workflow cha gọi Phase 4 report — run-and-heal không tự sinh để tránh trùng.
