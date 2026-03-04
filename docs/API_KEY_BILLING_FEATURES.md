# API-Key Billing Features (VNSO)

Tài liệu tổng hợp các chức năng đã triển khai cho gói dùng API-key, kèm đường dẫn thao tác từ trang chủ.

## 1) Bắt đầu từ trang chủ

- Truy cập: https://ai.vnso.vn/
- Đăng nhập bằng tài khoản người dùng hoặc admin.

## 2) Luồng cho **User** (Developer/API consumer)

### 2.1 Vào Developer Console

**Cách đi từ trang chủ:**

1. Từ màn hình chat, mở menu người dùng (avatar góc trên phải / dưới sidebar).
2. Chọn **API Platform**.
3. Hệ thống mở trang: `/developer/api-keys`

**Link trực tiếp:**
- https://ai.vnso.vn/developer/api-keys

### 2.2 Các tab/chức năng trong Developer Console (`/developer/api-keys`)

- **Overview**
  - Xem API key, copy/regenerate key
  - Xem credits, monthly requests, total requests
  - Xem usage summary và chart
  - Xem workflow pipeline (Choose plan → Add credits → Processing → Track)

- **Top Up**
  - Chọn payment account
  - Nhập số tiền, currency, transaction ref, note
  - Gửi yêu cầu nạp tiền
  - Hiển thị trạng thái xử lý:
    - Auto-approve (duyệt tự động)
    - Hoặc manual admin approval (duyệt thủ công)

- **Invoices**
  - Xem lịch sử invoice
  - Export invoice PDF

### 2.3 Trang Pricing

**Cách đi từ trang chủ:**

1. Ở sidebar trái, bấm nút **Upgrade plan** (đã thêm theo phong cách ChatGPT).
2. Hoặc vào Developer Console rồi mở Pricing.

**Link trực tiếp:**
- https://ai.vnso.vn/developer/api-keys/pricing

### 2.4 Trang Guide

- Link trực tiếp: https://ai.vnso.vn/developer/api-keys/guide
- Nội dung: hướng dẫn tích hợp, flow thanh toán, các endpoint chính.

## 3) Luồng cho **Admin**

### 3.1 Vào Billing Admin

**Cách đi từ trang chủ:**

1. Mở menu người dùng.
2. Chọn **Admin Panel**.
3. Vào mục **Billing**.
4. Hệ thống mở trang: `/admin/api-keys`

**Link trực tiếp:**
- https://ai.vnso.vn/admin/api-keys

### 3.2 Chức năng chính ở Billing Admin (`/admin/api-keys`)

- **Keys**
  - Quản lý API keys người dùng
  - Suspend/activate key
  - Cộng/trừ credits thủ công

- **Pricing**
  - Quản lý plan
  - Quản lý model pricing theo token/request

- **Payments**
  - Tạo payment account (Generic/Stripe/VNPay/MoMo)
  - Cấu hình webhook secret
  - Xem danh sách payment accounts
  - **Billing Workflow Automation**
    - Toggle `Auto-Approve Topups` ON/OFF

- **Topups**
  - Duyệt/từ chối top-up pending

- **Analytics**
  - Revenue chart
  - Usage charts theo ngày/model

- **Audit**
  - Nhật ký thao tác billing

## 4) Cơ chế duyệt top-up hiện tại

- Có **2 mode**:
  1. **Auto-approve ON**: khi user submit top-up, hệ thống tự duyệt + cộng credits + tạo invoice ngay.
  2. **Auto-approve OFF**: top-up ở trạng thái `pending`, admin duyệt thủ công.

- Cấu hình tại:
  - `/admin/api-keys` → tab **Payments** → `Billing Workflow Automation`.

## 5) Account signup có phải chờ admin duyệt không?

- Luồng signup user **không chờ admin duyệt** ở flow mặc định.
- User tạo tài khoản xong có thể đăng nhập ngay (trừ khi hệ thống bật các chính sách khác ở tầng auth/deployment).

## 6) Theme mode ở headbar

Đã thêm 3 nút mode tại:

- Headbar trong trang chat
- Trang đăng nhập/đăng ký (`/auth`)

Các mode:
- Light
- Dark
- System

## 7) i18n

OpenWebUI đã có i18n sẵn (Svelte `getContext('i18n')` + `$i18n.t(...)`), các màn hình billing/developer/admin đang dùng cùng cơ chế này.
