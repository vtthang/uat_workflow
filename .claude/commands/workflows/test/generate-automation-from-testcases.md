---
description: Convert file manual test cases (MD/Excel/JSON/URL) thành automation scripts hoàn chỉnh (POM + Test) theo framework AI-RBT. Tự inspect UI thật, thu thập locator, sinh code. Kết thúc ở static verify — chạy test bằng workflow `/run-and-heal`. Dùng khi user nói "convert test case sang automation", "sinh Playwright từ test case".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Sinh Automation Scripts từ Manual Test Cases

> Đọc `CLAUDE.md` trước (Browser Rules, Definition of Done) và `.claude/commands/rules/locator_repository.md`. Workflow này điều phối 2 subagent — `ui-debug-agent` (recon, cache-first vào locator repository) và `locator-healer` (auto-heal) — qua tool `Task`, và 3 skill `smart-locator`, `test-data-generator`, `record-with-codegen`.

Đọc file manual TC → inspect UI thật → thu thập locator → sinh POM + Test → static verify.
**Để chạy test và auto-heal:** dùng workflow `/run-and-heal` sau khi workflow này hoàn thành.

## Nguyên tắc thực thi

- Vai trò Senior Automation Engineer, Clean Code + POM. Output tiếng Việt.
- **TUYỆT ĐỐI KHÔNG đoán locator** — phải verify trên DOM thật (qua `ui-debug-agent`).
- Desktop viewport 1920×1080 cho mọi UI debug.
- **Rule E3:** test FAIL → tự đọc log → phân tích → sửa → chạy lại. CẤM hỏi user trong lúc fix; chỉ hỏi khi business rule mâu thuẫn hoặc hết 5 vòng auto-heal.
- PHẢI tạo artifact `task.md` theo dõi tiến độ.

## Input cần thu thập

| Input | Cách lấy | Ưu tiên |
|---|---|---|
| File test cases (MD/Excel/JSON/URL) | User cung cấp path/URL | ⭐ Bắt buộc |
| URL ứng dụng | User cung cấp hoặc trong TC | ⭐ Bắt buộc |
| Credentials (nếu login) | User cung cấp hoặc fixture | Tùy chọn |
| Tech stack | User chỉ định hoặc detect từ project | Tùy chọn |

Thiếu input bắt buộc → hỏi trước khi bắt đầu.

## Các bước

### Bước 1 — Phân tích & Lên kế hoạch
1. Đọc file TC: local → `Read`; URL → fetch. Xác định format (MD table / Excel / JSON / free-text).
2. **Đọc `config/test.config.json`** (xem `.claude/commands/rules/config_management.md`): xác định môi trường (`activeEnv`/`ENV`) → base URL, và account cần dùng (admin/user/guest). Thiếu config → tạo từ `test.config.example.json` và hỏi user điền `.env`.
   - **Nếu file TC có nhóm TC-PERM (phân quyền):** liệt kê các **persona/role có sẵn** trong config (mỗi portal → `accounts.<persona>.role`). TC-PERM nào cần role chưa có persona trong config → **không bịa**, ghi vào report "thiếu persona [role]" và skip đúng TC đó (các TC-PERM khác vẫn implement).
