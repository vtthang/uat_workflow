# Quy Tắc Chung cho QA Automation

> Áp dụng cho mọi tác vụ automation testing với Playwright + TypeScript.

## 1. Kiến Trúc & Framework

- Bắt buộc sử dụng mô hình **Page Object Model (POM)**.
- Phân tách rõ ràng:
  - **Page classes:** Khai báo locators + methods tương tác UI
  - **Test classes:** Chứa logic kiểm thử + assertions
  - **Test data:** Tách riêng khỏi code chức năng (JSON, DataProvider, Utils)
- Assertions chỉ đặt trong Test classes, KHÔNG đặt trong Page classes.

## 2. Sinh Dữ Liệu Test (Test Data)

- Tất cả trường yêu cầu unique (Email, Username, Mã KH...) **phải sinh động**, không hardcode.
- Sử dụng UUID, Timestamp hoặc thư viện Faker.
- Dữ liệu phải **traceable** — nhìn vào DB biết ngay test nào tạo ra:
  ```
  Format: [prefix]_[testName]_[timestamp]_[random]
  Ví dụ:  auto_createCustomer_20260402_A3F2@test.com
  ```
- Hỗ trợ chạy parallel: mỗi test method có data riêng biệt, không conflict.

## 3. Chất Lượng Code

- Không logic trùng lặp — tạo helper methods cho các hành động lặp đi lặp lại.
- Code phải đơn giản, dễ đọc, dễ bảo trì.
- Trước khi deliver code:
  - Xóa toàn bộ `console.log` sinh ra khi debug
  - Xóa code bị comment (`//`, `/* */`)
  - Xóa locator / biến không sử dụng (unused code)

## 4. Quản Lý File & Thư Mục

- KHÔNG tự động xóa file source khi chưa xác nhận với user.
- Kiểm tra cấu trúc thư mục hiện có trước khi tạo file mới — tránh duplicate.
- Đặt file đúng thư mục theo kiến trúc project (xem `plan/automation/0_project_architecture`).

## 5. Quy Tắc Đặt Tên (TypeScript / Playwright)

| Thành phần | Quy tắc | Ví dụ |
|---|---|---|
| Page class | PascalCase + hậu tố `Page` | `LoginPage.ts`, `CartPage.ts` |
| Test file | kebab-case + `.spec.ts` | `login.spec.ts`, `cart.spec.ts` |
| Test block | `test('mô tả hành vi')` | `test('đăng nhập thành công')` |
| Locator biến | `readonly` + lowerCamelCase | `readonly loginButton` |
| Utils | PascalCase hoặc kebab-case | `DataGenerator.ts`, `data-generator.ts` |

## 6. Assertions (Kiểm Tra Kết Quả)

- Mỗi test case **BẮT BUỘC** có ít nhất 1 assertion ở cuối.
- Nên có assertion xen kẽ ở các bước quan trọng.
- Assert phải mô tả rõ expected behavior:
  ```typescript
  await expect(page.getByText('Đăng nhập thành công')).toBeVisible();
  ```

## 7. Tính Độc Lập Của Test (Test Independence)

- Mỗi test case phải **độc lập** — không phụ thuộc kết quả test khác.
- Setup/teardown rõ ràng (`beforeEach/afterEach`).
- Không chia sẻ mutable state giữa các test methods.
- **Class scope cụ thể:** nếu dùng `scope="class"` / `@BeforeClass`, phải trace tuần tự từng test xem page đang ở đâu — một test có side effect navigate sẽ phá state của test sau. Xem `test_execution_rules.md` mục 7.
- **Không phụ thuộc data có sẵn trong hệ thống:** mỗi test tự tạo data cần thiết qua API trước khi thao tác — không assume "đã có bài Chờ duyệt trong danh sách". Data tồn tại trước có thể bị test khác consume, xoá, hoặc đổi state.

## 8. Verify trước khi deliver (Static Verify)

Trước khi chạy test lần đầu, kiểm tra tĩnh (không cần browser):

