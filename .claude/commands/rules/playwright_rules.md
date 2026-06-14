# Quy Tắc Dành Riêng Cho Playwright

> Áp dụng khi thiết lập và chạy automation với Playwright (TypeScript hoặc Java).

## 1. Thiết Lập Browser (BẮT BUỘC)

- **Viewport debug:** Mọi quá trình debug UI bắt buộc chạy với viewport desktop: **`1920x1080`**.
- **Playwright MCP — Resize bắt buộc:** Khi sử dụng Playwright MCP để debug UI, **LUÔN LUÔN** gọi `browser_resize(width=1920, height=1080)` **ngay sau khi mở browser** (sau lệnh `browser_navigate` đầu tiên). Đây là bước bắt buộc, không được bỏ qua.
  ```
  Thứ tự bắt buộc:
  1. browser_navigate(url) → mở trang
  2. browser_resize(width=1920, height=1080) → set viewport
  3. browser_snapshot() hoặc browser_take_screenshot() → bắt đầu inspect
  ```
- **Headed mode:** Bắt buộc mở browser có hiển thị (headed) trong quá trình thiết lập và debug test.
- **Headless mode:** Chỉ được phép sử dụng khi:
  - Test đã debug PASS 100% trên headed mode
  - Hoặc trong CI/CD pipeline mặc định

## 2. Workflow Phát Triển & Tìm Element

- Ưu tiên sử dụng **Playwright MCP** để mở browser và tương tác với trang đích.
- **Inspect DOM thực tế:** Verify và capture selector trực tiếp từ browser DOM.
- **TUYỆT ĐỐI KHÔNG:**
  - Suy đoán locator
  - Copy locator mù quáng từ code cũ mà không verify
  - Dựa trên URL / tài liệu mà không xác nhận sự tồn tại trên UI thật

## 3. Thứ Tự Ưu Tiên Locator Playwright

Playwright cung cấp bộ locator semantic hướng người dùng. Ưu tiên sử dụng thay vì CSS/XPath:

1. `getByRole()` — Tốt nhất cho semantic elements (button, link, heading...)
2. `getByLabel()` — Tốt nhất cho form fields có label
3. `getByPlaceholder()` — Tốt nhất cho inputs có placeholder text
4. `getByText()` — Tốt nhất cho text content
5. `getByTestId()` — Tốt nhất khi element có `data-testid`
6. `locator("css")` — Fallback khi không có lựa chọn tốt hơn

Ví dụ:
```typescript
// Đúng — Semantic locator
page.getByRole('button', { name: 'Đăng nhập' })
page.getByLabel('Email')
page.getByPlaceholder('Nhập mật khẩu')

// Sai — XPath/CSS thô khi có semantic thay thế
page.locator('//button[@class="btn-login"]')
page.locator('.form-input:nth-child(2)')
```

## 4. Chiến Lược Chờ Đợi (Wait Strategy)

**NGHIÊM CẤM:**
- `page.waitForTimeout()` — hard sleep
- `waitUntil: 'networkidle'` và `waitForLoadState('networkidle')` — **DISCOURAGED bởi chính Playwright**. Với web hiện đại (SPA, polling, analytics nền) mạng không bao giờ idle hẳn → test **treo tới timeout rồi fail**, đặc biệt nặng khi qua VPN/mạng chậm. Đây là một trong các nguyên nhân flaky phổ biến nhất.
- `await new Promise(r => setTimeout(r, N))` — tự tạo delay
- Bất kỳ cách nào cố định thời gian chờ

