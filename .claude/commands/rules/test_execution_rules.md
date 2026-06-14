# Quy Tắc Thực Thi Test (Test Execution Rules)

> Các nguyên tắc bắt buộc khi sinh & chạy automation, rút ra từ lỗi thực tế hay gặp. Áp dụng cho mọi web automation (ưu tiên Playwright).

## 0. Implement ĐẦY ĐỦ tất cả Expected Results (QUAN TRỌNG NHẤT)

**Lỗi hay gặp:** chỉ implement 1 trong nhiều điểm trong cột "Kết quả mong muốn" — thường chỉ check API status hoặc UI phản hồi đầu tiên, bỏ sót các điểm còn lại.

- Đọc **toàn bộ** cột "Kết quả mong muốn" của từng TC trước khi viết code.
- **Mỗi điểm** trong expected phải có assertion tương ứng trong test, trừ khi không thể kiểm tra kỹ thuật (DB nội bộ, gửi email thật).
- Ví dụ: TC expected ghi "Chuyển trạng thái sang Đã từ chối" → phải verify trạng thái trên UI danh sách, KHÔNG chỉ check `resp.status() === 200`.
- Nếu expected có nhiều điểm → tên test phải phản ánh đầy đủ, không viết tên chỉ cover 1 điểm.

```typescript
// SAI — chỉ check API, bỏ sót "trạng thái chuyển sang Đã từ chối" trên UI
expect(resp.status()).toBe(200);

// ĐÚNG — implement đầy đủ expected
expect(resp.status()).toBe(200);
await newsListPage.goto();
await newsListPage.searchByTitle(article.title);
expect(await newsListPage.getStatusForRow(article.title)).toMatch(/Đã từ chối/);
```

## 1. Error message / Toast — kiểm EXACT content

**Lỗi hay gặp:** dùng matcher substring nên message sai vẫn pass.

- Khi expected là một thông báo cụ thể (validation, toast, alert) → assert **exact text**, KHÔNG dùng substring mặc định.
- Playwright:
  ```typescript
  // ĐÚNG — exact
  await expect(page.getByRole('alert')).toHaveText('The Email Address field is required.');
  // hoặc
  await expect(page.getByText('Invalid email or password', { exact: true })).toBeVisible();

  // SAI — substring, "...required now" cũng pass
  await expect(page.getByText('field is required')).toBeVisible();
  ```
- Lấy expected text **nguyên văn từ test case** (cột Expected Result). Không tự diễn giải/rút gọn.
- Nếu message có phần động (tên, số) → tách phần tĩnh assert exact, phần động dùng regex có kiểm soát.
- Element message thường ẩn theo điều kiện → verify ở đúng state (`verifiedStates: after-invalid-login`), xem `locator_repository.md`.

## 1a. Submit thành công → phải fill đủ field bắt buộc (dù TC không ghi)

**Lỗi hay gặp:** TC viết ngắn gọn "Click [Duyệt] → popup thành công" mà không liệt kê "điền thumbnail", "điền tóm tắt"... → script không setup đủ field → action fail với 400/validation error.

**Nguyên tắc:** Khi Expected Result là **thành công**, dù TC không ghi chi tiết từng field, phải **tự suy ra** toàn bộ field bắt buộc trên màn hình đó và đảm bảo chúng có giá trị hợp lệ trước khi thực hiện action.

**Cách xác định field bắt buộc:** Nhìn UI — field có dấu `*`, hoặc thử submit rỗng xem validation báo field nào.

**Ví dụ:**
```
TC: "Click [Duyệt] → hiển thị popup thành công"
→ Phải hiểu: thumbnail (*), title (*), slug (*), author (*), summary (*), content (*) đều phải hợp lệ
→ Không thể chỉ navigate đến trang rồi click Duyệt ngay
```

**Áp dụng vào script:**
- Tạo test data qua API với đầy đủ field bắt buộc
- Với field không thể set qua API (e.g. thumbnail URL không load) → upload trực tiếp qua UI trong test setup
- Dùng `waitUntilReadyToApprove()` (no errors + button enabled) để xác nhận form đã đủ điều kiện

## 1b. Phân loại case trước khi viết code — Submit vs Validate

**Đọc cột Expected Result để xác định loại case TRƯỚC KHI code:**

| Expected Result chứa | Loại case | Wait strategy |
|---|---|---|
| "thành công", "trạng thái chuyển sang", "popup thành công", "navigate về", "Đã lên lịch", "Đã xuất bản" | **Submit thành công** | Đợi `no errors + button enabled` trước khi click |
| "hiển thị lỗi", "inline message", "Vui lòng...", "không cho phép", "cảnh báo", error message cụ thể | **Validate** | Click thẳng — mục tiêu là trigger lỗi |

**Submit case** — form phải sạch trước khi submit:
```typescript
// Không có error message nào visible + button enabled
await expect(page.locator('[class*="error"]:visible, [class*="invalid"]:visible')).toHaveCount(0);
await expect(submitButton).toBeEnabled({ timeout: 60_000 });
await submitButton.click();
```
Cách này tự động cover prerequisite APIs (slug validation, file upload...) mà không cần biết URL cụ thể.

**Validate case** — KHÔNG đợi button enabled:
```typescript
await submitButton.click();  // click dù form chưa valid
await expect(page.locator('text=Vui lòng thêm ảnh thumbnail')).toBeVisible();
```

## 2. Test validation 1 field → các field khác PHẢI hợp lệ

**Lỗi hay gặp:** test "email sai" mà để password trống → form fail vì password → false positive, không cô lập đúng field.

- Khi test ràng buộc của MỘT field, mọi field còn lại điền **giá trị hợp lệ** để cô lập đúng field đang test.
- Ví dụ test "email thiếu @": email = `invalidemail` (sai), password = `123456` (**hợp lệ**) → chắc chắn lỗi đến từ email.
- Ngoại lệ: case cố tình test "nhiều field cùng sai" (vd để trống cả 2) — khi đó theo đúng test case.
- Lấy giá trị hợp lệ cho field khác từ `test-data-generator` (positive data).

## 2b. TC "Giá trị mặc định" trên màn chỉnh sửa / duyệt / chi tiết

**Lỗi hay gặp:** dùng `toBeTruthy()` — chỉ check "field không trống", không verify đúng giá trị.

**Nguyên tắc:** tạo item qua API (lưu lại values), navigate vào màn, so sánh `toBe(article.field)`.