3. Parse: danh sách TC (ID, Title, Steps, Expected, Test Data, Priority), các page đi qua, pre-conditions, dependencies giữa TC.
4. Xác định tech stack (mặc định Playwright + TypeScript; xem bảng trong `CLAUDE.md`).
5. **Phân loại TOÀN BỘ TC** — Khi dùng **độc lập**: hiển thị bảng cho user trước khi tiếp tục. Khi trong **`/full-pipeline`**: phân loại nội bộ, không hiển thị, không chờ xác nhận.

   **Quy tắc phân loại (theo thứ tự ưu tiên):**
   - ✅ **AUTO** — implement được (kể cả case cần file/test-data — TỰ sinh, không hỏi user)
   - 🔄 **AUTO (cần điều kiện)** — cần precondition đặc biệt (bài quá hạn, 2 session, cross-portal)
   - ⏭️ **SKIP** — chỉ skip khi THỰC SỰ không có assertion được (so Figma/màu sắc/font/zoom)

   **Nguyên tắc "đừng skip vội":**
   - Case check DB → thay bằng verify UI (danh sách, màn chỉnh sửa) — **không cần query DB**
   - Case upload file → **tự sinh file test** đúng format/size yêu cầu — **không hỏi user, không skip**
   - Case cross-portal → login portal kia, kiểm tra item theo title/ID — **không skip**
   - Case concurrent → dùng 2 browser context trong 1 test — **không skip**
   - Case "click ngoài popup không đóng" / "click vùng không cho phép" → assert popup vẫn visible — **không skip**
   - Chỉ SKIP khi: so sánh Figma, kiểm tra font/màu/khoảng cách pixel-perfect, zoom browser

   **Format bảng phân loại:**
   ```
   | TC ID | Mục đích | Quyết định | Ghi chú |
   |---|---|---|---|
   | TC_01 | Login thành công | ✅ AUTO | |
   | TC_02 | Upload ảnh hợp lệ | ✅ AUTO | tự sinh avatar.jpg (<2MB) |
   | TC_03 | So sánh giao diện Figma | ⏭️ SKIP | Visual-only, không có assertion |
   ```

   **File test — TỰ SINH, không hỏi user (môi trường UAT không có sẵn file):**

   Khi TC cần file (ảnh/PDF/doc), **tự sinh file đúng yêu cầu** (format + size) bằng skill `test-data-generator` / script:
   - Ảnh hợp lệ jpg/png: sinh ảnh nhỏ (canvas / base64 mẫu); ảnh quá size: pad tới >2MB/>5MB.
   - PDF/doc: sinh file tối thiểu đúng định dạng + size yêu cầu.
   - Lưu file sinh ra ở thư mục tạm của test, cleanup sau test. **Không commit file test.**

   **Test data có state (Sửa/Xoá/Duyệt/Từ chối/trùng) — TỰ TẠO QUA UI để bootstrap API, không hỏi curl:**

   Môi trường UAT không cung cấp sẵn curl/API. Cách làm:

   > **Bootstrap API từ UI (lần đầu) → tái dùng API (lần sau):**
   > 1. Lần đầu cần data: thực hiện thao tác **tạo mới trên UI thật**, đồng thời **bắt request** của action đó:
   >    ```typescript
   >    const [req] = await Promise.all([
   >      page.waitForRequest(r => r.url().includes('/api/') && r.request().method() === 'POST'),
   >      createPage.submit(),
   >    ]);
   >    // Ghi lại: req.url(), req.method(), req.headers() (Authorization), req.postData()
   >    ```
   > 2. Từ request bắt được → dựng helper `_create_<entity>_via_api()`: cùng URL/method/body shape, token lấy từ session login (header `Authorization`).
   > 3. Lưu payload shape vào `src/fixtures/<feature>-fixture.json` để các lần/test sau gọi thẳng API (~200ms), không lặp lại UI.

   **Tại sao:** UI setup chậm/flaky; sau khi đã có API helper thì tạo data nhanh + ổn định. Lần đầu chấp nhận chậm để **tự lấy được curl** mà không phụ thuộc user.

   Cleanup item tạo ra sau test nếu cần giữ môi trường sạch. Ghi API đã bootstrap vào `task.md`.

   **Phát hiện TC time-sensitive → đề xuất chiến lược batch:**

   Khi TC cần **trạng thái thời gian** (bài quá hạn, lịch đăng đã qua, phiên hết hạn...):
   - **KHÔNG** tạo data với timestamp cố định trong quá khứ (dễ sai múi giờ, flaky)
   - **Tạo data với `scheduledTime = now()`** ngay đầu session → chạy batch TC khác trước → quay lại khi data đã tự nhiên quá hạn
   - Đặt tên data theo TC ID để tìm kiếm được: `"<TC_ID>_<mô_tả>_<timestamp>"`
   - Lưu IDs vào `src/fixtures/<feature>-fixture.json` để batch sau đọc vào — **KHÔNG lưu vào `output/test-results/`** vì Playwright tự động xóa thư mục này trước mỗi lần chạy
   - Ghi rõ trong `task.md`: danh sách TC time-sensitive, article tương ứng, thứ tự chạy
   - Xem `test_execution_rules.md` mục 7 để biết chi tiết.