**SỬ DỤNG:**
- Tận dụng auto-waiting mặc định của Playwright
- **Trước khi click submit/action button — phân biệt 2 loại case:**

  **Case submit thành công** (Expected: "thành công", "trạng thái chuyển sang...", "popup thành công"):
  ```typescript
  // Đợi form sẵn sàng = không có error nào + button enabled
  await expect(page.locator('[class*="error"]:visible, [class*="invalid"]:visible')).toHaveCount(0);
  await expect(submitButton).toBeEnabled({ timeout: 60_000 });
  await submitButton.click();
  ```
  Cách này tự động cover mọi prerequisite (slug validation, file upload...) mà không cần biết URL API cụ thể.

  **Case validate** (Expected: "hiển thị lỗi", "inline message", "không cho phép"):
  ```typescript
  // KHÔNG đợi button enabled — mục tiêu là trigger lỗi
  await submitButton.click();
  await expect(page.locator('text=Vui lòng...')).toBeVisible();
  ```

- **Đọc cột Expected Result để phân biệt:**
  - Expected chứa error/lỗi/cảnh báo/không cho phép → **validate case** → click thẳng
  - Expected chứa thành công/trạng thái chuyển/navigate → **submit case** → đợi `no errors + enabled`

- **Thay networkidle bằng**: chờ điều kiện tất định + element cụ thể:
  ```typescript
  // Thay vì waitUntil:'networkidle'
  await page.goto(url, { waitUntil: 'domcontentloaded' });   // sự kiện chắc chắn xảy ra
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();  // chờ đúng cái cần
  ```
  `expect` có vòng retry nội bộ (poll ~100ms) nên tự chờ nội dung async mà không phụ thuộc mạng yên.
- Web-First Assertions:
  ```typescript
  await expect(locator).toBeVisible();
  await expect(locator).toBeEnabled();
  await expect(locator).toHaveText('Thành công');
  await expect(page).toHaveURL(/dashboard/);
  ```
- Chỉ dùng `waitForSelector()` khi `expect()` không đáp ứng được yêu cầu đặc biệt

## 5. Cấu Trúc Test

```typescript
test.describe('Tên Module', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: navigate, login...
  });

  test('mô tả hành vi cần test', async ({ page }) => {
    // Arrange: khởi tạo page objects, data
    // Act: thực hiện hành động
    // Assert: kiểm tra kết quả
  });
});
```

- Mỗi test block phải có **assertion rõ ràng**
- Sử dụng `test.describe` để nhóm test theo module
- Sử dụng `beforeEach` / `afterEach` để setup / teardown

## 6. Exact Text Matching (error / toast / message)

Mặc định `getByText()` match **substring** → message sai vẫn lọt. Khi cần đúng nội dung:
```typescript
// Exact — dùng cho validation/toast có nội dung cụ thể
await expect(locator).toHaveText('The Email Address field is required.');
await expect(page.getByText('Invalid email or password', { exact: true })).toBeVisible();
```
Lấy text nguyên văn từ cột Expected của test case. Xem `test_execution_rules.md` mục 1.

## 7. API Calls trong Test — Dùng `page.evaluate(fetch())`

Khi cần gọi API từ test (tạo test data, setup precondition), **KHÔNG dùng `node-fetch` hay `axios`** — dùng `page.evaluate()` để fetch từ bên trong browser context:

```typescript
const result = await page.evaluate(async ({ url, token, body }) => {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return { status: resp.status, data: await resp.json() };
}, { url, token, body });
```

**Lý do:** Đi qua VPN giống browser (không bị chặn), tránh CORS, không cần cài thêm HTTP client.

## 8. Network Interception (API / trim verification)

Quan sát request/response thật trong UI test (khác REST Assured):
```typescript
// Response
const resp = await page.waitForResponse(r => r.url().includes('/api/x') && r.request().method() === 'POST');
expect(resp.status()).toBe(200);
const body = await resp.json();

// Request (dùng cho kiểm trim — đọc payload gửi lên)
const req = await page.waitForRequest(r => r.url().includes('/api/x') && r.method() === 'POST');
const sent = JSON.parse(req.postData() || '{}');
expect(sent.name).toBe('John Doe');   // đã trim
```
Trim PHẢI kiểm bằng request body, KHÔNG đoán qua UI. Xem `test_execution_rules.md` mục 3, 4.