```typescript
test.describe('...', () => {
  let article: ArticleData;           // lưu ở describe scope để test truy cập được

  test.beforeEach(async ({ articleApi, listPage, editPage }) => {
    article = await articleApi.createLuuNhap('GBV_S34');  // helper phải trả về đủ fields
    await listPage.navigateToEdit(article.title);
  });

  test('GBV_S34 - Tiêu đề hiển thị đúng giá trị đã lưu', async ({ editPage }) => {
    expect(await editPage.fieldTieuDe.inputValue()).toBe(article.title);      // ✅
    // SAI: expect(value.trim()).toBeTruthy()  ← không biết value có đúng hay không
  });
});
```

**Trường hợp đặc biệt — không thể verify exact:**
- **Datetime**: verify format `DD/MM/YYYY` + khoảng hợp lý (tương lai/quá khứ) thay vì exact timestamp.
- **Dropdown** (chỉ biết ID): `toBeTruthy()` chấp nhận được.
- **Rich text editor**: strip HTML → compare plain text: `toContain(article.content.replace(/<[^>]+>/g, ''))`.
- **Section sau toggle** (sendNotification, actionButton): phải tạo item với toggle ON và có data — nếu tạo item với toggle OFF rồi `enableToggle()` thì field rỗng, không có gì verify. Dùng helper riêng (vd `createWithToggles()`).

**API helper phải trả về đủ fields** để test dùng `toBe()`:
```typescript
return { id, title, slug, authorName, summary, content };  // ✅
// KHÔNG return { id, title } rồi bắt test dùng toBeTruthy()  ❌
```

**Trước khi viết API helper — TỰ lấy payload thật bằng cách tạo 1 bản ghi qua UI và bắt request** (môi trường UAT không cung cấp curl). Không suy đoán field name từ UI label hay TypeScript interface — tên field UI ≠ tên field API.

```typescript
// Bootstrap: tạo 1 item qua UI thật → bắt request → lấy URL/method/headers/body thật
const [req] = await Promise.all([
  page.waitForRequest(r => r.url().includes('/api/') && r.request().method() === 'POST'),
  createPage.submitWithAllFields(),   // điền đủ field hợp lệ rồi submit
]);
const url = req.url();
const auth = req.headers()['authorization'];   // token từ session
const body = JSON.parse(req.postData() || '{}'); // payload THẬT → map 1-1 vào helper

// SAI — đoán từ UI placeholder "Tên thông báo" → notificationTitle
// ĐÚNG — lấy từ body thật → notificationName, notificationPurpose, notificationPayload
```

Sau đó dựng `_create_<entity>_via_api()` từ payload thật, lưu shape vào `src/fixtures/<feature>-fixture.json` để tái dùng. Lần đầu chậm (qua UI) nhưng tự lấy được API, không phụ thuộc user.

## 3. Case gọi API — quan sát request & response

**Cần:** biết API nào được gọi, request gửi gì, response trả gì — ngay trong UI test.

- Dùng Playwright network interception (KHÔNG nhầm với REST Assured — đó là test API riêng):
  ```typescript
  // Chờ & bắt response của API cụ thể
  const respPromise = page.waitForResponse(r => r.url().includes('/admin/authentication') && r.request().method() === 'POST');
  await loginPage.clickLogin();
  const resp = await respPromise;
  expect(resp.status()).toBe(200);
  const body = await resp.json();          // đọc response body
  const reqData = resp.request().postData(); // đọc request đã gửi
  ```
- Assert được: URL, method, status code, request payload, response body.
- Ghi vào output/evidence/log: API gọi gì, request, response (xem mục 5) — phục vụ truy vết khi fail.

## 4. Case TRIM — bắt REQUEST để xác minh (KHÔNG đoán qua UI)

**Khẳng định kỹ thuật: Playwright LÀM ĐƯỢC.** Trim phải kiểm bằng cách đọc payload thật gửi lên server, không nhìn UI.

- Nhập giá trị có khoảng trắng đầu/cuối → submit → **bắt request → đọc body → assert giá trị đã/chưa trim**:
  ```typescript
  const reqPromise = page.waitForRequest(r => r.url().includes('/api/customer') && r.method() === 'POST');
  await form.fillName('   John Doe   ');   // có space đầu/cuối
  await form.submit();
  const req = await reqPromise;
  const sent = JSON.parse(req.postData() || '{}');
  // Nếu yêu cầu hệ thống TRIM:
  expect(sent.name).toBe('John Doe');       // đã trim
  // Nếu yêu cầu GIỮ NGUYÊN:
  // expect(sent.name).toBe('   John Doe   ');
  ```
- KHÔNG kết luận trim chỉ bằng nhìn giá trị hiển thị trên UI — UI có thể che giấu hành vi backend.
- Áp dụng cho mọi field text mà test case yêu cầu kiểm trim.

## 5. Evidence — chụp NHIỀU ảnh theo bước quan trọng (mọi case)

**Cần:** evidence cho TẤT CẢ case (cả pass), nhiều ảnh theo bước.

**Bắt buộc kể cả khi chạy headed (browser hiển thị).** Headed mode không miễn evidence — ảnh là bằng chứng bất biến, browser window đóng lại thì không còn gì để truy vết.

**Đợi page ổn định TRƯỚC khi chụp** — không được chụp khi còn skeleton/loading:
```typescript
// Đợi network settle + loading spinner biến mất
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
await page.locator('[class*="loading"], [class*="skeleton"], [aria-busy="true"]')
  .waitFor({ state: 'hidden', timeout: 5_000 }).catch(() => {});
// BasePage.screenshot() đã tích hợp sẵn — gọi trực tiếp là đủ
await basePage.screenshot(tcId, stepLabel);
```

Lý do: ảnh chụp khi loading sẽ capture trạng thái trống/skeleton, không thể dùng làm evidence hợp lệ.

**Scroll đến element trước khi chụp** để element hiển thị rõ ràng trong ảnh, không bị cắt:
```typescript
await targetLocator.scrollIntoViewIfNeeded();
await page.screenshot({ path: `output/evidence/${tcId}/03_error_shown.png`, fullPage: true });
```

- Chụp screenshot ở các mốc quan trọng của mỗi case: sau khi điền form, sau khi submit/action chính, tại điểm assert kết quả. Thêm ảnh ngay khi assertion fail.
- Quy ước lưu — dùng `BasePage.screenshot(tcId, stepLabel)` **(2 tham số)**:
  ```
  output/evidence/<evidenceFeatureDir>/[TC-ID][stepLabel].png
  Ví dụ: [TC-LIST-01][01_list_loaded].png
         [TC-CREATE-01][02_form_filled].png
         [TC-CREATE-01][03_after_submit].png
  ```
  - **tcId** theo format `TC-{FUNC}-{NN}` (xem `html_report_rules.md` mục 1)
