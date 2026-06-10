# Deliver Evidence & Report lên Google Drive

> Sinh HTML report từ evidence local → upload lên Google Drive theo cấu trúc `env > portal > module > feature` → xoá local để tránh nặng máy.

## Input — tự động, không hỏi user

Resolve theo thứ tự ưu tiên, **không hỏi user**:

| Biến | Cách lấy tự động |
|---|---|
| `mdPath` | Đọc từ `task.md` mục Handoff. Nếu không có → lấy file `.md` mới nhất trong `testcase/`. Nếu nhiều file → lấy file được modified gần nhất. |
| `env` | Đọc từ `task.md` → fallback `uat` |
| `portal` | Đọc từ `task.md` → fallback `admin` |
| `module` | Tên thư mục cha trong `testcase/<portal>/` → fallback tên file bỏ prefix |
| `featureName` | Tên file md bỏ `KBKT_UAT_` và đuôi |
| `runDate` | Ngày hôm nay `YYYY-MM-DD` |

**Evidence path local** (đã có cấu trúc sẵn):
```
evidence/<env>/<portal>/<module>/<function>/
  [TC-01][tc-name][step].png
  [TC-01][tc-name][step2].png
  [TC-02][tc-name][step].png
  <slug>_api-calls.json
  <slug>_main-api-response.json
  ...
```
VD: `evidence/uat/admin/user-management/tao-moi/`

**Lưu ý:** Không có subfolder per TC — tất cả TC của cùng module/function nằm chung 1 thư mục, phân biệt qua tên file `[TC-ID][...]`.

---

## Drive Root

Root folder cố định: **TPcoms_UAT** (ID: `1IjokBTRNG6GYG9nyirImDRZi5aTSPZWz`)

Cấu trúc folder:

```
TPcoms_UAT/              ← root (ID cố định)
└── <ENV>/               ← VD: uat
    └── <portal>/        ← VD: admin
        └── <module>/    ← VD: TinTuc
            └── <feature>/  ← VD: ThemMoiTinTuc
```

---

## Các bước thực hiện

### Bước 1 — Kiểm tra evidence (theo `report_rules.md § 5`)

Trước khi gen report, scan `evidence/<env>/<portal>/<module>/<feature>/` và log những gì còn thiếu (không dừng, chỉ ghi nhận):

- Mỗi TC có `TC-XX_network-log.json`?
- TC xem danh sách: có `TC-XX_data-mapping.json` + `TC-XX_api-response.json`?
- TC tìm kiếm: có `TC-XX_search-count.json` + `TC-XX_api-response.json`?
- TC lọc: có `TC-XX_filter-count.json` + `TC-XX_api-response.json`?

Ghi thiếu vào `pipeline_report.md` dưới dạng cảnh báo ⚠️, sau đó tiếp tục.

---

### Bước 2 — Sinh HTML report

```bash
npx ts-node scripts/generate-report.ts <mdPath> <env> "<portal>"
```

Kiểm tra output file tồn tại trong `report/`. Nếu lỗi → dừng, báo user.

---

### Bước 3 — Tạo cấu trúc thư mục trên Drive

Sử dụng **Google Drive MCP** (`mcp__claude_ai_Google_Drive__*`).

Thứ tự tạo từng tầng (search trước → tạo nếu chưa có):

1. **ENV folder** — parent: `1IjokBTRNG6GYG9nyirImDRZi5aTSPZWz`
2. **portal folder** — parent: ENV folder ID
3. **module folder** — parent: portal folder ID
4. **feature folder** — parent: module folder ID

**Với mỗi folder:**
1. `search_files` query: `title = '<tên>' and mimeType = 'application/vnd.google-apps.folder' and parentId = '<parent_id>'`
2. Nếu chưa có → `create_file` với `mimeType: 'application/vnd.google-apps.folder'`
3. Lưu lại folder ID để dùng cho tầng tiếp theo

---

### Bước 4 — Upload HTML report

Đọc file HTML đã sinh bằng `Read` tool → lấy toàn bộ nội dung.

Upload bằng:
```
mcp__claude_ai_Google_Drive__create_file:
  title: "<Feature>_<YYYY-MM-DD>.html"
  textContent: <nội dung HTML>
  contentMimeType: "text/html"
  disableConversionToGoogleType: true
  parentId: <feature folder ID>
```

Ghi lại Drive file URL trả về.

---

### Bước 5 — Xoá local files

Chỉ xoá sau khi upload thành công (có file ID trả về):

```bash
rm -rf evidence/<env>/<portal>/<module>/<featureName>/
rm -rf report/
```

Chỉ xoá đúng thư mục feature vừa upload — **không xoá toàn bộ `evidence/`** để tránh mất evidence của feature khác.

Không xoá nếu upload chưa có file ID (tránh mất data khi lỗi).

---

### Bước 6 — Report kết quả

Báo user:

```
## Đã upload lên Google Drive ✅

📁 Đường dẫn: TPcoms_UAT > <ENV> > <portal> > <module> > <feature>
📄 Report: <Drive file URL>

🗑️ Local files đã xoá:
   - evidence/ (N TC, M screenshots)
   - report/<filename>.html

Truy cập Drive để xem report: <folder URL>
```

---

## Lưu ý

- **KHÔNG xoá local** nếu Drive upload fail (không có file ID trả về)
- HTML report đã embed toàn bộ screenshots — không cần upload evidence riêng
- Nếu folder đã tồn tại (cùng tên) → dùng folder cũ, **không** tạo duplicate
- File HTML upload với `disableConversionToGoogleType: true` để giữ định dạng HTML