6. Tạo `task.md`:
   ```markdown
   # Automation Generation Progress
   - [x] B1: Phân tích test cases
   - [ ] B2: Khảo sát UI (recon)
   - [ ] B3: Thiết kế POM
   - [ ] B4: Chuẩn bị test data
   - [ ] B5: Sinh scripts
   - [ ] B6: Chạy test + Auto-heal
   - [ ] B7: Cleanup + Delivery

   ## Phân loại TC
   | TC ID | Mục đích | Quyết định | Ghi chú |
   |---|---|---|---|
   | TC01 | Login thành công | ✅ AUTO | |
   | TC02 | Upload ảnh | ✅ AUTO | tự sinh avatar.jpg (<2MB) |
   ```

### Bước 1.5 — Navigation flow discovery

Với **mỗi màn hình cần test**, xác định navigation theo thứ tự ưu tiên:

1. **Đọc `output/locators/<screen>.screen.json`** nếu đã có → lấy URL từ đó (field `url` hoặc `navigatePath`)
2. **Đọc `config/test.config.json`** xem có routing map không
3. **Gọi `ui-debug-agent`** để tự khám phá từ homepage → ghi URL vào locator repository

**Khi đang trong `/full-pipeline`** (zero intervention): Tự quyết định theo thứ tự trên, **KHÔNG hỏi user**.

**Khi dùng độc lập** (không trong pipeline): Nếu cả 3 nguồn trên đều không có URL → hỏi user 1 lần trước khi tiếp tục:
```
## Cần xác nhận navigation flow
Màn hình [Tên màn hình]: có URL trực tiếp không? (VD: /admin/users/create)
Hay phải qua UI steps? Nếu vậy: đi từ đâu → click gì?
```

**KHÔNG suy luận URL từ pattern** hay dùng URL từ project cũ khi chưa xác nhận.

### Bước 2 — Khảo sát UI (delegate `ui-debug-agent`, cache-first)
- Gọi subagent `ui-debug-agent` qua `Task`, truyền: URL + danh sách page/element theo TC + credentials nếu cần.
- Subagent **đọc `output/locators/<screen>.screen.json` trước** — có đủ thì tái dùng (bỏ qua mở browser), thiếu thì recon bổ sung. Kết quả ghi vào file repository (xem `.claude/commands/rules/locator_repository.md`).
- Màn phức tạp / khó inventory tự động (flow nhiều bước, cần hover/state nghiệp vụ) → dùng skill `record-with-codegen` để user tự record, rồi tinh chỉnh vào repository.
- Lưu tóm tắt Locator Collection vào `task.md`. Không tự mở browser trong context chính.
- **Ghi API endpoint thật vào locator repo** (field `apiEndpoints` per screen): khi recon, đọc network → ghi URL + method của **main API** từng màn (list GET, detail GET, create POST, update PUT...). `isMainApi` ở Bước 5 LẤY TỪ ĐÂY, **KHÔNG đoán** (xem `test_execution_rules.md` Rule 20). Tránh lỗi predicate bắt nhầm document/asset → evidence rỗng.

#### ⚠️ Kiểm tra giá trị mặc định (BẮT BUỘC khi recon)

**Bước 2a — Inventory giá trị mặc định (làm khi recon):**

Khi mở màn hình để khảo sát, **kiểm tra từng field** xem có giá trị sẵn không. Với mỗi field:

| Field | Có giá trị mặc định? | Ghi chú |
|---|---|---|
| Tiêu đề | ✅ Có ("Bài viết ABC") | Text từ record gốc |
| Thumbnail | ✅ Có (ảnh preview) | Có nút Remove/Delete |
| Nội dung editor | ✅ Có (HTML content) | TipTap/ProseMirror |
| Trường mới/trống | ❌ Không | Không cần clear |

**Ghi lại vào `task.md`** danh sách field có giá trị mặc định để dùng ở Bước 5:
```markdown
## Fields có giá trị mặc định — màn [Tên màn]
- thumbnail: ✅ có ảnh sẵn, nút xóa = `button[aria-label="Remove file"]`
- richTextEditor: ✅ có content sẵn, clear = Ctrl+A + Delete
- fieldTieuDe: ✅ disabled (read-only), không cần clear
- fieldEmail: ❌ trống sẵn
```

---

**Bước 5 — Sinh script validate: luôn clear trước khi test**

Khi TC là **validate một field** (test error message, outfocus, required...) trên màn có data mặc định:

> **Quy tắc:** Field nào có giá trị mặc định → **clear trước** → sau đó mới thực hiện thao tác validate

