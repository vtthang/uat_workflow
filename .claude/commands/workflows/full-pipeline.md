---
description: Pipeline hoàn toàn tự động — spec → testcase → automation → run → deliver. Zero human intervention.
argument-hint: "<spec_docx> <tên tính năng>"
---

# Full Auto Pipeline — Spec → UAT → Automation → Deliver

Pipeline chạy tự động hoàn toàn. Không hỏi user bất kỳ điều gì trong quá trình chạy. Mọi quyết định đều tự động theo quy tắc bên dưới.

---

## QUY TẮC AUTO-DECISION (đọc trước khi bắt đầu)

| Tình huống | Quyết định tự động |
|---|---|
| UC không map được section TLGP | Auto-skip UC đó, ghi vào report, tiếp tục |
| UC mapping không chắc chắn | Auto-include (chọn section gần nhất), đánh dấu ⚠️ |
| TC cần file media (📎 CẦN FILE) | Auto-skip TC đó, ghi vào report |
| Không biết URL màn hình | Dùng ui-debug-agent khám phá navigation từ homepage |
| Cần API tạo test data | Fallback sang UI setup, ghi chú "flaky possible" |
| TC time-sensitive | Auto-skip, ghi vào report với lý do |
| Static verify còn ❌ | Auto-fix, không hỏi |
| Test FAIL sau 2 retry | Mark FAIL, chạy tiếp, không dừng |
| Bất kỳ lỗi không block toàn bộ | Log vào report, tiếp tục |

**Nguyên tắc:** Tiến về phía trước, không chờ. Chỉ dừng nếu lỗi block 100% pipeline (không đọc được file spec, không connect được app).

---

## INPUT

| Input | Cách lấy |
|---|---|
| File TLGP (.docx) | Argument 1 hoặc tìm trong `spec/` |
| Tên tính năng | Argument 2 |
| URL ứng dụng | Đọc từ `config/test.config.json` (activeEnv → baseUrl) |
| Credentials | Đọc từ `config/test.config.json` |

Thiếu file spec hoặc không có `baseUrl` → dừng và báo lỗi cụ thể. Đây là điều kiện duy nhất được phép dừng.

---

## PHASE 1 — SINH TEST CASE

*Thực hiện tương đương `/gen-uat` nhưng bỏ toàn bộ confirm.*

### 1A. Đọc TLGP
- Tìm section tương ứng với từng Use-case
- Extract: màn hình, đường dẫn, vùng tìm kiếm, bảng danh sách, thông báo hệ thống, luồng nghiệp vụ

### 1C. Auto-mapping UC → TLGP
Với mỗi UC:
- **Tìm thấy section rõ ràng** → include, tiếp tục
- **Không tìm thấy** → auto-skip UC này, ghi vào `pipeline_report.md`: `⏭️ Skip UC [N]: không tìm thấy section TLGP tương ứng`
- **Mapping không chắc** → auto-include với note ⚠️ trong report

**KHÔNG hỏi user. Tiếp tục với các UC đã map được.**

### 1D. Xác định TC
Với mỗi Transaction của UC đã map:
- Happy Path: luôn có
- Alternative Path: nếu TLGP mô tả luồng thay thế
- Unhappy Path: luôn có với transaction "xem/hiển thị danh sách" (case không có dữ liệu)
- Tách Happy Path thành nhiều TC nếu có variant input (full match + partial match → 2 TC)

**Pagination (tự động thêm khi màn có phân trang):**
Nếu TLGP mô tả pagination controls → tự động thêm đủ 8 TC (xem `testcase_writing_rules.md` RULE 9):
- TC-Px: Phân trang khi đủ dữ liệu (Happy Path)
- TC-Px+1: Chuyển sang trang tiếp theo (Happy Path)
- TC-Px+2: Chuyển về trang trước đó (Happy Path)
- TC-Px+3: Chuyển đến trang bất kỳ (Happy Path)
- TC-Px+4: Chuyển về trang đầu tiên (Happy Path)
- TC-Px+5: Chuyển đến trang cuối cùng (Happy Path)
- TC-Px+6: Trạng thái disabled đúng ở biên (Alternative Path)
- TC-Px+7: Không đủ dữ liệu — không phân trang (Unhappy Path)
- TC-Px+8: Đổi page size (Alternative Path, chỉ khi UI có dropdown page size)