- **File path**: `os.path.exists()` từng file fixture — KHÔNG đặt tên theo convention mà chưa ls thư mục thực tế.
- **Page state trace**: với mỗi class dùng shared page, liệt kê "test N → kết thúc ở đâu → test N+1 bắt đầu ở đâu" — đảm bảo không có orphaned test.
- **Assertion strength**: assertion sau thao tác phải verify đúng item vừa thao tác, không verify "có bất kỳ item nào" (xem `test_execution_rules.md` mục 8).
- **SPA state**: Page class phải có cơ chế clear filter/state sau navigate (xem `test_execution_rules.md` mục 9).

Xem checklist đầy đủ trong `generate-automation-from-testcases.md` Bước 5.5.

## 10. Verification Depth — Bắt buộc cho màn hình danh sách

> Khi sinh test cho TC loại "Xem danh sách / Tìm kiếm / Lọc / Sắp xếp", **BẮT BUỘC** tuân theo 5 quy tắc sau. Không được dừng ở mức `toBeVisible()` trên container.

| TC loại | Quy tắc bắt buộc | Rule chi tiết |
|---|---|---|
| Xem danh sách | Verify tên từng column header + fields của row đầu | `test_execution_rules.md` Rule 14a, 14b |
| Tìm kiếm | Keyword từ data thực, verify TỪNG row chứa keyword | `test_execution_rules.md` Rule 14c |
| Lọc / Filter | Verify TẤT CẢ rows khớp criterion (tối đa 15) | `test_execution_rules.md` Rule 14d |
| Sort | Capture values trước/sau, compare từng cặp liền kề | `test_execution_rules.md` Rule 14e |
| Bất kỳ list screen | Intercept GET API, verify HTTP 200, compare row 1 với API data | `test_execution_rules.md` Rule 12e |

**Screenshot timing:** Luôn đợi `networkidle` + skeleton biến mất trước khi chụp. `BasePage.screenshot()` đã tích hợp sẵn — không gọi `page.screenshot()` trực tiếp trong test. Xem `test_execution_rules.md` Rule 5.

**Screenshot signature (2 params):**
```typescript
// BasePage.screenshot(tcId, stepLabel)
// tcId theo format TC-{FUNC}-{NN} (xem html_report_rules.md mục 1)
await basePage.screenshot('TC-LIST-01', '01_list_loaded');
// → output/evidence/uat/admin/<module>/<function>/[TC-LIST-01][01_list_loaded].png

await basePage.screenshot('TC-CREATE-01', '03_after_submit');
// → [TC-CREATE-01][03_after_submit].png
```

**tcId:** format `TC-{FUNC}-{NN}` — FUNC xác định theo chức năng (LIST, CREATE, DETAIL, TOGGLE, UPDATE, HISTORY, RESET...), NN bắt đầu từ 01.  
**stepLabel:** mô tả bước ngắn gọn, VD: `'01_list_loaded'`, `'02_form_filled'`, `'03_after_submit'`. Tham số thứ 3 tùy chọn là `focusLocator` (scroll element vào view trước khi chụp).

## 9. Chia sẻ state giữa các test run bằng fixture file

Khi cần pass dữ liệu từ **setup run** sang **test run** (vd: IDs của pre-created articles):

- Setup spec ghi ra `output/test-results/<feature>-fixture.json`
- Test spec đọc file đó vào đầu mỗi test
- File nằm trong `output/test-results/` (gitignore, không commit)

```typescript
// setup spec
fs.writeFileSync('output/test-results/fixture.json', JSON.stringify(data, null, 2));

// test spec
function loadFixture() {
  if (!fs.existsSync('output/test-results/fixture.json'))
    throw new Error('Chạy setup spec trước!');
  return JSON.parse(fs.readFileSync('output/test-results/fixture.json', 'utf-8'));
}
```

---

## 11. Test Data — Không dùng ký tự đặc biệt trong tên người dùng (fullName)

**Rule:** Hệ thống TPcoms UAT validate `fullName` chỉ chấp nhận chữ cái, chữ số và khoảng trắng. **TUYỆT ĐỐI KHÔNG dùng `_` (underscore), `@`, `#`, `$`, `%`, `-` trong fullName test data.**