## 9. Evidence (screenshot theo bước)

**Bắt buộc với MỌI chế độ chạy — kể cả headed (browser hiển thị).** Headed mode không miễn evidence: browser có thể thấy được nhưng ảnh là bằng chứng truy vết bất biến sau khi test chạy xong.

**Scroll đến element trước khi chụp** để element hiển thị rõ trong ảnh (không bị cắt hoặc nằm ngoài vùng nhìn):
```typescript
// Scroll đến element cần chụp evidence, rồi mới screenshot
await errorLocator.scrollIntoViewIfNeeded();
await page.screenshot({ path: `output/evidence/${tcId}/03_error_shown.png`, fullPage: true });
```

Chụp ở mốc quan trọng mỗi case (sau fill, sau submit, tại assert) + khi fail. Trace: `--trace on-first-retry`. Xem `test_execution_rules.md` mục 5.

## 10. Timeout cho môi trường chậm (VPN / mạng yếu)

**QUAN TRỌNG — phân biệt với hard-sleep (mục 4):** nâng timeout ≠ hard-sleep.
- Hard-sleep (`waitForTimeout`) = chờ cứng N giây dù element đã sẵn sàng → CẤM.
- Nâng timeout = đặt **trần thời gian chờ tối đa**; element/response tới sớm thì tiếp tục ngay → ĐƯỢC PHÉP khi môi trường chậm.

**Khi nào nâng:** web cần VPN, mạng yếu, hoặc agent quan sát thấy navigation/response liên tục chậm (nhưng KHÔNG fail vì lỗi logic). Agent tự quyết mức nâng theo độ chậm thực tế quan sát được — không có con số cố định.

**Nâng đúng 3 tầng** (VPN ảnh hưởng cả ba, sót tầng nào case đó vẫn fail):

1. **Navigation** (tải trang — chậm nhất qua VPN):
   ```typescript
   await page.goto(url, { timeout: 60_000 });        // per-call
   // hoặc global trong config: use: { navigationTimeout: 60_000 }
   ```
2. **Action / expect** (chờ element, assertion):
   ```typescript
   await expect(locator).toBeVisible({ timeout: 30_000 });
   // hoặc global: expect: { timeout: 30_000 }, use: { actionTimeout: 30_000 }
   ```
3. **API response** (round-trip qua VPN — phần waitForResponse mục 7):
   ```typescript
   const resp = await page.waitForResponse(pred, { timeout: 45_000 });
   ```

**Đặt ở config theo môi trường, KHÔNG hardcode trong test:**
```typescript
// playwright.config.ts — đọc biến môi trường, đổi khi chạy VPN
const slow = !!process.env.VPN || !!process.env.SLOW_NET;
export default defineConfig({
  timeout: slow ? 120_000 : 30_000,        // test timeout tổng
  expect: { timeout: slow ? 30_000 : 10_000 },
  use: {
    navigationTimeout: slow ? 60_000 : 30_000,
    actionTimeout: slow ? 30_000 : 15_000,
  },
});
```
Chạy: `VPN=1 npx playwright test`. Test code GIỮ NGUYÊN — chỉ đổi config khi môi trường chậm.

**Vẫn ưu tiên web-first assertion (auto-wait) làm cơ chế chính** — timeout chỉ là trần an toàn, không thay thế auto-wait.

## 11. Login Fixture — Phải chờ redirect hoàn toàn

Sau khi click submit login, **KHÔNG return ngay**. Phải chờ browser navigate khỏi `/login`:

```typescript
// ❌ SAI — return ngay sau click, auth chưa settle
await loginButton.click();

// ✅ ĐÚNG — chờ navigation hoàn thành
await Promise.all([
  page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60_000 }),
  loginButton.click(),
]);
```

**Lý do:** SPA sau khi POST login lưu token vào localStorage rồi mới redirect. Nếu test tiếp tục ngay, navigate tiếp có thể bị redirect về `/login` vì auth chưa settle.