- **KHÔNG thêm timestamp**, **KHÔNG thêm suffix random** vào tên file.
- Chạy lại test → file tự **overwrite** (cùng path = cùng file), không tạo file trùng.
- `stepLabel`: mô tả bước ngắn gọn, tiếng Anh hoặc tiếng Việt không dấu, dùng `_` thay space.
  VD: `'01_form_loaded'`, `'02_form_filled'`, `'03_toast_success'`.
- Tất cả screenshot của một module/function nằm **cùng thư mục** (`evidenceFeatureDir`), phân biệt nhau qua tên file.
- **Chụp ở 100% zoom, capture đầy đủ scroll** — `BasePage.screenshot()` tự động resize viewport theo `scrollHeight` thực tế của page (kể cả inner scroll container) trước khi chụp, sau đó restore lại. Mục đích: ảnh rõ nét 100%, không cắt nội dung dưới fold (pagination, total count, footer). **KHÔNG** gọi `page.screenshot()` trực tiếp — mất resize logic. **KHÔNG** dùng `style.zoom` — làm mờ ảnh.
- Bật trace cho case fail để debug sâu: `--trace on-first-retry` (hoặc `retain-on-failure`).
- KHÔNG chụp tràn lan ngoài các mốc quan trọng (giữ evidence gọn, có ý nghĩa).

## 6. Đánh P/F vào file testcase gốc — KHÔNG đổi data khác (Excel)

**Cần:** ghi kết quả Pass/Fail thẳng vào file `.xlsx` gốc, thêm cột kết quả, tuyệt đối không sửa nội dung TC.

**Nguyên tắc bảo toàn (CRITICAL):**
- Mở file gốc bằng `openpyxl` (`load_workbook`), **chỉ ghi vào cột kết quả**, save lại đúng file. KHÔNG đọc-rồi-ghi-lại bằng pandas (pandas làm mất format, merged cell, formula).
- KHÔNG sửa bất kỳ cell nào ngoài cột kết quả (và cột output/evidence/note nếu có). KHÔNG đổi thứ tự dòng, không xoá, không reformat.
- Nếu file CHƯA có cột kết quả → thêm cột mới ở cuối (vd "Result", "Evidence", "Run Date"). Nếu ĐÃ có → ghi vào đúng cột đó theo TC ID.
- Khớp dòng theo **TC ID** (không theo số thứ tự dòng — tránh ghi nhầm).

```python
from openpyxl import load_workbook
wb = load_workbook("TC_CRM_LOGIN.xlsx")   # giữ nguyên format gốc
ws = wb.active
# tìm cột "Result" (hoặc thêm mới ở cuối), tìm dòng theo TC ID, chỉ ghi cell đó
ws.cell(row=r, column=result_col).value = "PASS"   # hoặc "FAIL"
ws.cell(row=r, column=evidence_col).value = "output/evidence/TC_LOGIN_013/"
wb.save("TC_CRM_LOGIN.xlsx")
```

- Trước khi save: xác nhận chỉ có cột kết quả thay đổi. Báo cáo cuối nêu rõ: đã ghi P/F cho N dòng, không đụng data khác.
- An toàn: nếu không chắc cấu trúc file → hỏi user trước khi ghi (theo `CLAUDE.md` mục an toàn dữ liệu).

---

## 7. TC Time-sensitive — Chiến lược batch và đặt tên test data

**Khi TC cần "trạng thái thời gian"** (bài viết quá hạn, tài liệu hết hạn, lịch kích hoạt...):

**Chiến lược batch:**
1. Tạo data với thời gian = **now()** ngay đầu session (`scheduledPublishDate = new Date().toISOString()`)
2. Chạy các TC khác trước (~15-20 phút)
3. Khi quay lại, data đã quá hạn tự nhiên → chạy batch time-sensitive

**Đặt tên test data theo TC ID** (bắt buộc khi dùng precreated data):
```
"<TC_ID>_<mô_tả>_<timestamp>"
Ví dụ: "XTBV_46_tu_choi_1748500000000"
```
Lý do: Tìm kiếm được chính xác bản ghi của từng TC trên UI, tránh nhầm với data cũ.

**Lưu fixture giữa các run** bằng file JSON:
```typescript
// Setup spec ghi ra
fs.writeFileSync('output/test-results/fixture.json', JSON.stringify(articles));
// Batch sau đọc vào
const articles = JSON.parse(fs.readFileSync('output/test-results/fixture.json', 'utf-8'));
```

**Khi có nhiều datetime field ràng buộc nhau** → xem `datetime_rules.md` để biết cách phân tích ràng buộc chéo và chuẩn bị data đúng.

## 9. Class Scope — Trace page state qua từng test

**Lỗi hay gặp:** dùng `scope="class"` chia sẻ một page/session cho nhiều test. Test giữa chừng gọi submit / approve / navigate → page rời khỏi màn hình → test tiếp theo tưởng vẫn đang ở review screen → timeout hoặc assert sai.

- Trước khi viết bất kỳ test nào trong class scope, trace tuần tự: *"test N kết thúc ở trang nào? test N+1 cần bắt đầu ở đâu?"*
- Test có side effect navigate (approve, submit, go back...) → test ngay sau phải tự tạo bài mới qua API và navigate lại — không thể "tiếp tục từ chỗ test trước dừng".
- Pattern chuẩn: thêm helper `_goto_fresh_<screen>(tc_id)` gọi API tạo item mới + navigate vào đúng màn trước mỗi test cần clean state.
- Nếu class scope quá phức tạp để kiểm soát → đổi về `scope="function"` / `beforeEach` — đơn giản hơn là debug state leak.

## 8. Assertion phải verify đúng đối tượng vừa thao tác

**Lỗi hay gặp:** sau khi approve bài A, test chỉ kiểm tra "có bài nào đó trạng thái Đã xuất bản" → PASS dù bài A chưa đổi status (false positive vì hệ thống đã từng có bài xuất bản trước đó).

- Sau thao tác trên item X: lưu `title` / `id` của X **trước** khi thao tác, tìm lại đúng X sau đó, assert status của **chính X**.
- Search theo title vào ô tìm kiếm để tìm bài (không chỉ filter theo status rồi lấy row đầu tiên bất kỳ).
- `count > 0` chỉ hợp lệ khi test "danh sách có ít nhất 1 item" — không dùng để verify kết quả thao tác.

## 10. SPA State — Filter/UI state tồn tại qua navigate