**Lý do:** Form validation sẽ reject ngay với message "Chỉ chấp nhận chữ cái, chữ số và khoảng trắng. Không nhập các ký tự lạ (@, #, $, %, ...)" — test sẽ fail ở bước điền form chứ không phải ở bước test thực sự.

```typescript
// SAI — chứa underscore → bị reject ngay ở validation
const name = `AutoTest_CREATE01_${s}`;
const name = `AutoTest-UPDATED-${s}`;

// ĐÚNG — chỉ dùng chữ cái, số, khoảng trắng
const name = `AutoCreate01 ${s}`;
const name = `AutoUpdated ${s}`;
```

**Áp dụng toàn bộ hệ thống:** Mọi field "Họ và tên", "Tên hiển thị", "Tên tài khoản" dạng người dùng — dùng pattern `<PrefixCamelCase> ${suffix}`.

---

## 12. API Monitoring — Setup, type, và reset

### Xác định isMainApi — phân biệt main API vs background calls

Main API = action chính của feature. Phân biệt bằng **URL + HTTP method** — không dùng URL đơn thuần.

| Feature type | Method | Pattern ví dụ |
|---|---|---|
| Tạo mới | `POST` | `/admin-members`, `/posts` |
| Cập nhật | `PUT` / `PATCH` | `/admin-members/{id}` |
| Xóa / Action | `DELETE` / `POST` / `PATCH` | `/admin-members/{id}/activate` |
| Xem danh sách / tìm kiếm | `GET` | `/admin-members?page=...` |
| Xem chi tiết | `GET` | `/admin-members/{id}` |

```typescript
// ✅ Write feature: lọc theo URL + method write
const MAIN_API_URL = /\/admin-members\b/;
const isMainApi = (res: Response) =>
  MAIN_API_URL.test(res.url()) && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(res.request().method());

// ✅ Read feature: lọc GET
const isMainApi = (res: Response) =>
  /\/admin-members/.test(res.url()) && res.request().method() === 'GET';

// Chưa biết URL → dùng tạm để discover:
const isMainApi = () => true;  // capture all, xem _api-calls.json → thu hẹp pattern
```

### Type bắt buộc cho apiLog

```typescript
interface ApiLogEntry {
  method: string;
  url: string;
  status: number;
  time: number;
  responseBody?: any;  // chỉ populate khi isMainApi(res) === true
}
const apiLog: ApiLogEntry[] = [];

// Setup listener trong beforeEach (async vì cần await res.json())
page.on('response', async res => {
  if (/\.(js|css|png|jpg|ico|woff|svg)$/i.test(res.url())) return;
  const entry: ApiLogEntry = {
    method: res.request().method(),
    url: res.url(),
    status: res.status(),
    time: Date.now(),
  };
  if (isMainApi(res)) {
    entry.responseBody = await res.json().catch(() => null);  // full response body
  }
  apiLog.push(entry);
});
```

### afterEach — dùng `teardownApiMonitor` (KHÔNG tự viết inline)

```typescript
import { setupApiMonitor, teardownApiMonitor } from '../../src/utils/ApiMonitor';

test.afterEach(async ({}, testInfo) => {
  await teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR);
  // Tự động:
  //   - Ghi 1 file: <EVIDENCE_DIR>/TC-LIST-01_api-calls.json (mọi calls; main API entry có responseBody)
  //   - Nếu FAIL: attach api-calls.txt vào Playwright report
  //   - Reset apiLog.length = 0
});
```

`teardownApiMonitor` extract TC ID bằng regex `/TC-[A-Z]+-\d+/i` từ `testInfo.title` → dùng làm prefix tên file. TC ID phải nằm ở đầu test title (VD: `'TC-LIST-01 Xem danh sach'`).

### Reset apiLog trước action chính

**Rule:** Đặt `apiLog.length = 0` **ngay trước** khi click action button (submit/save/confirm), KHÔNG đặt trong `beforeEach`.

