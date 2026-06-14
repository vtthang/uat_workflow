# System Knowledge — Bản đồ tính năng & quan hệ nghiệp vụ

> File tri thức tích luỹ về hệ thống. **Đọc trước khi gen testcase** một tính năng (để biết nó liên quan/ảnh hưởng tới đâu) và **cập nhật sau khi test xong** một tính năng. Xem `testcase_writing_rules.md` RULE 17.
>
> Đây KHÔNG phải output — giữ lại và gửi kèm khi chia sẻ project (đừng để vào `output/`).

## Cách dùng

1. **Trước khi gen TC tính năng X:** đọc bảng dưới → tìm các tính năng liên quan tới X (share data, chung màn, có luồng nối tiếp, ảnh hưởng trạng thái). Bổ sung TC kiểm tra ảnh hưởng chéo.
2. **Sau khi test xong tính năng X:** thêm/cập nhật 1 entry cho X theo template, ghi rõ quan hệ với các tính năng khác.

## Template entry

```
### <Tên tính năng> (module: <module>, portal: <portal>)
- **Mô tả ngắn:** ...
- **Màn hình / route:** ...
- **Dữ liệu nghiệp vụ chính:** <entity và field quan trọng>
- **Quyền truy cập:** <role nào được làm gì> (đồng bộ với permission-matrix nếu có)
- **Liên quan tới:**
  - `<tính năng khác>` — <ảnh hưởng thế nào: chung entity / nối luồng / đổi trạng thái dùng chung ...>
- **Ảnh hưởng chéo cần test:** <case kiểm tra khi tính năng này thay đổi data mà tính năng kia phụ thuộc>
- **Ngày cập nhật:** YYYY-MM-DD
```

## Bản đồ tính năng

<!-- Thêm entry mới bên dưới. Giữ thứ tự theo module. -->

_(chưa có tính năng nào được ghi nhận — sẽ được pipeline tự bổ sung sau mỗi lần test)_

### Quản lý tài khoản / người dùng (module: iam, portal: admin)
- **Mô tả ngắn:** CRUD tài khoản người dùng admin portal + phân quyền nhóm, reset mật khẩu, lịch sử thay đổi.
- **Màn hình / route:** list `/users`; detail `/users/{id}?subpage=information`; create `/users/create-account`; edit `/users/{id}/update-account`. Sidebar: "Quản lý tài khoản".
- **API chính:** list `GET /api/v1/iam/admin-members`; permissions `GET /api/v1/iam/me/permissions?functionCode=FUNC_ADMIN_USER_MGMT`; groups `GET /api/v1/iam/groups/checkbox`.
- **Dữ liệu nghiệp vụ chính:** iam.users (full_name, email, phone, department, position, language, groups, active).
- **Quyền truy cập:** chỉ PORTAL_ADMIN (admin portal). partner/customer là portal riêng → không truy cập.
- **Liên quan tới:**
  - `Nhóm phân quyền (groups)` — gán cho user; nhóm "không cho phép" ảnh hưởng quyền dùng chức năng của user.
  - `Lịch sử thay đổi (history_changes)` — mọi create/update/toggle/reset ghi log; tạo user luôn sinh ≥1 bản ghi "Tạo mới".
  - `Phiên đăng nhập` — vô hiệu hóa/reset mật khẩu → force logout session.
- **Ảnh hưởng chéo cần test:** đổi nhóm phân quyền user → ảnh hưởng quyền truy cập chức năng của user đó; vô hiệu hóa → user không đăng nhập được + bị thu hồi token.
- **Ghi chú defect:** lỗi-tải-dữ-liệu (API 500) hiển thị empty-state thay vì toast lỗi (TC-LIST-09).
- **Ngày cập nhật:** 2026-06-13
