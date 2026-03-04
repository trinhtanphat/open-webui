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
3. Hoặc bấm nút **Developer Console** trên sidebar (icon `</>`, xuất hiện khi user có quyền API keys).
4. Hệ thống mở trang: `/developer/api-keys`

**Link trực tiếp:**
- https://ai.vnso.vn/developer/api-keys

### 2.2 Các tab/chức năng trong Developer Console (`/developer/api-keys`)

- **Overview**
  - Xem API key (mặc định ẩn `sk-***`, bấm 👁 để hiện/ẩn, bấm copy/regenerate)
  - Xem credits, monthly requests, total requests
  - **Low Balance Warning**: tự động hiện cảnh báo khi credits < 100, có nút Top Up Now
  - **Quick Start**: hiển thị curl endpoint mẫu, Base URL
  - Xem usage summary và chart
  - Chọn cửa sổ dữ liệu chart: **7d / 30d / 90d**
  - Xem workflow pipeline (Choose plan → Add credits → Processing → Track)

- **Top Up**
  - Chọn payment account (có **icon/logo** cho từng provider: Stripe, VNPay, MoMo, PayPal, Bank Transfer, Generic)
  - Có preset số tiền nhanh: **$10 / $25 / $50 / $100 / $250**
  - Nhập số tiền, **currency select dropdown** (USD/VND/EUR/GBP/JPY/CNY/KRW/SGD/THB)
  - Currency tự động lấy default từ admin settings
  - Nhập transaction ref, note
  - Lọc lịch sử top-up theo trạng thái: **All / Pending / Approved / Rejected**
  - Gửi yêu cầu nạp tiền
  - Hiển thị trạng thái xử lý:
    - Auto-approve (duyệt tự động)
    - Hoặc manual admin approval (duyệt thủ công)

- **Invoices**
  - Xem lịch sử invoice
  - Lọc invoice theo trạng thái: **All / Paid / Pending / Rejected**
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
  - Tạo payment account (Generic/Bank Transfer/Stripe/VNPay/MoMo/PayPal)
  - **Icon preview** cho từng provider khi chọn
  - Cấu hình webhook secret
  - Xem danh sách payment accounts (có **icon/logo** provider)
  - **Billing Workflow Automation**
    - Toggle `Auto-Approve Topups` ON/OFF
  - **Default Currency Setting**
    - Chọn currency mặc định cho hệ thống (USD/VND/EUR/GBP/JPY/CNY/KRW/SGD/THB)
    - User sẽ tự động thấy currency này trong form top-up

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

## 7) Sidebar enhancements

### 7.1 User Role Badge
- Sidebar hiển thị **role badge** bên cạnh tên user (Admin/User/Pending).
- Admin: badge tím, User: badge xám, Pending: badge cam.

### 7.2 Developer Console Button
- Sidebar có nút **Developer Console** (icon `</>`) dẫn thẳng tới `/developer/api-keys`.
- Chỉ hiện khi user có quyền API keys hoặc là admin.

### 7.3 Upgrade Plan Button
- Sidebar có nút **Upgrade plan** (gradient tím) dẫn tới `/developer/api-keys/pricing`.

## 8) Payment Provider Icons (Logo)

Các provider đã có icon/logo riêng:
- **Stripe** — logo tím với chữ S
- **VNPay** — logo xanh dương
- **MoMo** — logo hồng (circle)
- **PayPal** — logo xanh đậm  
- **Bank Transfer** — icon ngân hàng cổ điển
- **Generic** — icon thẻ tín dụng

Hiển thị tại:
- User: dropdown chọn payment account, card thông tin chi tiết
- Admin: dropdown tạo account (có preview), danh sách accounts

## 9) i18n

OpenWebUI đã có i18n sẵn (Svelte `getContext('i18n')` + `$i18n.t(...)`), các màn hình billing/developer/admin đang dùng cùng cơ chế này.

## 10) Email Notifications (SMTP)

### 10.1 Cấu hình SMTP

**Cách đi từ trang chủ:**
1. Admin Panel → Billing → tab **Email**
2. Nhập SMTP Host, Port, Username, Password, From Address
3. Bật/tắt TLS, Enable Billing Emails
4. Bấm **Save SMTP Settings** → **Send Test Email** để kiểm tra

