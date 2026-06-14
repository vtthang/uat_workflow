# HTML Report Rules — UAT Evidence Report

> Quy tắc sinh file HTML report tự chứa (self-contained) từ evidence JSON + screenshots sau khi chạy test.
> Dùng kết hợp với `report_rules.md` (evidence capture) và `test_execution_rules.md` (screenshot).

---

## 1. TC ID Format — chuẩn function-based

**Format:** `TC-{FUNC}-{NN}` (dấu gạch ngang, viết hoa FUNC, NN bắt đầu từ 01)

| Chức năng | FUNC | Ví dụ |
|---|---|---|
| Xem danh sách / tìm kiếm / lọc / sort | `LIST` | `TC-LIST-01` |
| Tạo mới | `CREATE` | `TC-CREATE-01` |
| Xem chi tiết | `DETAIL` | `TC-DETAIL-01` |
| Kích hoạt / Vô hiệu hóa | `TOGGLE` | `TC-TOGGLE-01` |
| Cập nhật / Sửa | `UPDATE` | `TC-UPDATE-01` |
| Lịch sử thay đổi | `HISTORY` | `TC-HISTORY-01` |
| Reset mật khẩu | `RESET` | `TC-RESET-01` |
| Phân quyền | `PERM` | `TC-PERM-01` |
| Xóa | `DELETE` | `TC-DELETE-01` |

**Quy tắc:**
- `tcId` trong evidence JSON phải khớp với ID trong TC card HTML.
- Test file dùng `tcId` này khi gọi `BasePage.screenshot(tcId, ...)` và ghi evidence JSON.
- FUNC xác định theo nghiệp vụ của TC, không phải theo tên module.

---

## 2. Cấu trúc HTML tổng thể

```
report.html (self-contained — ảnh embed base64, không cần file ngoài)
├── <head>  CSS inline
├── <nav class="top-nav">  sticky nav → link đến từng func-section
├── <div class="report-header">  tiêu đề + meta + summary-row
└── <main>
    └── <section class="func-section" id="func-{slug}">  (1 section / chức năng)
        ├── <div class="func-header">  h2 + UC code + badges PASS/SKIP/FAIL
        └── <div class="tc-list">
            └── <div class="tc-card" id="{TC-ID}">  (1 card / TC)
                ├── <div class="tc-header">  TC-ID + tên + badge
                └── <div class="tc-body">
                    ├── Screenshots carousel  (base64)
                    ├── API Calls table
                    ├── count-box  (search / filter TCs)
                    ├── Data Mapping table  (list / detail TCs)
                    └── <details> Response body  (collapsible)
```

---

## 3. Report Header

```html
<div class="report-header">
  <h1>Báo cáo UAT — {Tên tính năng}</h1>
  <div class="meta">
    Môi trường: {env} ({baseUrl}) | Portal: {portal} | Ngày chạy: {YYYY-MM-DD} | Version: 2.0
  </div>
  <div class="summary-row">
    <div class="summary-box"><div class="num">{totalTC}</div><div class="lbl">Tổng TC</div></div>
    <div class="summary-box pass"><div class="num">{pass}</div><div class="lbl">PASS</div></div>
    <div class="summary-box skip"><div class="num">{skip}</div><div class="lbl">SKIP</div></div>
    <div class="summary-box fail"><div class="num">{fail}</div><div class="lbl">FAIL</div></div>
    <div class="summary-box"><div class="num">{totalScreenshots}</div><div class="lbl">Screenshots</div></div>
    <div class="summary-box"><div class="num">{totalApiCalls}</div><div class="lbl">API Calls</div></div>
  </div>
</div>
```

**`totalApiCalls`** = tổng số entries trong tất cả `_api-calls.json` của các TC (không phải 0).

---

## 4. Func Section (1 section / chức năng)