```typescript
// ✅ ĐÚNG — clear field có data mặc định trước khi validate
await newsReviewPage.removeThumbnail();           // xóa ảnh thumbnail mặc định
await newsReviewPage.thumbnailUploadInput.focus(); // focus vào field trống
await newsReviewPage.richTextEditor.click();       // outfocus → error hiện ra

// ✅ ĐÚNG — clear rich text editor trước khi test validate empty
await newsReviewPage.clearEditor();   // Ctrl+A + Delete qua keyboard
await newsReviewPage.breadcrumbNav.click(); // outfocus → error hiện ra
```

**Quy tắc clear theo loại field:**

| Loại field | Cách clear | Lưu ý |
|---|---|---|
| Input / Textarea | `.fill('')` hoặc `Ctrl+A → Delete` | |
| Rich text editor (TipTap/ProseMirror) | `Ctrl+A → Delete` qua `page.keyboard` | KHÔNG dùng `.fill()` — bypass event handler |
| File upload / Image | Click nút **Delete/Remove** trên preview | Verify locator trên DOM thật. KHÔNG dùng `input[type=file].click()` — mở file dialog |
| Dropdown / Select | Clear action của component hoặc chọn placeholder | |

**Trigger outfocus sau khi clear:**
- KHÔNG click vào `input[type="file"]` → mở file dialog
- Dùng click vào element an toàn: breadcrumb, nav, heading, rich text editor

### Bước 3 — Thiết kế POM
1. Mỗi page/screen → 1 Page class.
   - **POM theo feature** (UserListPage, ArticleCreatePage...) → ghi vào **`output/pages/`** (artifact generated, bị loại khi chia sẻ).
   - **POM dùng chung / framework** (`BasePage`, `LoginPage`) → giữ ở **`src/pages/`** (đã là code khung; `src/fixtures/base.fixture.ts` import từ đây).
2. Sinh Page class (`Write`), cấu trúc: Locators (đầu class, từ B2) → Constructor → Action methods (mô tả hành vi: `login()`, không `clickButton()`) → Verification methods.
   - Feature POM ở `output/pages/` extends `BasePage` từ `src/pages/` — chú ý import path tương đối đúng độ sâu.
3. Locator lấy từ **file repository** `output/locators/<screen>.screen.json` (B2 đã ghi, đã verify) — KHÔNG đoán lại. Cần locator mới phát sinh → dùng skill `smart-locator` rồi ghi bổ sung vào repository.
4. Kiểm tra structure hiện có, không tạo duplicate. Đặt file đúng thư mục theo (1).

### Bước 4 — Test Data (dùng `test-data-generator`)
1. Phân loại data: unique-per-run (email/username/ID) → sinh random + traceable; cố định → env/config; data-driven → file external.
2. Format traceable: `<prefix>_<testName>_<timestamp>` (vd `auto_login_1712049200@test.com`).
3. Sensitive data (credentials): lấy account từ `config/test.config.json` (password resolve từ `.env`) — xem `config_management.md`. KHÔNG hardcode, KHÔNG đọc `.env` trực tiếp. Base URL cũng lấy từ config theo môi trường.