**Lý do:** Listener `page.on('response', ...)` được setup sớm (trong `beforeEach` hoặc đầu test) để bắt mọi call. Nếu `goto()` hoặc các bước setup cũng trigger API thì apiLog sẽ đã có entries trước khi action chính — dẫn đến assert "tối đa 1 POST call" bị fail vì đếm nhầm cả navigation calls.

```typescript
// Pattern chuẩn
page.on('response', res => { /* setup sớm nhất có thể */ });

await createPage.goto();         // có thể trigger GET calls → apiLog += entries
await createPage.fillForm(...);  // không trigger API

apiLog.length = 0;               // ← reset ngay trước action chính
await createPage.submit();       // ← chỉ đếm POST từ đây

const postCalls = apiLog.filter(c => c.method === 'POST');
expect(postCalls.length).toBeLessThanOrEqual(1);  // ← chính xác
```

---

## 13. Toast timing — Dùng Promise.race thay vì trực tiếp check toast

**Rule:** Toast notification thường biến mất trong 2-3 giây sau khi hiện. Khi action thành công kèm navigation (redirect về `/list`), **KHÔNG dùng `toBeVisible()` trực tiếp trên toast** — toast đã biến mất trước khi assertion chạy.

```typescript
// SAI — race condition: page đã redirect về /users, toast không còn
await expect(page.getByText(/thành công/i)).toBeVisible({ timeout: 5_000 });

// ĐÚNG — race giữa URL change và toast visibility
await Promise.race([
  page.waitForURL(/\/users/, { timeout: 30_000 }),
  page.getByText(/thành công/i).waitFor({ timeout: 30_000 }),
]);
// Sau đó assert URL (ổn định hơn toast)
await expect(page).toHaveURL(/\/users/, { timeout: 10_000 });
```

**Hoặc nếu Page class có `waitForSuccessToast()`:**
```typescript
await editPage.waitForSuccessToast();  // đã implement Promise.race bên trong
await expect(page).toHaveURL(/\/users$/, { timeout: 15_000 });
```

**Nguyên tắc chung:** Sau action thành công, assert navigation URL (bền vững) thay vì assert toast text (thoáng qua). Toast là bonus evidence, URL là assertion chính.

---

## 14. Tạo mới → Verify bằng search, không dùng first-row assertion

**Rule:** Sau khi tạo mới một bản ghi, **search theo tên/email vừa tạo để verify**, KHÔNG assert `tableRows.first()` chứa tên vừa tạo.

**Lý do:** Tests chạy parallel có thể tạo bản ghi khác đồng thời → bản ghi mới nhất không nhất thiết là row đầu tiên trong danh sách.

```typescript
// SAI — có thể fail nếu test khác tạo bản ghi mới cùng lúc
await expect(listPage.tableRows.first()).toContainText(`AutoCreate01 ${s}`);

// ĐÚNG — search để tìm chính xác bản ghi vừa tạo
await listPage.search(`AutoCreate01 ${s}`);
await page.waitForTimeout(800);
await expect(listPage.tableRows.first()).toContainText(`AutoCreate01 ${s}`, { timeout: 10_000 });
```

**Áp dụng cho:** Mọi TC loại "tạo mới" sau khi redirect về danh sách.

---

## 15. Email duplicate validation — Blur để trigger server-side check

**Rule:** Trong form tạo/sửa user, validation email trùng là **server-side real-time check** (fire on `blur`), KHÔNG phải validation on-submit. Để test TC này:

```typescript
// Nhập email trùng → blur → chờ 1-1.5s → assert inline error
await editPage.inputEmail.clear();
await editPage.inputEmail.fill(existingEmail);
await editPage.inputEmail.blur();       // trigger server validation
await page.waitForTimeout(1500);        // đợi API response
// Inline error xuất hiện ngay, trước khi submit
const emailError = page.locator('p:near(input[name="email"]), span:near(input[name="email"])').first();
await expect(emailError).toBeVisible({ timeout: 8_000 });
await expect(emailError).toContainText(/tồn tại|đã có/i);
// Không cần click submit hoặc confirm popup
```

**Không click submit** sau khi nhập email trùng — server validation đã block form ngay tại field level.