**Lỗi hay gặp:** `page.goto(url)` reset URL nhưng React SPA restore filter state từ localStorage → danh sách vẫn hiển thị theo filter cũ ("Lưu nháp") → search không tìm thấy bài "Chờ duyệt".

- `page.goto()` ≠ "clean slate" với SPA — không assume state được reset.
- Page class phải có `clear_<filter>()` và gọi nó sau mỗi `navigate()`.
- `filter_by_status()` phải hoạt động được kể cả khi filter đang active với status khác — không dùng `filter(has_text="Trạng thái")` vì text thay đổi khi đang active.
- `click_approve_icon_by_title()` phải tự clear filter trước khi search, vì không thể assume filter đang ở trạng thái nào khi được gọi.

## 11. TC "Upload file hợp lệ" — mỗi định dạng là 1 sub-case riêng

TC ghi "upload hợp lệ (JPG/PNG)" → **tách thành 2 test** `_082a` (JPG) + `_082b` (PNG). Không gộp vào 1 test rồi chỉ chạy 1 loại.

Áp dụng cho cả thumbnail lẫn editor uploads. Đặt tên suffix chữ cái: `a`, `b`, `c`...

---

## 12. API Monitoring — Bắt buộc cho mọi test có action gọi API

**Yêu cầu:** Mọi test thực hiện action gọi API (submit form, tạo mới, sửa, xóa, tìm kiếm...) phải:
1. **Capture toàn bộ API call** trong suốt test để phát hiện duplicate
2. **Verify UI reflect đúng response API** — cả success lẫn error

### 12a. Xác định MAIN_API — phân biệt main API vs background calls

**Main API** là API thực hiện action chính của feature. Phân biệt bằng **URL endpoint + HTTP method** — không dùng URL regex đơn thuần vì cùng 1 endpoint có thể có nhiều method.

| Feature type | Method | Ví dụ URL pattern |
|---|---|---|
| Tạo mới | `POST` | `/admin-members`, `/posts` |
| Cập nhật | `PUT` / `PATCH` | `/admin-members/{id}`, `/posts/{id}` |
| Xóa | `DELETE` | `/admin-members/{id}` |
| Action (kích hoạt, reset...) | `POST` / `PATCH` | `/admin-members/{id}/activate`, `/reset-password` |
| Xem danh sách / tìm kiếm | `GET` | `/admin-members?page=...` |
| Xem chi tiết | `GET` | `/admin-members/{id}` |

**Pattern chuẩn — luôn kết hợp URL + method:**

```typescript
// ❌ Sai: URL alone bắt cả GET list lẫn POST create
const isMainApi = (res) => /\/admin-members/.test(res.url());

// ✅ Đúng: write action
const MAIN_API_URL = /\/admin-members\b/;
const MAIN_API_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];
const isMainApi = (res) =>
  MAIN_API_URL.test(res.url()) && MAIN_API_METHODS.includes(res.request().method());

// ✅ Đúng: read action (list / detail / search)
const isMainApi = (res) =>
  /\/admin-members/.test(res.url()) && res.request().method() === 'GET';
```

**Cách tìm URL nếu chưa biết:**
1. Đọc file `_api-calls.json` từ lần chạy trước → lọc theo method đúng → URL đó là main API
2. Nếu chưa có file — set `isMainApi = () => true` (capture all có body) → chạy 1 lần → xem log → thu hẹp pattern

### 12b. Setup API Monitor (đặt trong `beforeEach`)

```typescript
interface ApiLogEntry {
  method: string;
  url: string;
  status: number;
  time: number;
  responseBody?: any;  // chỉ có cho main API calls (isMainApi = true)
}
const apiLog: ApiLogEntry[] = [];

// Listener async — capture response body chỉ cho main API
page.on('response', async res => {
  if (/\.(js|css|png|jpg|ico|woff|svg)$/i.test(res.url())) return;
  const entry: ApiLogEntry = {
    method: res.request().method(),
    url: res.url(),
    status: res.status(),
    time: Date.now(),
  };
  if (isMainApi(res)) {  // isMainApi = URL + method filter định nghĩa ở trên
    entry.responseBody = await res.json().catch(() => null);
  }
  apiLog.push(entry);
});
```

**afterEach — KHÔNG tự viết, dùng `teardownApiMonitor` từ `ApiMonitor.ts`:**
```typescript
import { setupApiMonitor, teardownApiMonitor } from '../../src/utils/ApiMonitor';

test.afterEach(async ({}, testInfo) => {
  await teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR);
});
```

`teardownApiMonitor` tự động:
- Extract TC ID bằng regex `/TC-[A-Z]+-\d+/i` từ `testInfo.title` (format `TC-LIST-01`)
- Ghi **1 file duy nhất**: `<EVIDENCE_DIR>/<TC_ID>_api-calls.json` (ví dụ `TC_UU_001_api-calls.json`)
- KHÔNG dùng slug từ tên test — chỉ dùng ID
- KHÔNG tạo file `_main-api-response.json` riêng — main API entry đã có `responseBody` trong file chung
- Nếu FAIL: attach `api-calls.txt` vào Playwright report
```

### 12b. Kiểm tra Duplicate API Call (assert sau mỗi action chính)

```typescript
// Sau khi click submit / trigger action
function assertNoDuplicateApiCall(log: typeof apiLog, withinMs = 1000) {
  const seen = new Map<string, number>();
  const duplicates: string[] = [];
  for (const entry of log) {
    const key = `${entry.method}:${entry.url}`;
    const prev = seen.get(key);
    if (prev !== undefined && entry.time - prev < withinMs) {
      duplicates.push(`DUPLICATE: ${key} (${entry.time - prev}ms apart)`);
    }
    seen.set(key, entry.time);
  }
  expect(duplicates, `API duplicate calls detected:\n${duplicates.join('\n')}`).toHaveLength(0);
}

// Gọi sau action:
await submitButton.click();
await page.waitForLoadState('networkidle');
assertNoDuplicateApiCall(apiLog);
```

### 12c. Verify UI reflect đúng API response

**Rule:** UI phải hiển thị đúng những gì API trả về — không được bỏ qua error từ server.

```typescript
// Bắt response cụ thể
const [resp] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/items') && r.request().method() === 'POST'),
  submitButton.click(),
]);

const status = resp.status();
const body = await resp.json().catch(() => null);

if (status === 200 || status === 201) {
  // Assert UI hiển thị thành công
  await expect(page.getByRole('alert')).toContainText('Thành công');
  // Assert item xuất hiện trên danh sách
} else if (status === 400) {
  // Assert UI hiển thị đúng message lỗi từ server
  const serverMsg = body?.message || body?.error || '';
  await expect(page.locator('[class*="error"]:visible').first()).toContainText(serverMsg);
} else if (status === 422) {
  // Validation error — thường có field-level errors
  // Assert từng field error nếu server trả về errors object
}