### Bước 5 — Sinh Scripts
1. Mỗi TC (hoặc nhóm TC liên quan) → 1 test file. Cấu trúc Arrange-Act-Assert.
2. **Trước khi code từng TC:** đọc TOÀN BỘ cột "Kết quả mong muốn" — liệt kê tất cả các điểm cần assert. KHÔNG bỏ sót bất kỳ điểm nào. Xem `test_execution_rules.md` mục 0.
3. Assertion bắt buộc theo `.claude/commands/rules/test_execution_rules.md`:
   - **Exact text** cho error/toast (mục 1) — `toHaveText` / `exact:true`, lấy nguyên văn từ cột Expected. KHÔNG substring.
   - **Test 1 field validation** → fill hợp lệ mọi field khác để cô lập (mục 2).
   - **Giá trị mặc định** (màn sửa/duyệt/chi tiết) → tạo qua API → `toBe(value)`, không `toBeTruthy()` (mục 2b). Phục vụ `testcase_writing_rules.md` RULE 12.
   - **Validate bắt buộc / độ dài / ký tự** (RULE 13–14) → clear field có default trước (Bước 5), trigger đủ 2 hướng outfocus + submit; phân loại submit-vs-validate (mục 1b).
   - **Case "không có dữ liệu" / lỗi server** (RULE 16.3) → ép bằng `page.route` giả response rỗng/lỗi (mục 19), không xoá data thật.
   - **Case gọi API** → bắt request/response, assert status + body (mục 3).
   - **Case trim** → bắt request, đọc payload, assert giá trị đã/chưa trim (mục 4). KHÔNG đoán qua UI.
   - **API Monitoring** (mục 12) — **BẮT BUỘC cho MỌI describe block**, không trừ case nào:
     - Dùng utility **`src/utils/ApiMonitor.ts`** (có sẵn trong project). Import `setupApiMonitor`, `teardownApiMonitor`, `assertNoDuplicateApiCall`, `ApiLogEntry`.
     - **Khai báo ngoài các test** (describe scope):
       ```typescript
       const EVIDENCE_DIR = 'output/evidence/uat/admin/<module>/<function>';
       const apiLog: ApiLogEntry[] = [];
       // isMainApi = URL + method — KHÔNG dùng URL đơn lẻ
       const isMainApi = (res: { url(): string; request(): { method(): string } }) =>
         /\/api\/endpoint/i.test(res.url()) && res.request().method() === 'POST';
       ```
     - **`test.beforeEach`**: `apiLog.length = 0; setupApiMonitor(page, apiLog, isMainApi);`
     - **`test.afterEach`**: `await teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR);`
       → Ghi **1 file** `<slug>_api-calls.json` cho **mọi TC** (cả PASS lẫn FAIL).
       Mỗi entry: `{ method, url, status, time }`. Riêng main API entry có thêm `responseBody`.
       Filter `e.responseBody != null` để tìm main API calls khi cần đọc lại.
       → Nếu FAIL: attach thêm `api-calls.txt` vào Playwright report.
     - **Sau mỗi action gọi API**: `assertNoDuplicateApiCall(apiLog)` — phát hiện double-submit.
     - **Bắt response main API**: dùng `Promise.all([page.waitForResponse(...), action()])` — assert status + body → assert UI phản ánh đúng (200 → toast thành công; 400 → error message từ server body, không hardcode).
   - **Pagination** (mục 13) — **BẮT BUỘC** khi TC thuộc nhóm TC-Px:
     - Verify tổng item từ API response khớp label trên UI
     - Assert trạng thái next/prev button theo từng trang
     - Assert không có duplicate GET call khi navigate trang
4. **Evidence** (mục 5): chụp ảnh ở các mốc quan trọng mỗi case dùng `BasePage.screenshot(tcId, stepLabel)` **(2 tham số)**. File lưu tại `output/evidence/<env>/<portal>/<module>/<function>/[TC-ID][stepLabel].png`. Bật trace cho case fail. Khi FAIL: attach `api-calls.txt` (Rule 12d).
   - **JSON evidence — BẮT BUỘC** theo `.claude/commands/rules/report_rules.md`:
     - `test.afterEach` → `teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR)` → tự động lưu `{tcId}_api-calls.json` cho **mọi TC**
     - TC có main API → lưu thủ công `{tcId}_api-response.json` (full response body, có `pagination` + `items`)
     - TC danh sách (row 1) / chi tiết / sửa / phê duyệt (full field) → lưu thủ công `{tcId}_data-mapping.json` (so sánh API ↔ UI field-by-field) — xem `test_execution_rules.md` mục 12e
     - TC tìm kiếm → lưu thủ công `{tcId}_search-count.json` (keyword, apiTotal, uiRowCount)
     - TC lọc → lưu thủ công `{tcId}_filter-count.json` (filter, apiTotal, uiRowCount)
     - **tcId trong test title phải bắt đầu bằng `TC-{FUNC}-{NN}`** để `teardownApiMonitor` extract đúng (VD: `'TC-LIST-01 Xem danh sach'`)
     - Xem `report_rules.md` §2-3 để biết cấu trúc từng file
5. Code: không hard-sleep (chỉ smart wait), không inline locator, import gọn, test độc lập, cleanup data đã tạo trong teardown.

### Bước 5B — Cross-cutting: Phân quyền + Đa ngôn ngữ

> Áp dụng khi file TC có nhóm `TC-PERM-*` (phân quyền) và/hoặc có mục "Ngôn ngữ hiển thị" (i18n). Xem `testcase_writing_rules.md` RULE 10 & 11. **Không trộn** code phân quyền vào spec feature (spec feature login cố định 1 role).

#### 5B.1 — Phân quyền: sinh `output/tests/_common/permission.spec.ts`