**KHÔNG dùng `waitForLoadState('networkidle')`** thay thế — VPN + SPA polling khiến network không bao giờ idle → treo 60s rồi timeout.

**Tác động đặc biệt:** Test KHÔNG có bước khởi tạo data qua API (batch overdue, cross-portal, concurrent) rất dễ bị race condition này vì không có delay tự nhiên sau login.

## 12. Rich-text Editor (TipTap/ProseMirror) — fill() vs keyboard.type()

```typescript
// ❌ fill() — set DOM trực tiếp, bypass keyboard events
await richTextEditor.fill('content');  // KHÔNG trigger: maxlength, validation, character count

// ✅ keyboard.type() — gõ thực sự, trigger mọi event handler
await richTextEditor.click();
await page.keyboard.type('content', { delay: 0 });
```

**Quy tắc:**
- Dùng `fill()` khi chỉ cần điền text để proceed (không test validate/maxlength)
- Dùng `keyboard.type()` khi test: maxlength, character counter, input validation của editor

## 13. Tab panel với Card Layout — Không dùng tbody tr

**Rule:** Một số tab panel (ví dụ: tab Lịch sử hoạt động trong User Detail) sử dụng **card/div layout**, KHÔNG dùng `<table>`. Locator `tbody tr` sẽ trả về 0 element và khiến test fail ngay cả khi data đang hiển thị.

**Cách nhận biết:** Khi `page.locator('tbody tr').count()` trả về 0 dù UI đang hiển thị rows → inspect DOM để xác định layout thực tế.

**Locator cho card layout (đã verify trên TPcoms UAT):**
```typescript
// History tab — card layout
const historyCards = page.locator("[role='tabpanel'] .flex.justify-between.items-start.p-6.rounded-lg.border");

// Verify có items
const cardCount = await historyCards.count();
if (cardCount === 0) {
  // Empty state — verify tab panel visible
  await expect(page.locator("[role='tabpanel']")).toBeVisible({ timeout: 15_000 });
} else {
  await expect(historyCards.first()).toBeVisible({ timeout: 15_000 });
}
```

**Quy tắc chung:** Khi test màn chi tiết (Detail/View) có tab section, **bắt buộc inspect DOM thực tế** qua ui-debug-agent trước khi viết locator cho tab content — KHÔNG assume là `<table>`.

---

## 14. Tab panel — Next button disabled khi chỉ có 1 trang

**Rule:** Khi assert "trang cuối - Next disabled" trong pagination, nếu `btnNextPage` có thể không visible (danh sách chỉ có 1 trang):

```typescript
// SAI — có thể fail nếu pagination không render khi chỉ có 1 trang
await expect(listPage.btnNextPage).toBeDisabled();

// ĐÚNG — kiểm tra visibility trước khi assert
const nextVisible = await listPage.btnNextPage.isVisible().catch(() => false);
if (nextVisible) {
  await expect(listPage.btnNextPage).toBeDisabled();
} else {
  // Không có pagination control = hệ thống ẩn khi chỉ có 1 trang → OK
}
```

---

## 13. Playwright Chromium và VPN Proxy-mode

Playwright launch Chromium fresh, **không dùng system proxy** mặc định. Nếu VPN proxy-mode (không phải full-tunnel), terminal và Playwright không qua VPN dù browser thường vào được.

**Verify trước khi chạy:** `curl -I https://<domain>` — phải trả về HTTP status, không timeout.

**Fix:**
```bash
# Option 1: Set proxy env cho terminal + Playwright
export HTTPS_PROXY=http://127.0.0.1:<PORT>   # PORT từ System Preferences > Network > Proxies
HTTPS_PROXY=... VPN=1 npx playwright test ...

# Option 2: playwright.config.ts đọc env
use: {
  ...(process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {}),
}

# Option 3: VPN full-tunnel mode (route toàn bộ traffic, khuyến nghị)
```