// Log vào evidence
await page.screenshot({ path: `output/evidence/${tcId}/api_response_${status}.png` });
```

**Checklist bắt buộc khi implement:**
- [ ] Tất cả action gọi API đều có `page.waitForResponse()` tương ứng (không fire-and-forget)
- [ ] Case 200/201 → assert UI thành công VÀ assert data hiển thị
- [ ] Case 400/422 → assert UI hiển thị đúng error message từ server (không hardcode)
- [ ] Không có duplicate call (assertNoDuplicateApiCall pass)
- [ ] API log được ghi vào `task.md` mục evidence khi fail

### 12d. Ghi API calls vào evidence khi FAIL

Xem mẫu ở **12a** (afterEach). Bắt buộc attach `api-calls.txt` khi `testInfo.status === 'failed'`.

### 12e. List / Detail / Sửa / Phê duyệt — Lưu data-mapping evidence (Pattern A)

Với TC danh sách (LIST), chi tiết (DETAIL), **chỉnh sửa (EDIT), phê duyệt (APPROVE)** — sau khi load xong, so sánh API response với UI và lưu `data-mapping.json`.

**Phạm vi capture:**
- **List** → row đầu tiên của bảng.
- **Detail / Sửa / Phê duyệt** → **toàn bộ field** của form/card (đối chiếu từng field giá trị API ↔ giá trị hiển thị trên UI), không chỉ 1 field.

**Pattern A — Initial load:**
```typescript
// Bắt API response khi navigate vào màn
const [resp] = await Promise.all([
  page.waitForResponse(r => /\/admin-members/.test(r.url()) && r.request().method() === 'GET'),
  listPage.goto(),
]);
const body = await resp.json().catch(() => null);
const firstItem = body?.items?.[0] ?? body?.data?.[0];

if (firstItem) {
  // Đọc UI values từ row đầu tiên
  const uiName  = (await listPage.tableRows.first().locator('td').nth(0).textContent())?.trim() ?? '';
  const uiEmail = (await listPage.tableRows.first().locator('td').nth(1).textContent())?.trim() ?? '';

  const mappingFields = [
    { field: 'Họ tên',    apiValue: firstItem.fullName ?? firstItem.name ?? '', uiDisplay: uiName,  match: uiName  === (firstItem.fullName ?? firstItem.name ?? '') },
    { field: 'Email',     apiValue: firstItem.email ?? '',                      uiDisplay: uiEmail, match: uiEmail === (firstItem.email ?? '') },
  ];

  const fs = await import('fs');
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  fs.writeFileSync(`${EVIDENCE_DIR}/${tcId}_data-mapping.json`, JSON.stringify({ tcId, fields: mappingFields }, null, 2));
}
```

**Lưu ý:**
- `apiValue` = giá trị thô từ API JSON; `uiDisplay` = text hiển thị trên table cell.
- `match = true` nếu sau khi normalize (trim, lowercase nếu cần) hai giá trị bằng nhau.
- Với TC DETAIL / SỬA / PHÊ DUYỆT: capture **tất cả fields** của form/card, không chỉ row đầu. Nguồn `apiValue` = response GET chi tiết (hoặc data đã tạo nếu màn không gọi GET).
- Lưu vào cùng `EVIDENCE_DIR` với các file evidence khác.

### 12f. Search / Filter — Lưu count evidence

Với TC tìm kiếm và lọc, capture API response để lưu `search-count.json` / `filter-count.json`.

Dùng `Promise.all([waitForResponse, action()])` để tránh race condition:

```typescript
async function captureNextApiResponse(
  page: Page, urlPattern: RegExp, action: () => Promise<void>, timeout = 15_000,
): Promise<any> {
  try {
    const [res] = await Promise.all([
      page.waitForResponse(r => urlPattern.test(r.url()) && r.request().method() === 'GET', { timeout }),
      action(),
    ]);
    return await res.json().catch(() => null);
  } catch { return null; }
}

// Trong test search:
const apiBody = await captureNextApiResponse(page, /my-api-endpoint/i, () => listPage.search(keyword));
if (apiBody) {
  const totalItems = apiBody?.data?.totalItems;
  const uiRows = await page.locator('tbody tr').count();
  saveJson(`${TC_ID}_search-count.json`, { tcId, keyword, apiTotal: totalItems, uiRowCount: uiRows, note: '...' });
}

// Trong test filter:
const apiBody = await captureNextApiResponse(page, /my-api-endpoint/i, () => listPage.filterByStatus('ACTIVE'));
if (apiBody) {
  saveJson(`${TC_ID}_filter-count.json`, { tcId, filter: 'Trạng thái: Kích hoạt', apiTotal, uiRowCount, note: '...' });
}
```

---

## 14. Verification Depth — Màn hình danh sách

> Áp dụng khi test TC loại "Xem danh sách", "Tìm kiếm", "Lọc", "Sắp xếp". Không được chỉ verify `toBeVisible()` trên container — phải verify tới level data.

### 14a. Column Headers — Verify theo tên, không chỉ đếm

```typescript
// SAI — chỉ đếm, không biết cột sai tên
await expect(page.locator('thead th')).toHaveCount(8);

// ĐÚNG — verify từng cột có tên đúng
const expectedColumns = ['Họ tên', 'Email', 'Số điện thoại', 'Trạng thái'];
for (const col of expectedColumns) {
  await expect(
    page.locator('thead').getByText(col, { exact: false }),
    `Column "${col}" phải hiển thị`,
  ).toBeVisible({ timeout: 5_000 });
}
// Cột icon-only (Actions, ...) → vẫn dùng count để verify số cột tổng
const thCount = await page.locator('thead th').count();
expect(thCount).toBe(8);
```

### 14b. First Row Data — Verify đủ fields, không chỉ "row tồn tại"

```typescript
// SAI — chỉ verify row có tồn tại
await expect(listPage.tableRows.first()).toBeVisible();

// ĐÚNG — verify từng field quan trọng của row đầu tiên
const firstRow = listPage.tableRows.first();
const cells = firstRow.locator('td');

// Field tên chính không được rỗng
const nameText = (await cells.nth(0).textContent())?.trim();
expect(nameText, 'Cột tên chính không được rỗng').toBeTruthy();

// Ít nhất 1 contact field (email hoặc phone) phải có giá trị
const emailText = (await cells.nth(1).textContent())?.trim();
const phoneText = (await cells.nth(2).textContent())?.trim();
expect(emailText || phoneText, 'Email hoặc SĐT phải có giá trị').toBeTruthy();

