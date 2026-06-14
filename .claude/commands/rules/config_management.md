# Quy Tắc Quản Lý Config (Môi trường · Account · URL)

> Một file config DUY NHẤT gói toàn bộ: nhiều môi trường (dev/staging/prod), nhiều loại account (admin/user/guest), base URL. Secret (password/token) KHÔNG nằm trong file này — chỉ tham chiếu qua biến `.env`.

## 1. Vị trí & vai trò

- File: `config/test.config.json` (gốc project, cạnh test).
- **Code chạy đọc lúc runtime** (khác locator repository — cái đó agent đọc lúc sinh code). Test gọi `config.accounts.admin`, `config.environments[env].baseURL`.
- Commit được vào git (KHÔNG chứa secret thật).

## 2. Cấu trúc (JSON — đồng bộ với locator repository)

```json
{
  "environments": {
    "dev":     { "baseURL": "https://dev.crm.example.com" },
    "staging": { "baseURL": "https://staging.crm.example.com" },
    "prod":    { "baseURL": "https://crm.anhtester.com" }
  },
  "accounts": {
    "admin": { "username": "admin@example.com", "password": "${ADMIN_PASSWORD}", "role": "admin" },
    "user":  { "username": "user@example.com",  "password": "${USER_PASSWORD}",  "role": "user" },
    "guest": { "username": "guest@example.com", "password": "${GUEST_PASSWORD}", "role": "guest" }
  },
  "activeEnv": "staging",
  "timeouts": { "slowEnv": false }
}
```

- Đổi môi trường: sửa `activeEnv` hoặc set biến `ENV=staging` lúc chạy.
- `timeouts.slowEnv: true` (hoặc biến `VPN=1`) → nâng timeout theo `playwright_rules.md` mục 9.
- `baseURL` dùng chung với `playwright.config.ts` (`use: { baseURL: cfg.environments[env].baseURL }`).

## 3. Secret — KHÔNG để giá trị thật trong config (CRITICAL)

- Password/token trong config CHỈ là **tên biến**: `"password": "${ADMIN_PASSWORD}"`.
- Giá trị thật nằm trong `.env` (đã `.gitignore`):
  ```
  ADMIN_PASSWORD=...
  USER_PASSWORD=...
  GUEST_PASSWORD=...
  ```
- Lúc chạy, code resolve `${ADMIN_PASSWORD}` từ `process.env`. Tuân thủ `CLAUDE.md` mục an toàn dữ liệu: KHÔNG hardcode credentials, KHÔNG commit file chứa secret, KHÔNG in ra chat.
- Phải có `config/test.config.example.json` (mẫu, commit được) + `.env.example` (chỉ tên biến, không giá trị) để team biết cần điền gì.

## 4. Cách test dùng config

```typescript
// config.ts — load + resolve ${VAR}
import cfg from './config/test.config.json';
const env = process.env.ENV || cfg.activeEnv;
export const baseURL = cfg.environments[env].baseURL;
export function account(name: 'admin'|'user'|'guest') {
  const a = cfg.accounts[name];
  const pwd = a.password.replace(/^\$\{(.+)\}$/, (_, v) => process.env[v] || '');
  return { username: a.username, password: pwd, role: a.role };
}

// test dùng:
const admin = account('admin');
await loginPage.login(admin.username, admin.password);
```

## 5. Quan hệ với các phần khác

| Dữ liệu | Lưu ở đâu |
|---|---|
| Môi trường, base URL, account (username), role | `config/test.config.json` |
| Password / token (giá trị thật) | `.env` (gitignore) |
| Locator theo màn | `output/locators/<screen>.screen.json` |
| Test data động (email random...) | sinh runtime qua `test-data-generator` |

Đừng trộn: config = cố định + bí mật-tham-chiếu; test data = sinh động per-run; locator = element map.