1. **Fixture `loginAs(persona)`** — login theo persona, cache `storageState` để không login lại nhiều lần:
   - Đặt trong `src/fixtures/` (vd `auth.fixture.ts`), cùng convention với `base.fixture.ts` đang có.
   - Lấy account qua `account(persona)` và portal qua helper config (mỗi persona thuộc 1 portal) — **không hardcode** username/password/URL.
   - Cache file `.auth/<persona>.json`; có sẵn thì tái dùng, chưa có thì login (qua `LoginPage`) rồi `context.storageState({ path })`.
   - Thêm `.auth/` vào `.gitignore` (chứa session, không commit).
2. **Sinh test từ TC-PERM** — mỗi TC-PERM = 1 `test()`:
   - **Phía deny — biểu hiện đúng theo TC** (RULE 10.4):
     - menu/route ẩn → `await expect(page.locator(menuItem)).toHaveCount(0)`
     - redirect/403 → goto URL trực tiếp → assert URL bị đẩy về login/home, hoặc thấy trang 403
     - nút ẩn/disabled → `toBeHidden()` / `toBeDisabled()`
     - API 403 → bắt response, assert `status() === 403` + UI hiển thị thông báo không có quyền
   - **Cross-portal** (3 domain riêng): deny = account không đăng nhập được portal kia → test thử login portal đích bằng creds persona → assert login thất bại / không vào được.
   - **KHÔNG sinh phía allow** — happy path ở spec feature đã chứng minh role được phép (RULE 10.2).
3. TC-PERM thiếu persona trong config → skip đúng TC đó, ghi report (đã quyết ở Bước 1).

#### 5B.2 — Đa ngôn ngữ: assert qua `t()`, không hardcode chuỗi

1. **Module i18n** `src/i18n/` với:
   - `dict: Record<string, { vi: string; en?: string }>` — key `<màn>.<loại>.<tên>`; `vi` lấy **nguyên văn** từ cột "Kết quả mong muốn" của TC; `en` để trống, điền khi cần chạy EN.
   - `t(key)` resolve theo `process.env.LOCALE` (mặc định `vi`), fallback `vi` nếu thiếu `en`.
   - `assertLocalizedUI(page)` — bắt lỗi lòi key thô / placeholder dịch dở `{{...}}`; gọi cuối mỗi test (RULE 11.2).
2. **Assertion trong spec feature dùng `t()`** thay vì literal — đây là điều kiện để sau này chạy EN mà **không sửa code**:
   ```ts
   // ❌ await expect(toast).toHaveText('Email đã tồn tại');
   // ✅
   await expect(toast).toHaveText(t('create.error.emailExists'));
   ```
   - Vẫn thỏa "exact text" (`test_execution_rules.md` mục 1): `t('...')` trả đúng nguyên văn tiếng Việt.
   - Cuối mỗi test: `await assertLocalizedUI(page)`.
3. **Cấu hình chạy lại theo ngôn ngữ** (run dimension, không phải bộ test mới):
   - `playwright.config.ts`: set browser `locale` theo `process.env.LOCALE` (`vi-VN` / `en-US`).
   - `package.json`: thêm script `"test:en": "LOCALE=en playwright test"`. Round mặc định (`npm test`) = tiếng Việt.
   - **EN chỉ chạy khi user yêu cầu** — không thêm EN vào suite mặc định (tránh nhân đôi thời gian khi chưa cần).

### Bước 5.5 — Static Verify (BẮT BUỘC trước khi bàn giao)

Sau khi sinh script xong, thực hiện checklist dưới đây. Phát hiện lỗi nào → tự sửa ngay rồi mới tiếp. Output report cho user.

**A. Filesystem**
- Mọi file path trong script: kiểm tra `os.path.exists()` từng cái — KHÔNG assume tên file theo convention
- Tên file phải lấy từ `ls` thực tế, không đặt tên suy diễn (`thumb_over_2mb.jpg` khi chưa biết tên thật)
- Import paths resolve được trong project structure

**B. Page state trace**
- Trace tuần tự từng test trong class theo thứ tự chạy: *"test N kết thúc ở URL/trang nào? test N+1 assume đang ở đâu?"*
- Test nào có side effect navigate (submit, approve, breadcrumb, redirect) → test ngay sau **phải** tự navigate lại về đúng trang, không phụ thuộc state từ test trước