**API response error (tự động thêm với transaction "tạo/sửa/xóa/action"):**
- Luôn thêm Unhappy Path: API trả 400 → UI hiển thị đúng error message

### 1E. Gen file output
Xuất ngay (không list TC để confirm):
- File: `testcase/KBKT_UAT_[TênTínhNăng].md`
- Cấu trúc: `##` UC → `###` Transaction → `####` TC
- Mỗi TC đủ 6 field: Actor, Loại luồng, Precondition, Dữ liệu mẫu, Các bước, Kết quả mong muốn

Ghi vào `pipeline_report.md`:
```
## Phase 1 — Gen Testcase
✅ File: testcase/KBKT_UAT_[TênTínhNăng].md
- X UC / Y Transaction / Z TC
⏭️ Skip: [danh sách UC bị skip + lý do]
```

---

## PHASE 2 — SINH AUTOMATION SCRIPTS

*Thực hiện tương đương `/generate-automation-from-testcases` nhưng bỏ toàn bộ confirm.*

### 2A. Parse test cases
- Đọc file `.md` từ Phase 1
- Parse danh sách TC: ID, Title, Steps, Expected, Test Data, Priority

### 2B. Đọc config
- Đọc `config/test.config.json`: activeEnv → baseUrl, accounts
- Xác định tech stack: Playwright TypeScript (mặc định)

### 2C. Phân loại TC — auto-decide không hỏi
- ✅ AUTO: implement ngay
- 📎 CẦN FILE: **auto-skip**, ghi vào report — `⏭️ Skip TC_XX: cần file [tên file] — không có sẵn`
- 🔄 AUTO (cần điều kiện): implement với note về precondition
- ⏭️ SKIP: skip với lý do (visual-only)

**KHÔNG hiển thị bảng phân loại cho user, không chờ phản hồi.**

### 2D. Khảo sát UI — auto navigation discovery
Với mỗi màn hình cần test, **KHÔNG hỏi user về URL**. Thay vào đó:

1. Đọc `locators/<screen>.screen.json` nếu đã có → tái dụng
2. Nếu chưa có → gọi `ui-debug-agent` với task:
   ```
   Từ homepage [baseUrl], tìm màn hình "[Tên màn hình]".
   Thử các hướng: sidebar menu, top nav, breadcrumb.
   Ghi lại URL thực tế tìm được và locators của các element cần test.
   ```
3. Nếu ui-debug-agent không tìm được màn hình → skip các TC thuộc màn đó, ghi vào report

### 2E. Thiết kế POM
- Mỗi page/screen → 1 Page class
- Locator lấy từ file repository (đã verify qua 2D)
- BasePage nếu chưa có

### 2F. Sinh scripts
- Mỗi TC AUTO → 1 test
- Assertion đầy đủ theo Expected Results
- Evidence: `BasePage.screenshot(tcId, tcName, step)` → `evidence/<env>/<portal>/<module>/<function>/[TC-ID][tc-name][step].png`
- Test data: random + traceable format `<PrefixCamelCase> ${suffix}` (không dùng underscore/ký tự đặc biệt)

**API Monitoring — BẮT BUỘC cho mọi test có action gọi API** (xem `test_execution_rules.md` Rule 12):
- Setup `apiLog` + `responseMap` listener trong `beforeEach` của mỗi describe block
- Sau action chính: `assertNoDuplicateApiCall(apiLog)` — phát hiện double-submit
- Bắt response: assert UI phản ánh đúng status + body (200 → success UI; 400 → error message từ server)
- `afterEach`: nếu FAIL → attach `api-calls.txt` vào report

**Pagination Assertions — BẮT BUỘC cho TC-Px** (xem `test_execution_rules.md` Rule 13):
- Verify tổng item từ API GET response khớp label UI
- Assert next/prev button state từng trang
- Assert không có duplicate GET khi navigate trang

### 2G. Static verify — auto-fix
Chạy checklist (filesystem, page state trace, API endpoints, assertion completeness).
Phát hiện ❌ → tự sửa ngay, không hỏi. Lặp đến khi sạch.