**Environment Variables (alternative):**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com
SMTP_TLS=True
ENABLE_BILLING_EMAILS=True
```

### 10.2 Các loại email tự động

| Sự kiện | Người nhận | Mô tả |
|---------|-----------|-------|
| Top-up Submitted | User + Admin | Xác nhận yêu cầu nạp tiền đã được gửi |
| Top-up Approved | User | Thông báo đã duyệt + credits đã cộng |
| Top-up Rejected | User | Thông báo từ chối + lý do |
| Invoice Issued | User | Chi tiết hóa đơn sau khi thanh toán |
| Low Credits | User | Cảnh báo credits sắp hết |
| Admin Alert | Admin | Thông báo có yêu cầu nạp tiền mới cần duyệt |

### 10.3 Gmail Quick Setup

- SMTP Host: `smtp.gmail.com`
- Port: `587`
- TLS: ✓
- Dùng **App Password** từ Google Account → Security → App passwords

## 11) Currency với Country Flags 🏳️

Tất cả dropdown chọn currency đều hiển thị cờ quốc gia:

| Currency | Flag |
|----------|------|
| USD | 🇺🇸 |
| VND | 🇻🇳 |
| EUR | 🇪🇺 |
| GBP | 🇬🇧 |
| JPY | 🇯🇵 |
| CNY | 🇨🇳 |
| KRW | 🇰🇷 |
| SGD | 🇸🇬 |
| THB | 🇹🇭 |
| AUD | 🇦🇺 |
| CAD | 🇨🇦 |
| INR | 🇮🇳 |
| MYR | 🇲🇾 |
| PHP | 🇵🇭 |
| IDR | 🇮🇩 |
| TWD | 🇹🇼 |
| HKD | 🇭🇰 |
| CHF | 🇨🇭 |
| BRL | 🇧🇷 |

Hiển thị tại:
- User: Top-up form currency dropdown
- Admin: Default currency dropdown
- Admin: Model pricing currency dropdown (đã chuyển từ text input sang dropdown)

## 12) Registration + Payment Workflow (Pipeline)

### 12.1 Toàn bộ luồng từ đăng ký đến sử dụng API

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRATION FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. User truy cập https://ai.vnso.vn/auth                       │
│ 2. Chọn "Sign up" → nhập Name, Email, Password                 │
│ 3. Tạo tài khoản thành công → đăng nhập tự động               │
│ 4. User thấy giao diện chat                                    │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  API KEY ACTIVATION                              │
├─────────────────────────────────────────────────────────────────┤
│ 5. Sidebar → "Developer Console" hoặc menu → "API Platform"    │
│ 6. Bấm "Activate API Key" → chọn plan (Starter/Pro/Business)   │
│ 7. Hệ thống tạo API key: sk-xxxx...xxxx (51 chars)             │
│ 8. Key chỉ hiển thị ĐẦY ĐỦ 1 lần → copy & lưu                │
│ 9. Sau đó chỉ thấy key masked: sk-abc1***...                   │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PAYMENT / TOP-UP                              │
├─────────────────────────────────────────────────────────────────┤
│ 10. Kéo xuống phần "Top Up Balance"                             │
│ 11. Chọn Payment Account (Bank Transfer / MoMo / VNPay...)      │
│ 12. Chọn preset ($10/$25/$50/$100/$250) hoặc nhập tùy ý        │
│ 13. Chọn currency (🇻🇳 VND / 🇺🇸 USD / ...)                     │
│ 14. Nhập Transaction Reference (mã giao dịch ngân hàng)        │
│ 15. Bấm "Submit Top-up Request"                                │
│                                                                 │
│ ┌─────────────────────────────────────────────────┐             │
│ │ AUTO-APPROVE = ON?                              │             │
│ │   ✓ → Tự động cộng credits + tạo invoice        │             │
│ │   ✗ → Status = "pending" → chờ admin duyệt      │             │
│ └─────────────────────────────────────────────────┘             │
│                                                                 │
│ 📧 Email notifications (nếu SMTP configured):                  │
│   - User nhận email xác nhận đã gửi yêu cầu                   │
│   - Admin nhận email có yêu cầu nạp tiền mới                   │
│   - User nhận email khi được duyệt/từ chối                     │
│   - User nhận invoice email                                     │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API USAGE                                     │
├─────────────────────────────────────────────────────────────────┤
│ 16. User dùng API key gọi endpoint:                             │
│     curl https://ai.vnso.vn/api/chat/completions \              │
│       -H "Authorization: Bearer sk-xxxx..." \                   │
│       -d '{"model":"gpt-4o","messages":[...]}'                  │
│                                                                 │
│ 17. Hệ thống trừ credits theo model pricing                    │
│ 18. User theo dõi usage trong Developer Console:                │
│     - Daily Usage chart (7d/14d/30d/90d)                        │
│     - By Model chart                                            │
│     - Usage summary (total requests, total spend)               │
│                                                                 │
│ ⚠️ Credits < 100 → Low Balance Warning hiện + email cảnh báo   │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Admin Workflow (Duyệt thủ công)

```
Admin nhận 📧 email "New Top-up Request"
    │
    ▼
Admin Panel → Billing → tab "Top-ups"
    │
    ├── Approve → nhập credits → cộng credits + tạo invoice
    │                → User nhận 📧 "Top-up Approved" + "Invoice"
    │
    └── Reject → nhập lý do → từ chối
                     → User nhận 📧 "Top-up Rejected"
```

## 13) Tổng hợp Admin có những gì

### Admin Billing Dashboard (`/admin/api-keys`)

| Tab | Chức năng |
|-----|----------|
| **API Keys** | Quản lý keys tất cả user, suspend/activate, +/- credits thủ công |
| **Pricing** | Published Plans (Starter/Pro/Business), Model Pricing CRUD (input/output/request cost) |
| **Payments** | Tạo/quản lý Payment Accounts, Auto-Approve toggle, Default Currency setting |
| **Top-ups** | Xem/duyệt/từ chối yêu cầu nạp tiền pending |
| **Analytics** | Daily Usage charts (30d), Usage by Model charts, Revenue Daily table, Usage tables |
| **Audit** | Audit trail - log mọi thao tác billing (who/what/when) |
| **Email** | SMTP config, Test email, Enable/disable billing emails |

### Dashboard Summary Cards
- Total Active Keys
- Total Credits
- Total Requests
- Revenue

### Các tính năng khác của Admin (ngoài billing)
- User management (tạo/sửa/xóa user)
- Model management (cấu hình Ollama/OpenAI models)
- System settings (auth, OAuth, LDAP)
- Chat access control
- Analytics dashboard (chung)
- Export/Import data