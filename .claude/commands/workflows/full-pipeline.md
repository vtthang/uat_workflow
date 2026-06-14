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
| TC cần file media | **Tự sinh file test** đúng format/size — không hỏi user, không skip |
| Không biết URL màn hình | Dùng ui-debug-agent khám phá navigation từ homepage |
| Cần API tạo test data | **Tạo qua UI 1 lần → bắt request → dựng API helper** tái dùng (không hỏi curl) |
| TC time-sensitive | Auto-skip, ghi vào report với lý do |
| **TC-PERM (phân quyền)** | **KHÔNG auto-skip.** Login persona role tương ứng từ config → assert deny. Chỉ skip nếu config thiếu persona cho role đó (ghi rõ "thiếu persona [role]") |
| **Ngôn ngữ** | Round mặc định = primary (tiếng Việt). Không sinh TC i18n riêng. Project ngôn ngữ thứ 2 chỉ chạy khi user yêu cầu |
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

### 1A. Đọc TLGP — xác định scope theo tên tính năng
- Trong TLGP, tìm section mô tả **tính năng được yêu cầu** (Argument 2).
- Từ đó liệt kê Use-case / màn / Transaction trong phạm vi tính năng.
- Extract: màn hình, đường dẫn, field + ràng buộc, bảng danh sách, thông báo hệ thống, luồng nghiệp vụ, **role/quyền**.

### 1C. Auto-xác định scope
- **Section mô tả rõ** → include.
- **Không tìm thấy section cho tính năng** → dừng, báo lỗi (spec không đủ).
- **Mô tả sơ sài** → auto-include với note ⚠️ trong report.

**KHÔNG hỏi user. Tiếp tục với các màn đã đủ spec.**

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

**Field validation — tự động với MỌI form có field nhập (tạo/sửa/reset/popup), áp ISTQB (skill `testcase-design`, RULE 11b + 12–15):**
Duyệt mỗi field: giá trị mặc định (R12) · bắt buộc 2 hướng outfocus+submit, không bắt buộc no-error, clear-first (R13) · độ dài BVA min-1/min/max/max+1 + ký tự EP (R14) · trùng dữ liệu + dropdown/checkbox/decision-table (R15). Message lỗi exact SRS, chỉ sinh nhánh SRS có quy định.

**Luồng nghiệp vụ — hậu điều kiện (RULE 16):** happy path verify thêm: thêm→search ra; sửa→mở lại đúng; xoá→mất; duyệt/từ chối→đổi status. Có case empty-state + search từ data thật.

**Nghiệp vụ liên quan (RULE 17):** đọc `knowledge/system-features.md` → thêm TC ảnh hưởng chéo nếu tính năng liên quan tính năng khác; **cập nhật file** này sau khi gen.

**Phân quyền (tự động thêm khi UC có >1 role/tác nhân) — xem `testcase_writing_rules.md` RULE 10:**
- Derive nhóm `TC-PERM-*` từ happy path: mỗi happy path = 1 action cần bảo vệ
- **Chỉ sinh phía deny** (role không được phép); phía allow đã được happy path chứng minh
- Gộp: role chặn ở cửa → 1 TC coarse/role; role giới hạn action → 1 deny-case kèm mỗi happy path
- Role login lấy từ persona trong `config/test.config.json` — auto-detect các role có persona; thiếu persona → ghi report, không bịa

**Đa ngôn ngữ (KHÔNG sinh TC riêng) — xem RULE 11:**
- Primary = tiếng Việt (mặc định). Mỗi TC (kể cả TC-PERM) tự chèn mục "Ngôn ngữ hiển thị"
- Mọi error/toast trích nguyên văn tiếng Việt (nguồn của `t()` ở Phase 2)

### 1E. Gen file output
Xuất ngay (không list TC để confirm):
- File: `output/testcase/KBKT_UAT_[TênTínhNăng].md`
- Cấu trúc: `##` UC → `###` Transaction → `####` TC
- Mỗi TC đủ 6 field: Actor, Loại luồng, Precondition, Dữ liệu mẫu, Các bước, Kết quả mong muốn