Ghi vào `pipeline_report.md`:
```
## Phase 2 — Automation Scripts
✅ Page Objects: [danh sách]
✅ Test files: [danh sách]
✅ Static verify: sạch
⏭️ Skip TCs: [danh sách + lý do]
```

---

## PHASE 3 — CHẠY TEST & AUTO-HEAL

*Thực hiện tương đương `/run-and-heal` nhưng bỏ confirm đầu.*

### 3A. Chạy test — không xác nhận trước
Chạy tất cả file test từ Phase 2 mà không hỏi:

```bash
npx playwright test tests/ --headed --reporter=list
```

### 3B. Xử lý kết quả — Rule E3 (bắt buộc)
- Full suite chạy **đúng 1 lần**
- PASS → ghi ✅
- FAIL → ghi ❌ tạm, note lại TC ID
- Sau khi full suite xong: với mỗi TC FAIL:
  - Phân tích log + sửa code
  - Chạy lại **duy nhất TC đó** bằng `--grep "TC-XX"`, tối đa **2 lần**
  - Vẫn FAIL sau 2 lần → mark ❌ vĩnh viễn, ghi vào report
- **TUYỆT ĐỐI KHÔNG chạy lại toàn bộ suite**

### 3C. Verify stability
Không chạy lại TC PASS để "verify stable" — 1 lần PASS là đủ.

### 3D. Cleanup
- Xóa debug log, console.log
- Xóa file debug tạm trong `/tmp/`

### 3E. Ghi kết quả vào file testcase `.md`
- Tìm dòng `#### TC-XX` → thêm marker inline:
  - PASS → `#### TC-XX: <tên> — **✅ PASS**`
  - FAIL → `#### TC-XX: <tên> — **❌ FAIL** — <root cause>`
  - SKIP → `#### TC-XX: <tên> — **⏭️ SKIP**`
- Dùng `Edit` tool ghi thẳng vào `.md`, không tạo file mới

Ghi vào `pipeline_report.md`:
```
## Phase 3 — Test Results
| TC ID | Tên | Kết quả | Vòng heal | Evidence |
|---|---|---|---|---|
| TC-LIST-01 | Xem danh sách khi có dữ liệu | ✅ PASS | 0 | evidence/uat/admin/... |
| TC-CREATE-01 | Tạo tài khoản thành công | ✅ PASS | 1 | evidence/uat/admin/... |

Tổng: X PASS / Y FAIL / Z SKIP
```

---

## PHASE 4 — DELIVERY

*Thực hiện tương đương `/deliver-to-drive` — tự động ngay sau Phase 3.*

### 4A. Sinh HTML Report
Trước khi upload, sinh file HTML report tự chứa từ evidence:
- Đọc tất cả `evidence/<env>/<portal>/<module>/<function>/` — thu thập JSON + ảnh
- Sinh `{TenTinhNang}_report_{YYYY-MM-DD}.html` tại root project
- Spec đầy đủ tại `html_report_rules.md`

### 4B. Upload lên Drive
- Upload HTML report + evidence folder lên Google Drive
- Cập nhật `pipeline_report.md` với Drive ID + link

---

## PIPELINE REPORT

Tạo `pipeline_report.md` ngay từ đầu, cập nhật liên tục sau mỗi phase:

```markdown
# Pipeline Report — [Tên tính năng] — [timestamp]

## Phase 1 — Gen Testcase
## Phase 2 — Automation Scripts
## Phase 3 — Test Results
## Phase 4 — Delivery

## Items bị skip (tổng hợp)
| Item | Lý do | Hành động cần thiết |
|---|---|---|
| UC3 | Không có section TLGP | Chờ BA bổ sung spec |
| TC_05 | Cần file avatar.jpg | User cung cấp rồi re-run |

## Cảnh báo
[Các ⚠️ đánh dấu trong quá trình chạy]
```

Sau khi hoàn thành tất cả phase, báo cáo tóm tắt cuối:

```
## Pipeline hoàn thành

Phase 1: X UC / Y TC sinh ra (Z UC skip)
Phase 2: A test files / B page classes (C TC skip)
Phase 3: X PASS / Y FAIL / Z SKIP
Phase 4: HTML report sinh ✅ | Upload Drive ✅

Report: {TenTinhNang}_report_{YYYY-MM-DD}.html
Chi tiết: pipeline_report.md
```