**C. API endpoint**
- Endpoint trong test khớp với endpoint đã verify trong codebase (api_helper, config)
- Không nhầm `BASE_URL` (portal UI) với API server URL

**D. Assertion completeness — đối chiếu với Expected Results (BẮT BUỘC)**
- Với **mỗi TC**, mở file testcase gốc, đọc **toàn bộ** cột "Kết quả mong muốn", đếm số điểm expected.
- Đếm số assertion trong script → phải tương ứng 1-1 với từng điểm expected (trừ điểm không thể verify kỹ thuật như DB nội bộ, gửi email thật).
- **Lỗi phổ biến:** chỉ check `resp.status() === 200` trong khi expected còn ghi "Chuyển trạng thái sang X trên danh sách" → phải navigate về list và verify status.
- Không dùng `count > 0` để verify kết quả thao tác trên item cụ thể — phải verify đúng item đó (tìm lại theo title/ID sau khi thao tác)
- Test không phụ thuộc data có sẵn trong hệ thống — phải tự tạo qua API helper

**E. Server constraint**
- Kiểm tra payload API tạo test data có field nào server có thể reject (thumbnail bắt buộc, ngày đăng không được quá khứ...)
- Nếu chưa biết constraint → đánh ⚠️ và hỏi user trước khi chạy

**F. Cross-cutting (chỉ khi có TC-PERM / i18n)**
- TC-PERM nằm ở `output/tests/_common/permission.spec.ts`, KHÔNG lẫn trong spec feature; mỗi TC-PERM có persona hợp lệ từ config (hoặc đã ghi skip vì thiếu persona)
- Không sinh phía allow trong permission spec; biểu hiện deny khớp TC
- Spec feature assert qua `t()` (không literal hardcode); mỗi test gọi `assertLocalizedUI(page)`
- `dict` i18n có đủ key dùng trong test; `vi` khớp nguyên văn cột Expected
- `playwright.config.ts` set `locale` theo `LOCALE`; `package.json` có script `test:en`

**Format output bắt buộc:**
```
## Static Verify Report — <tên file test>
✅ File paths: N/N tồn tại
✅ Page state trace: không có test nào bị orphan
✅ API endpoints: khớp api_helper
✅ Assertion completeness: N TC kiểm tra — tất cả expected đã có assertion tương ứng
⚠️ Server constraint: <mô tả field có thể reject> — cần xác nhận
❌ Assertion completeness: <TC_ID> expected "<điểm bị thiếu>" nhưng chưa có assertion → đã thêm
```
Chỉ coi bước này hoàn thành khi **không còn ❌**.

### Bước 6 — Ghi Handoff vào task.md và Bàn giao

Sau khi static verify sạch, cập nhật `task.md` với thông tin handoff để workflow `/run-and-heal` đọc:

```markdown
## Handoff — Run & Heal
- **Tech stack:** Playwright TypeScript
- **Lệnh chạy:** `npx playwright test output/tests/ --headed`
- **File test sinh ra:**
  - `output/tests/TC01_login.spec.ts`
  - `output/tests/TC02_upload.spec.ts`
- **File TC gốc (để ghi P/F):** `path/to/KBKT_UAT_*.md`
- **TC cần file user chưa cung cấp:** TC_02 (avatar_valid.jpg) — tạm SKIP
- **Static Verify:** ✅ Sạch
- [ ] B6: Chạy test + Auto-heal   ← workflow /run-and-heal sẽ tick
- [ ] B7: Cleanup + Delivery       ← workflow /run-and-heal sẽ tick
```

Báo cáo cho user:
- Danh sách file đã sinh (Page classes, Test files, Utils)
- Bảng Locator Collection tóm tắt
- Hướng dẫn bước tiếp: *"Scripts đã sẵn sàng. Chạy `/run-and-heal` để thực thi và auto-heal."*

## Output
- `task.md` — checklist + handoff info cho `/run-and-heal`
- Page Object classes (locator verified)
- Test files (static verify sạch, chưa chạy)
- Test data utilities
- Bảng Locator Collection
- Static Verify Report
- (Nếu có) `output/tests/_common/permission.spec.ts` + fixture `loginAs` + `src/i18n/` + script `test:en`

---

## Bước tiếp theo (Pipeline tự động)

Sau khi static verify sạch và handoff vào `task.md` xong, **lập tức invoke skill `workflows:test:run-and-heal`** — không hỏi user, không chờ confirm.