```html
<section class="func-section" id="func-{slug}">
  <div class="func-header">
    <h2>{Tên chức năng}</h2>
    <div class="func-badges">
      <span class="badge-pass">{N} PASS</span>   <!-- chỉ render nếu > 0 -->
      <span class="badge-skip">{N} SKIP</span>   <!-- chỉ render nếu > 0 -->
      <span class="badge-fail">{N} FAIL</span>   <!-- chỉ render nếu > 0 -->
    </div>
    <span class="func-uc">{UC-CODE}</span>
  </div>
  <div class="tc-list">
    <!-- TC cards -->
  </div>
</section>
```

`slug` = chữ thường, gạch ngang, ví dụ: `func-xem-danh-sach`, `func-tao-moi`.

---

## 5. TC Card

### 5.1 Header
```html
<div class="tc-card" id="{TC-ID}">
  <div class="tc-header">
    <span class="tc-id">{TC-ID}</span>
    <span class="tc-name">{Tên TC}</span>
    <span class="tc-badge" style="background:{color}">PASS|SKIP|FAIL</span>
  </div>
```
Màu badge: PASS `#16a34a`, SKIP `#d97706`, FAIL `#dc2626`.

### 5.2 Screenshots Carousel
```html
<div class="section-title">📷 Screenshots ({N} ảnh)</div>
<div class="carousel">
  <div class="carousel-item" id="slide-{TC-ID}-{index}">
    <div class="img-label">{step-label}</div>
    <img src="data:image/png;base64,{base64}" onclick="openModal(this)" />
  </div>
  <!-- ... -->
</div>
```
- **Screenshot filename format:** `[{TC-ID}][{stepLabel}].png` (2-param: `BasePage.screenshot(tcId, stepLabel)`)
- `img-label` = phần `stepLabel` — bỏ prefix `[TC-ID]` từ tên file, giữ nội dung trong `[...]` thứ 2.
  - VD: file `[TC-LIST-01][01_list_loaded].png` → `img-label = 01_list_loaded`
- Ảnh embed base64 trực tiếp — report tự chứa, không cần thư mục ngoài.
- TC SKIP: chỉ render screenshots nếu có, không render API/Mapping.

### 5.3 API Calls Table
```html
<div class="section-title">📡 API Calls ({N})</div>
<table>
  <thead>
    <tr>
      <th style="width:60px">Method</th>
      <th>Endpoint</th>
      <th style="width:60px">Status</th>
    </tr>
  </thead>
  <tbody>
    <!-- Row thường -->
    <tr>
      <td class="method method-get">GET</td>
      <td>/api/v1/iam/me/userinfo</td>
      <td style="color:#16a34a">200</td>
    </tr>
    <!-- Row isMain — highlight tím -->
    <tr style="background:#f5f3ff">
      <td class="method method-get">GET</td>
      <td>
        /api/v1/iam/admin-members
        <span style="color:#94a3b8">?page=0&size=10</span>
        <span style="background:#7c3aed;color:#fff;font-size:9px;padding:1px 5px;border-radius:3px">MAIN</span>
      </td>
      <td style="color:#16a34a">200</td>
    </tr>
  </tbody>
</table>
```

**Quy tắc API Calls table:**
- **3 cột**: Method | Endpoint | Status. Không có cột isMain hay Timing riêng.
- **isMain rows**: highlight `background:#f5f3ff` (tím nhạt) + badge `MAIN` màu `#7c3aed` ngay sau endpoint.
- Endpoint: phần path trước `?` màu đen; query params màu `#94a3b8` (muted).
- Màu Method: GET `#2563eb`, POST `#059669`, PUT/PATCH `#d97706`, DELETE `#dc2626`.
- Status 2xx: `#16a34a` (xanh); 4xx/5xx: `#dc2626` (đỏ).
- Nguồn dữ liệu: `{tcId}_api-calls.json` → field `calls[]`.