// Toggle trạng thái tồn tại
await expect(firstRow.locator("button[role='switch']")).toBeVisible();

// Action buttons tồn tại
await expect(firstRow.locator('td:last-child').locator('a, button').first()).toBeVisible();
```

### 14c. Search — Keyword từ data thực, verify TỪNG row kết quả

```typescript
// SAI — keyword hard-code, không biết có data không
await listPage.search('Nguy');
await expect(listPage.tableRows.first()).toBeVisible(); // pass ngay cả khi empty

// ĐÚNG — lấy keyword từ row đầu tiên của table
await expect(listPage.tableRows.first()).toBeVisible({ timeout: 15_000 });
const firstName = (await listPage.tableRows.first().locator('td').nth(0).textContent())?.trim() ?? '';
const keyword = firstName.split(/\s+/).find(w => w.length >= 2) ?? firstName.slice(0, 3);
expect(keyword.length, 'Phải có keyword từ data thực').toBeGreaterThan(0);

await listPage.search(keyword);
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

const rows = listPage.tableRows;
const count = await rows.count();
expect(count, 'Phải có kết quả khi search bằng keyword lấy từ data').toBeGreaterThan(0);

// Verify TỪNG row — không chỉ row đầu
for (let i = 0; i < count; i++) {
  const cellText = (await rows.nth(i).locator('td').nth(0).textContent())?.toLowerCase() ?? '';
  expect(cellText, `Row ${i + 1} phải chứa keyword "${keyword}"`).toContain(keyword.toLowerCase());
}
```

**Lưu ý:** Nếu search áp dụng trên nhiều field (name + email + phone), verify theo OR: row khớp ở BẤT KỲ field nào đều hợp lệ.

### 14d. Filter — Verify TẤT CẢ rows khớp criterion

```typescript
// SAI — chỉ verify container visible
await listPage.filterByStatus('Kích hoạt');
await expect(listPage.tableContainer).toBeVisible(); // luôn pass dù filter sai

// ĐÚNG — verify TẤT CẢ rows đều có trạng thái đúng
await listPage.filterByStatus('Kích hoạt');
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

const count = await listPage.tableRows.count();
const checkUpTo = Math.min(count, 15); // giới hạn 15 rows nếu danh sách dài
for (let i = 0; i < checkUpTo; i++) {
  const toggle = listPage.tableRows.nth(i).locator("button[role='switch']");
  await expect(
    toggle,
    `Row ${i + 1}: toggle phải "checked" khi filter Kích hoạt`,
  ).toHaveAttribute('data-state', 'checked');
}

// Filter theo text badge (nhóm phân quyền, loại...)
await listPage.filterByGroup('AA');
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
const filteredRows = await listPage.tableRows.count();
for (let i = 0; i < Math.min(filteredRows, 15); i++) {
  const rowText = (await listPage.tableRows.nth(i).textContent())?.toLowerCase() ?? '';
  expect(rowText, `Row ${i + 1} phải thuộc nhóm "AA"`).toContain('aa');
}
```

**Verify API được gọi khi filter:**
```typescript
// Đếm requests trước/sau filter — verify filter trigger network call
let reqCount = 0;
page.on('request', () => { reqCount++; });
const before = reqCount;

await listPage.filterByStatus('Kích hoạt');
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

expect(reqCount, 'Filter phải trigger ít nhất 1 request').toBeGreaterThan(before);
```

### 14e. Sort — Capture values trước/sau, so sánh thứ tự thực tế

```typescript
// SAI — chỉ verify container visible sau sort
await sortHeader.click();
await expect(listPage.tableContainer).toBeVisible(); // không verify sort thực sự hoạt động

// ĐÚNG — so sánh column values trước và sau sort

// Helper: lấy text của một cột từ tất cả rows hiển thị
async function getColumnTexts(page: Page, colIndex: number): Promise<string[]> {
  return page.locator('tbody tr').evaluateAll(
    (rows: HTMLTableRowElement[], idx: number) =>
      rows.map(r => r.cells[idx]?.textContent?.trim() ?? ''),
    colIndex,
  );
}

// Chờ table ổn định
await expect(listPage.tableRows.first()).toBeVisible();
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

// Sort ASC
const sortHeader = page.locator('thead th').filter({ hasText: /họ.tên|tên|name/i }).first();
await sortHeader.click();
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

const valuesAsc = await getColumnTexts(page, 0);
// Verify từng cặp liền kề: a[i] <= a[i+1]
for (let i = 0; i < valuesAsc.length - 1; i++) {
  const cmp = valuesAsc[i].localeCompare(valuesAsc[i + 1], 'vi', { sensitivity: 'base' });
  expect(cmp, `Sort ASC: "${valuesAsc[i]}" phải <= "${valuesAsc[i + 1]}"`).toBeLessThanOrEqual(0);
}

// Sort DESC (click lần 2)
await sortHeader.click();
await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

const valuesDesc = await getColumnTexts(page, 0);
for (let i = 0; i < valuesDesc.length - 1; i++) {
  const cmp = valuesDesc[i].localeCompare(valuesDesc[i + 1], 'vi', { sensitivity: 'base' });
  expect(cmp, `Sort DESC: "${valuesDesc[i]}" phải >= "${valuesDesc[i + 1]}"`).toBeGreaterThanOrEqual(0);
}
```

**Lưu ý:** Sort có thể server-side hoặc client-side — cả hai đều verify được bằng cách so sánh giá trị hiển thị, không cần biết implementation.

---

## 13. Pagination — Bắt buộc với màn hình danh sách có phân trang

Khi màn hình có pagination controls (số trang, nút next/prev, bộ chọn items/page), bắt buộc implement các assertion sau:

### Assert trạng thái pagination sau load

```typescript
// Verify tổng số item khớp với API response
const [resp] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/items') && r.request().method() === 'GET'),
  listPage.goto(),
]);
const body = await resp.json();
const totalFromApi = body.total ?? body.totalCount ?? body.data?.total;

// Verify UI hiển thị đúng số lượng
await expect(listPage.totalCountLabel).toHaveText(new RegExp(String(totalFromApi)));

// Verify số item trên trang không vượt quá page size
const rows = await listPage.tableRows.count();
expect(rows).toBeLessThanOrEqual(pageSize);
```

### Assert nút prev/next đúng trạng thái

```typescript
// Trang đầu: prev phải disabled
await expect(listPage.prevButton).toBeDisabled();
await expect(listPage.nextButton).toBeEnabled();

