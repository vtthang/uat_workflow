# Report Rules — API Response & Data Evidence

> Áp dụng khi sinh report cho mọi tính năng. Kết hợp với `test_execution_rules.md § 12e` (capture pattern).

---

## 1. Cấu trúc JSON evidence bắt buộc

Mỗi TC phải lưu đủ các file JSON vào `evidence/<env>/<portal>/<module>/<function>/`:

| File | TC type | Sinh bởi | Nội dung |
|---|---|---|---|
| `TC-LIST-01_api-calls.json` | **Mọi TC** | `teardownApiMonitor` (auto) | Tất cả API calls; main API entry có thêm `responseBody` |
| `TC-LIST-01_data-mapping.json` | TC danh sách / chi tiết | Test code (manual) | fields[], mỗi field: field, apiValue, uiDisplay, match |
| `TC-LIST-02_search-count.json` | TC tìm kiếm (kể cả không có kết quả) | Test code (manual) | keyword, apiTotal, uiRowCount, note |
| `TC-LIST-06_filter-count.json` | TC lọc | Test code (manual) | filter, apiTotal, uiRowCount, note |

**Quan trọng:** `_search-count.json` và `_filter-count.json` bắt buộc có kể cả khi `apiTotal = 0`.

---

## 2. Cấu trúc từng file

### `api-calls.json` (auto — `teardownApiMonitor`)
```json
[
  { "method": "GET", "url": "https://.../me/userinfo", "status": 200, "time": 1749470894948 },
  { "method": "GET", "url": "https://.../admin-members?page=0&size=10", "status": 200, "time": 1749470895001,
    "responseBody": { "page": 0, "size": 10, "totalItems": 100, "items": [...] }
  }
]
```
- Sinh tự động bởi `teardownApiMonitor` — tên file: `{tcId}_api-calls.json`
- Main API entry có thêm `responseBody` (phân biệt qua `entry.responseBody != null`)
- TC ID theo format `TC-{FUNC}-{NN}` (xem `html_report_rules.md` mục 1)

### `data-mapping.json`
```json
{
  "tcId": "TC-LIST-01",
  "fields": [
    { "field": "Họ tên",    "apiValue": "Nguyễn Văn A",  "uiDisplay": "Nguyễn Văn A",  "match": true },
    { "field": "Email",     "apiValue": "a@example.com", "uiDisplay": "a@example.com", "match": true },
    { "field": "Trạng thái","apiValue": "ACTIVE",        "uiDisplay": "Kích hoạt",     "match": true }
  ]
}
```
> Capture từ row đầu tiên (TC danh sách) hoặc toàn bộ fields (TC chi tiết).  
> `apiValue` = giá trị thô từ API response; `uiDisplay` = text hiển thị trên UI.

### `search-count.json`
```json
{
  "tcId": "TC-LIST-02",
  "keyword": "từ khóa",
  "apiTotal": 5,
  "uiRowCount": 5,
  "note": "UI hiển thị 5/5 kết quả (trang 1)"
}
```
> Case không có kết quả: `apiTotal: 0, uiRowCount: 0, note: "API total: 0 — empty state hiển thị đúng"`

### `filter-count.json`
```json
{
  "tcId": "TC-LIST-06",
  "filter": "Trạng thái: Kích hoạt",
  "apiTotal": 85,
  "uiRowCount": 10,
  "note": "API total: 85 | UI hiển thị: 10 (trang 1)"
}
```

---

## 3. API Calls log — sinh tự động qua `setupApiMonitor` + `teardownApiMonitor`

> Xem chi tiết pattern tại `test_execution_rules.md` §12 và `automation_rules.md` §12.

**Setup trong `beforeEach`:**
```typescript
import { setupApiMonitor, teardownApiMonitor, ApiLogEntry } from '../../src/utils/ApiMonitor';

const EVIDENCE_DIR = 'evidence/uat/admin/<module>/<function>';
const apiLog: ApiLogEntry[] = [];
const isMainApi = (res: { url(): string; request(): { method(): string } }) =>
  /\/admin-members/.test(res.url()) && res.request().method() === 'GET';

test.beforeEach(async ({ page }) => {
  apiLog.length = 0;
  setupApiMonitor(page, apiLog, isMainApi);
});
```

**Teardown trong `afterEach`:**
```typescript
test.afterEach(async ({}, testInfo) => {
  await teardownApiMonitor(apiLog, testInfo, EVIDENCE_DIR);
  // Ghi: <EVIDENCE_DIR>/TC-LIST-01_api-calls.json
  // TC ID extract bằng regex /TC-[A-Z]+-\d+/i từ testInfo.title
});
```

**Test title PHẢI bắt đầu bằng TC ID** để teardownApiMonitor extract đúng:
```typescript
test('TC-LIST-01 Danh sách hiển thị đúng khi có dữ liệu', async ({}) => { ... });
test('TC-CREATE-01 Tạo tài khoản thành công', async ({}) => { ... });
```

---

## 4. Report generator — xem `html_report_rules.md`

> Toàn bộ spec sinh HTML report (cấu trúc, TC card, API Calls table, count-box, Response body, embedding ảnh base64) được mô tả trong `html_report_rules.md`.

Tóm tắt mapping evidence → HTML:

| File evidence | Render trong TC card |
|---|---|
| `{tcId}_api-calls.json` | API Calls table; entry có `responseBody` → isMain row highlight tím + badge MAIN + `<details>` Response body |
| `{tcId}_data-mapping.json` | Data Mapping table: Field / Giá trị API / Hiển thị UI / Khớp (list/detail TCs) |
| `{tcId}_search-count.json` | count-box: Keyword + API total + UI rows + note |
| `{tcId}_filter-count.json` | count-box: Filter + API total + UI rows + note |
| `[{tcId}][{stepLabel}].png` | Screenshots carousel (embed base64) — zoom 75% trước khi chụp |

**Thứ tự render trong TC body:**
```
1. Screenshots carousel
2. API Calls table
3. count-box (search/filter TCs)
4. Data Mapping table (list/detail TCs)
5. Response body collapsible
```

---

## 5. Checklist trước khi gen report

- [ ] Mỗi TC có `{tcId}_api-calls.json` (sinh tự động qua `teardownApiMonitor`)
- [ ] TC danh sách / chi tiết: có `{tcId}_data-mapping.json` (field / apiValue / uiDisplay / match)
- [ ] TC tìm kiếm (kể cả không có kết quả): có `{tcId}_search-count.json`
- [ ] TC lọc: có `{tcId}_filter-count.json`
- [ ] Test title bắt đầu bằng TC ID đúng format `TC-{FUNC}-{NN}`