### 5.4 count-box (TC tìm kiếm và lọc)
```html
<!-- Tìm kiếm -->
<div class="count-box">
  <span class="count-label">Keyword:</span> <code>{keyword}</code>
  &nbsp;&nbsp;
  <span class="count-label">API total:</span> <b style="color:#2563eb">{apiTotal}</b>
  &nbsp;&nbsp;
  <span class="count-label">UI rows:</span> <b>{uiRowCount}</b>
  &nbsp;&nbsp;
  <span style="color:#16a34a;font-weight:700">{note}</span>
</div>

<!-- Lọc -->
<div class="count-box">
  <span class="count-label">Filter:</span> <code>{filterValue}</code>
  &nbsp;&nbsp;
  <span class="count-label">API total:</span> <b style="color:#2563eb">{apiTotal}</b>
  &nbsp;&nbsp;
  <span class="count-label">UI rows:</span> <b>{uiRowCount}</b>
  &nbsp;&nbsp;
  <span style="color:#16a34a;font-weight:700">{note}</span>
</div>
```
Nguồn: `{tcId}_search-count.json` hoặc `{tcId}_filter-count.json`.
Bắt buộc render kể cả khi `apiTotal = 0`.

### 5.5 Data Mapping Table (list / detail TCs)
```html
<div class="section-title">🗂️ Data Mapping ({N} fields)</div>
<table>
  <thead>
    <tr>
      <th>Field</th>
      <th>Giá trị API</th>
      <th>Hiển thị UI</th>
      <th style="width:60px">Khớp</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Họ tên</td>
      <td><code>Nguyễn Văn A</code></td>
      <td>Nguyễn Văn A</td>
      <td style="color:#16a34a;font-weight:700">✓</td>
    </tr>
    <!-- match=false: màu đỏ -->
    <tr style="background:#fef2f2">
      <td>Email</td>
      <td><code>a@example.com</code></td>
      <td>b@example.com</td>
      <td style="color:#dc2626;font-weight:700">✗</td>
    </tr>
  </tbody>
</table>
```
**Nguồn: `{tcId}_data-mapping.json`** — chỉ render cho TC loại LIST (danh sách) và DETAIL (chi tiết).
- Row `match=false`: highlight `background:#fef2f2` (đỏ nhạt), icon `✗` màu `#dc2626`.
- Row `match=true`: bình thường, icon `✓` màu `#16a34a`.
- TC không có file `_data-mapping.json` → không render section này.

### 5.6 Response Body (collapsible)
```html
<details style="margin-top:8px">
  <summary>
    <span style="color:{methodColor};font-weight:700">{METHOD}</span>
    <code style="margin:0 6px">{path}</code>
    <span style="color:{statusColor};font-weight:700">{status}</span>
    {totalItems}
  </summary>
  <pre style="background:#0f172a;color:#e2e8f0;padding:10px;border-radius:6px;font-size:11px;max-height:300px;overflow:auto;margin-top:6px">{jsonString}</pre>
</details>
```
**Nguồn: field `responseBody` trong `{tcId}_api-calls.json`** — entry nào có `responseBody` là main API entry (được `setupApiMonitor` capture khi `isMainApi(res) = true`).

- **KHÔNG** dùng file riêng `_api-response.json` hay `BasePage.saveJson`.
- Mỗi TC có thể có nhiều `<details>` nếu có nhiều main API entry (ví dụ: TC gọi cả check-email lẫn POST create).
- TC không có main API call (validation client-side, bấm hủy, v.v.) → không render section này.

---

## 6. Thứ tự hiển thị nội dung trong TC body

```
1. Screenshots carousel          — luôn có (nếu có ảnh)
2. API Calls table               — luôn có (nếu có _api-calls.json)
3. count-box                     — search/filter TCs only
4. Data Mapping table            — list/detail TCs only (nếu có _data-mapping.json)
5. Response body (collapsible)   — có entry responseBody trong _api-calls.json
```

TC SKIP: chỉ render Screenshots (nếu có). Không render API/Mapping.

---

## 7. Navigation Bar

```html
<nav class="top-nav">
  <h1>UAT — {Tên tính năng}</h1>
  <a href="#func-{slug1}">{Tên chức năng 1}</a>
  <a href="#func-{slug2}">{Tên chức năng 2}</a>
  <!-- một link / func-section -->
</nav>
```
Nav là sticky (top:0, z-index:100). Click smooth-scroll đến section tương ứng.

---

## 8. Modal Lightbox (click ảnh zoom)