// Navigate sang trang 2
await listPage.nextButton.click();
await page.waitForLoadState('networkidle');
await expect(listPage.prevButton).toBeEnabled();

// Trang cuối: next phải disabled
await listPage.goToLastPage();
await expect(listPage.nextButton).toBeDisabled();
```

### Assert không có duplicate API call khi navigate trang

Áp dụng Rule 12b — navigate trang không được trigger 2 GET request cùng lúc.

### Không assert pagination khi chỉ có 1 trang

```typescript
if (totalFromApi <= pageSize) {
  // Verify không có pagination controls, hoặc chúng disabled
  // Không navigate trang khi không cần
}
```

---

## 15. Re-run — CHỈ chạy lại TC đang FAIL, tối đa 2 lần mỗi TC

**Rule:**
- Toàn bộ suite chỉ được chạy **đúng 1 lần** duy nhất.
- Sau đó, **chỉ được chạy lại đúng TC bị FAIL** (dùng `--grep`), tối đa **2 lần** mỗi TC.
- **TUYỆT ĐỐI KHÔNG chạy lại toàn bộ suite** dù chỉ có 1 TC fail.
- **Ngoại lệ DUY NHẤT:** khi fix chạm **shared-code** (POM / util / fixture / `isMainApi`/predicate / config) → re-run **mọi TC phụ thuộc code đó** (kể cả TC đang PASS), vì fix có thể làm evidence của TC PASS sai/thiếu âm thầm (xem mục 20).

**Lý do:** Tránh tốn thời gian, tránh side-effect lên TC đang PASS (tạo data dư, đổi trạng thái dữ liệu trên UAT).

```bash
# ĐÚNG — chỉ chạy đúng TC bị fail
export PATH="$HOME/.nvm/versions/node/v24.15.0/bin:$PATH"
node ./node_modules/.bin/playwright test --grep "TC-14" --headed

# ĐÚNG — nhiều TC fail cùng lúc
node ./node_modules/.bin/playwright test --grep "TC-14|TC-27|TC-33" --headed

# SAI — chạy lại toàn bộ dù chỉ có vài TC fail
node ./node_modules/.bin/playwright test output/tests/ --headed
```

**Quy trình auto-heal (Rule E3):**
1. Chạy toàn bộ suite **1 lần duy nhất**
2. Ghi nhận danh sách TC FAIL
3. Với mỗi TC FAIL:
   - Đọc log lỗi → phân tích nguyên nhân → sửa code
   - Xóa evidence cũ của TC đó (xem Rule 16)
   - Chạy lại **đúng TC đó**: `playwright test --grep "TC-XX"`
   - PASS → ✅. Vẫn FAIL → sửa lần 2, chạy lại 1 lần nữa (tổng tối đa **2 lần re-run**)
   - Vẫn FAIL sau 2 lần → mark ❌, ghi vào report, **KHÔNG chạy tiếp**

---

## 16. Re-run — Xóa evidence cũ trước khi chạy lại

**Rule:** Trước khi re-run, xóa tất cả file evidence của TC đó trong thư mục module/function.

**Lý do:** Evidence từ lần chạy FAIL sẽ lẫn với evidence mới, gây nhầm lẫn khi review.

```bash
# Evidence nằm tại: output/evidence/<env>/<portal>/<module>/<function>/
# Xóa đúng các file của TC đang re-run (theo pattern [TC-CREATE-01]* và TC-CREATE-01_*)
find output/evidence/uat/admin/user-management/tao-moi -name "[TC-CREATE-01]*" -o -name "TC-CREATE-01_*" | xargs rm -f

# KHÔNG xóa toàn bộ thư mục — sẽ mất evidence của TC khác
```

---

## 17. API Response — Lưu ra file JSON per TC (cả PASS lẫn FAIL)

**Rule:** `afterEach` luôn lưu 1 file JSON cho mọi TC có action gọi API:
- `<TC_ID>_api-calls.json` — toàn bộ API calls; main API entry có thêm `responseBody`
- Tên file chỉ dùng TC ID, **KHÔNG dùng slug từ tên test case**

Xem mẫu đầy đủ tại **Rule 12a** (afterEach pattern).

**Cấu trúc evidence folder (tất cả TC cùng module/function trong 1 thư mục):**
```
output/evidence/uat/admin/user-management/tao-moi/
  [TC-CREATE-01][01_form_loaded].png
  [TC-CREATE-01][02_form_filled].png
  [TC-CREATE-01][03_after_submit].png
  TC-CREATE-01_api-calls.json
  [TC-CREATE-02][01_form_filled].png
  TC-CREATE-02_api-calls.json
  ...
```

---

## 18. Assertion count — Dùng count() + expect() thay vì toHaveCount({ minimum })

**Rule:** `toHaveCount({ minimum: N })` KHÔNG phải là Playwright API hợp lệ. Dùng pattern sau:

```typescript
// SAI — không tồn tại trong Playwright API
await expect(locator).toHaveCount({ minimum: 7 });