Ghi vào `output/pipeline_report.md`:
```
## Phase 1 — Gen Testcase
✅ File: output/testcase/KBKT_UAT_[TênTínhNăng].md
- X UC / Y Transaction / Z TC (trong đó P TC-PERM phân quyền)
- Ngôn ngữ primary: tiếng Việt — mọi TC có mục "Ngôn ngữ hiển thị"
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
- ✅ AUTO: implement ngay (kể cả TC cần file → **tự sinh file test** đúng format/size; TC cần data → **tạo qua UI → bắt request → dựng API helper**)
- 🔄 AUTO (cần điều kiện): implement với note về precondition
- ⏭️ SKIP: chỉ visual-only (Figma/font/màu/zoom)

**KHÔNG hiển thị bảng phân loại cho user, không chờ phản hồi.**

### 2D. Khảo sát UI — auto navigation discovery
Với mỗi màn hình cần test, **KHÔNG hỏi user về URL**. Thay vào đó:

1. Đọc `output/locators/<screen>.screen.json` nếu đã có → tái dụng
2. Nếu chưa có → gọi `ui-debug-agent` với task:
   ```
   Từ homepage [baseUrl], tìm màn hình "[Tên màn hình]".
   Thử các hướng: sidebar menu, top nav, breadcrumb.
   Ghi lại URL thực tế tìm được và locators của các element cần test.
   ```
3. Nếu ui-debug-agent không tìm được màn hình → skip các TC thuộc màn đó, ghi vào report

### 2E. Thiết kế POM
- Mỗi page/screen → 1 Page class
- **Feature POM → `output/pages/`**; BasePage/LoginPage (chung) → `src/pages/`
- Locator lấy từ file repository `output/locators/` (đã verify qua 2D)

### 2F. Sinh scripts
- Mỗi TC AUTO → 1 test, đặt trong `output/tests/<portal>/<feature>/` (TC-PERM → `output/tests/_common/`)
- Assertion đầy đủ theo Expected Results
- Evidence: `BasePage.screenshot(tcId, tcName, step)` → `output/evidence/<env>/<portal>/<module>/<function>/[TC-ID][tc-name][step].png`
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

**Cross-cutting — phân quyền + đa ngôn ngữ** (xem `generate-automation-from-testcases.md` Bước 5B):
- TC-PERM → `output/tests/_common/permission.spec.ts` + fixture `loginAs` (storageState/persona); chỉ sinh phía deny; thiếu persona → skip TC đó, ghi report
- Spec feature assert qua `t()` (không hardcode chuỗi) + `assertLocalizedUI(page)` cuối mỗi test; thêm script `test:en`, round mặc định = tiếng Việt

### 2G. Static verify — auto-fix
Chạy checklist (filesystem, page state trace, API endpoints, assertion completeness).
Phát hiện ❌ → tự sửa ngay, không hỏi. Lặp đến khi sạch.

Ghi vào `output/pipeline_report.md`:
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
npx playwright test output/tests/ --headed --reporter=list
```

### 3B. Xử lý kết quả — Rule E3 (bắt buộc)
- Full suite chạy **đúng 1 lần**
- PASS → ghi ✅
- FAIL → ghi ❌ tạm, note lại TC ID
- Sau khi full suite xong: với mỗi TC FAIL:
  - Phân tích log + sửa code
  - Chạy lại **duy nhất TC đó** bằng `--grep "TC-XX"`, tối đa **2 lần**
  - Vẫn FAIL sau 2 lần → mark ❌ vĩnh viễn, ghi vào report
- **TUYỆT ĐỐI KHÔNG chạy lại toàn bộ suite** — TRỪ khi fix chạm **shared-code** (POM/util/predicate/config): khi đó re-run mọi TC phụ thuộc code đó (kể cả TC đang PASS) để evidence không bị sai âm thầm.

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

Ghi vào `output/pipeline_report.md`:
```
## Phase 3 — Test Results
| TC ID | Tên | Kết quả | Vòng heal | Evidence |
|---|---|---|---|---|
| TC-LIST-01 | Xem danh sách khi có dữ liệu | ✅ PASS | 0 | output/evidence/uat/admin/... |
| TC-CREATE-01 | Tạo tài khoản thành công | ✅ PASS | 1 | output/evidence/uat/admin/... |
| TC-PERM-01 | Partner không truy cập được màn | ✅ PASS | 0 | output/evidence/uat/_common/permission |

Tổng: X PASS / Y FAIL / Z SKIP
  - Feature: A PASS / B FAIL / C SKIP
  - Phân quyền (TC-PERM): D PASS / E FAIL / F SKIP (thiếu persona)
  - Ngôn ngữ: round tiếng Việt (mặc định); EN chạy khi user yêu cầu
```

---

## PHASE 3.5 — EVIDENCE COMPLETENESS GATE (bắt buộc, trước report)

Theo `report_rules.md` §5: với **mỗi TC PASS**, verify đủ evidence (`api-calls.json` + `responseBody` main API + `data-mapping`/`search-count`/`filter-count` đúng loại). Thiếu → **re-run TC đó dù đang PASS** (ngoại lệ Rule 15). Chỉ sang Phase 4 khi gate xanh hoàn toàn. Ghi kết quả gate vào `output/pipeline_report.md`.

---

## PHASE 4 — REPORT (local, KHÔNG upload Drive)

*Chỉ sinh HTML report tại local. Không đẩy lên Drive.* Report PHẢI render: screenshots · count-box · **Data Mapping** · API Calls (main highlight) · **Full response body** (collapsible).

### 4A. Sinh HTML Report
- Dùng `python3 scripts/gen_report.py <testcase.md> <evidence_root> <out.html> "<title>"` — tự đọc testcase lấy **title + steps + expected + actual** (status từ marker P/F trong testcase), gộp evidence (ảnh + count-box + Data Mapping mọi cột + API Calls fetch/xhr main + full response).
- Output: `output/reports/{TenTinhNang}_report_{YYYY-MM-DD}.html` (tự chứa, ảnh embed base64)
- Spec đầy đủ tại `html_report_rules.md` + `report_rules.md` §4b
- Cập nhật `output/pipeline_report.md`

---

## PIPELINE REPORT

Tạo `output/pipeline_report.md` ngay từ đầu, cập nhật liên tục sau mỗi phase:

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
Phase 4: HTML report sinh ✅ (output/reports/) — KHÔNG upload Drive

Report: output/reports/{TenTinhNang}_report_{YYYY-MM-DD}.html
Chi tiết: output/pipeline_report.md
```