```html
<div class="modal" id="modal" onclick="closeModal()">
  <span class="modal-close" onclick="closeModal()">✕</span>
  <img id="modal-img" src="" alt=""/>
</div>
<script>
function openModal(el) {
  document.getElementById('modal-img').src = el.src;
  document.getElementById('modal').classList.add('open');
}
function closeModal() {
  document.getElementById('modal').classList.remove('open');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
</script>
```

---

## 9. Quy trình sinh HTML report

### Input
```
output/evidence/
  {env}/{portal}/{module}/{function}/
    {tcId}_api-calls.json           ← auto (teardownApiMonitor); main API entry có responseBody
    {tcId}_data-mapping.json        ← manual (BasePage.saveJson) — list/detail TCs
    {tcId}_search-count.json        ← manual (BasePage.saveJson)
    {tcId}_filter-count.json        ← manual (BasePage.saveJson)
    [{tcId}][{stepLabel}].png       ← screenshots (2-param signature; zoom 75% trước khi chụp)
```

### Bước sinh
1. **Collect** — đọc tất cả file evidence theo `tcId` prefix.
2. **Group** — nhóm TC theo chức năng (LIST, CREATE, DETAIL...) → func-section.
3. **Count** — tổng PASS/SKIP/FAIL, tổng screenshots, tổng API calls (sum entries).
4. **Embed** — đọc từng ảnh PNG → `Buffer.from(fs.readFileSync(path)).toString('base64')`.
5. **Render** — sinh HTML theo cấu trúc mục 2–8.
6. **Output** — lưu `output/reports/{feature}_report_{date}.html`.

### Tên file output
```
output/reports/{TenTinhNang}_report_{YYYY-MM-DD}.html
Ví dụ: output/reports/QuanLyNguoiDung_report_2026-06-10.html
```

---

## 10. Checklist trước khi deliver HTML report

- [ ] `totalApiCalls` ≠ 0 (phải là tổng calls thực tế, không hardcode 0)
- [ ] Mọi ảnh đều embed base64 (không có `src` trỏ file ngoài)
- [ ] TC SKIP không render API/Mapping section
- [ ] isMain rows highlight tím + badge MAIN
- [ ] count-box có kể cả khi apiTotal = 0
- [ ] Nav links khớp với id của func-section
- [ ] Report tự mở được bằng cách double-click file HTML (không cần server)

---

## Cấu trúc HTML report bắt buộc (sinh bởi `scripts/gen_report.py`)

Report PHẢI có các thành phần sau (đã code sẵn trong `scripts/gen_report.py` — dùng script này, không tự bịa lại):

1. **Menu điều hướng PHÂN CẤP 2 cấp** (sidebar trái, sticky): **Tính năng (UC) > các phần trong tính năng**.
   - Cấp 1 = UC (vd "UC3. Tạo mới") → anchor `#uc{n}`.
   - Cấp 2 = phần (vd "Tạo mới", "Validate — Tạo mới") → anchor `#grp-<prefix>`.
   - Mỗi mục hiện số TC + badge đỏ số FAIL. Bấm → cuộn tới section.
2. **Bảng tổng hợp case FAIL ở ĐẦU trang** (`failbox`): liệt kê mọi TC FAIL + mô tả ngắn (actual result), mỗi dòng **link `#<TC-ID>`** → bấm điều hướng thẳng tới card case đó. Không có FAIL → hiện box xanh "Không có case FAIL".
3. **Mỗi card TC có `id="<TC-ID>"`** (để fail-summary/menu nhảy tới được) + title + Các bước + Kết quả mong muốn + Kết quả thực tế + ảnh (trước/sau) + Data Mapping mọi cột + count-box/maxlength + API Calls (fetch/xhr, main có Full response).
4. **Sắp xếp theo thứ tự UC trong SRS** (`UC_RANK` / `PARENTS` trong script).

> Lệnh: `python3 scripts/gen_report.py <testcase.md> <evidence_root> <out.html> "<title>"`. Status P/F đọc từ marker trong file testcase. Khi đổi cấu trúc report → sửa trong `scripts/gen_report.py` (single source).