// ĐÚNG — dùng count() + expect thuần
const count = await locator.count();
expect(count).toBeGreaterThanOrEqual(7);
```

Áp dụng cho mọi assertion "có ít nhất N element".

---

## 19. Ép trạng thái "không có dữ liệu" / lỗi bằng route interception

> Triển khai cho `testcase_writing_rules.md` RULE 16.3. Khi môi trường thật khó tạo trạng thái rỗng / lỗi server, dùng `page.route` chặn và giả response — KHÔNG xoá data thật trên UAT.

**Empty state — giả response danh sách rỗng:**
```typescript
await page.route(/\/api\/items/, async route => {
  if (route.request().method() !== 'GET') return route.continue();
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ items: [], total: 0 }),  // khớp shape API thật
  });
});
await listPage.goto();
await expect(page.getByText('Không có dữ liệu', { exact: true })).toBeVisible(); // message exact SRS
```

**Lỗi server — giả 500/400 để verify UI báo lỗi:**
```typescript
await page.route(/\/api\/items/, route =>
  route.fulfill({ status: 500, contentType: 'application/json', body: '{"message":"Lỗi hệ thống"}' }),
);
```

**Nguyên tắc:**
- Body giả **phải khớp shape API thật** (đọc từ `_api-calls.json` lần chạy trước hoặc curl mẫu) — sai shape thì UI render sai, không phản ánh đúng hành vi.
- **Gỡ route sau khi verify** (`await page.unroute(...)`) nếu test còn thao tác tiếp với data thật.
- Chỉ dùng khi không thể tạo trạng thái tự nhiên — ưu tiên data thật khi khả thi.

---

## 20. Evidence completeness là ASSERTION, KHÔNG phải side-effect (CRITICAL)

> Lỗi từng gặp: predicate `isMainApi` sai → `body = null` → khối `if (body) { lưu data-mapping }` bị bỏ qua **âm thầm**, test vẫn PASS nhưng evidence thiếu. Tới lúc gen report mới lộ. Cấm tái diễn.

**Nguyên tắc:** với TC bắt buộc có evidence API (list / detail / sửa / phê duyệt / search / filter — RULE 16, report_rules §1), việc **bắt được main API là điều kiện PASS**, không phải tuỳ chọn.

- **Assert bắt được response TRƯỚC khi dùng** — KHÔNG `if (body)` rồi im lặng bỏ qua:
  ```typescript
  const body = await ump.gotoList();
  expect(body, 'Phải bắt được response main API (list) — kiểm tra isMainApi/predicate').not.toBeNull();
  // sau đó MỚI lưu data-mapping / api-response từ body
  ```
- Sau khi lưu, **assert file evidence đã tồn tại** (fail nếu thiếu):
  ```typescript
  expect(fs.existsSync(`${EVIDENCE_DIR}/${tcId}_data-mapping.json`), 'Thiếu data-mapping.json').toBeTruthy();
  ```
- `isMainApi`/predicate **lấy từ recon, không đoán** (xem `generate-automation-from-testcases.md` Bước 2 — recon ghi `apiEndpoints` thật vào locator repo). Nếu chưa biết → chạy 1 lần `isMainApi = () => true`, đọc `_api-calls.json`, chốt URL **rồi mới** viết assertion.

→ Hệ quả: predicate sai = test **FAIL ngay vòng đầu** (không phải xanh giả) → được heal trong cùng lần chạy, không bao giờ lọt tới report.

---

## 21. Chất lượng Evidence & API log (BẮT BUỘC — từ feedback thực tế)

### 21.1 — API log: CHỈ Fetch/XHR + CHỈ hành động chính
- Listener chỉ ghi request có `resourceType` ∈ {`fetch`,`xhr`} — bỏ document/script/css/img/font.
- **Loại bỏ API bootstrap** (đăng nhập → vào màn): `auth/login`, `auth/refresh`, `me/userinfo`, `me/permissions`, `groups/checkbox`, ... KHÔNG đưa vào api-calls.json.
- **Scope theo hành động:** `apiLog.length = 0` (reset) **ngay trước** action chính của TC (sau khi đã vào màn/đã setup). → api-calls.json chỉ chứa API của **chính hành động đang test** + sau submit, không phải từ lúc login.
- `ApiMonitor.ts` đã hỗ trợ filter resourceType + bootstrap exclude; spec gọi `resetApiLog()` tại ranh giới action.

### 21.2 — Data-mapping: ĐỦ MỌI CỘT, không phải 1 cột
- TC danh sách: map **tất cả cột** của row đầu (Họ tên, Email, SĐT, Chức vụ, Phòng ban, Nhóm phân quyền, Trạng thái) — API value ↔ UI display ↔ match cho từng cột.
- TC chi tiết/sửa/duyệt: map **toàn bộ field** của form/card.

### 21.3 — Screenshot: scroll chụp ĐỦ cột + ĐỦ pagination
- Bảng có scroll ngang → scroll để ảnh thấy **mọi cột** (đặc biệt cột Trạng thái ở cuối) trước khi verify/chụp.
- Vùng pagination ở dưới → `scrollIntoViewIfNeeded()` rồi chụp để thấy **đầy đủ** số trang + tổng + page-size.
- Verify cột nào thì phải scroll cột đó vào viewport rồi mới assert (không assert cột ngoài màn).

### 21.4 — Pagination: tính từ API + đủ 5 case điều hướng + mỗi case có API
- Tính `totalPages = ceil(total / pageSize)` từ **API response** (total + item/page) → **so sánh với số trang hiển thị** trên thanh pagination UI.
- Bắt buộc đủ **5 case**: First page, Last page, Next page, Previous page, **Any page (click số trang bất kỳ)**.
- **Mỗi case điều hướng phải bắt được API list response** (GET admin-members) + assert không duplicate.

### 21.5 — List bắt buộc có case "API 200 nhưng data rỗng"
- Khác case 500 (mục 19): dùng route fulfill **status 200** với `items: [], total: 0` → verify UI hiển thị empty-state đúng (phân biệt với lỗi tải).

### 21.6 — DETAIL: kiểm tra cả các tab khác
- Không chỉ tab "Thông tin cá nhân" — verify chuyển được sang tab "Lịch sử thay đổi" và "Phiên đăng nhập" (tab active đổi + nội dung tab load).

### 21.7 — Action mutating: chụp ảnh TRƯỚC + SAU
- CREATE/UPDATE/RESET: bắt buộc screenshot **trước submit** (form đã điền) VÀ **sau submit** (kết quả) — để report phân biệt được các case khác nhau ở input.

### 21.9 — Detector lỗi/cảnh báo: KHÔNG match nhãn tĩnh + chờ render + đọc API body

> 3 lỗi từng gặp ở case "trùng dữ liệu" làm pass/fail SAI:
1. **Cấm regex bắt trúng NHÃN field.** Vd kiểm cảnh báo trùng SĐT mà regex chứa "Số điện thoại" → match nhãn field (luôn hiển thị) → false-positive. Chỉ bắt **text lỗi đặc trưng** ("đã tồn tại", "trùng", "không hợp lệ"...), loại từ trùng với label.
2. **Cảnh báo có thể render trễ/transient** → chờ (`waitForTimeout`/`waitFor visible`) trước khi kết luận "không có cảnh báo". Kết luận quá sớm = sai.
3. **Tồn tại/trùng nằm trong API BODY, không phải status.** check-* trả 200 luôn; phải đọc `body.data`. Lưu ý hệ thống có thể gọi **nhiều biến thể** (vd SĐT giữ-0 vs strip-0) — bắt **đúng call** báo tồn tại, đừng bắt nhầm call đầu.
4. Tín hiệu **mạnh nhất** cho "trùng bị chặn" = **không có POST tạo thành công (2xx)** (không tạo được bản trùng), kết hợp với cảnh báo hiển thị.

### 21.8 — Nghịch lý "lỗi hiển thị nhưng API 2xx" → phải điều tra & ghi rõ
- Nếu UI báo lỗi mà API trả 200 (vd CREATE email trùng): bắt **response body** của API đó, kiểm `success`/`errorCode` trong body. Ghi vào evidence + report actual result (có thể là check client-side hoặc API trả 200 kèm cờ lỗi).
