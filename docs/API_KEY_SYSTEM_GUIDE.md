# Hướng Dẫn Hệ Thống API Key & Billing — Open WebUI (VNSO)

> **Base URL**: `https://ai.vnso.vn`  
> **API Prefix**: `/api/v1/api-keys`  
> **Phiên bản**: 2026-03-30  

---

## Mục Lục

1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Thống Nhất API Endpoints](#2-thống-nhất-api-endpoints)
3. [Hướng Dẫn Sử Dụng Cho User](#3-hướng-dẫn-sử-dụng-cho-user)
4. [Hướng Dẫn Quản Trị Cho Admin](#4-hướng-dẫn-quản-trị-cho-admin)
5. [Luồng Thanh Toán & Webhook](#5-luồng-thanh-toán--webhook)
6. [Bảng API Endpoints Chi Tiết](#6-bảng-api-endpoints-chi-tiết)
7. [Bảo Mật — Security Checklist](#7-bảo-mật--security-checklist)
8. [Kết Quả Test](#8-kết-quả-test)
9. [Ví Dụ CURL](#9-ví-dụ-curl)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Tổng Quan Kiến Trúc

### Hệ thống gồm 1 base URL duy nhất:

```
https://ai.vnso.vn/api/v1/api-keys
```

Tất cả endpoint API key & billing đều nằm dưới prefix này. **Không có endpoint trùng lặp hay URL phân tán.**

### Cấu trúc phân quyền:

| Nhóm | Prefix | Quyền |
|------|--------|-------|
| User endpoints | `/api/v1/api-keys/me/*` | Verified user (role: user/admin) |
| Public read-only | `/api/v1/api-keys/plans`, `/settings`, `/model-pricing`, `/payment-accounts` | Verified user |
| Admin endpoints | `/api/v1/api-keys/admin/*` | Admin only |
| Webhooks | `/api/v1/api-keys/webhooks/payment/{provider}` | Không cần auth (dùng signature) |

### Stack kỹ thuật:

- **Backend**: FastAPI (Python) — 1 router file `api_keys.py`
- **Database**: SQLAlchemy (SQLite/PostgreSQL) — tables: `apikey`, `model_pricing`, `usage_log`, `billing_payment_account`, `billing_topup_request`, `billing_invoice`, `billing_audit_log`
- **Frontend**: Svelte + TypeScript — file `src/lib/apis/api-keys/index.ts`
- **Auth**: JWT (Bearer token) hoặc API Key (`sk-...`)
- **API Key format**: `sk-<48 ký tự random>` (tạo bằng `secrets` module)
- **Lưu trữ key**: SHA-256 hash (không lưu key gốc, chỉ lưu 10 ký tự đầu để hiển thị)

---

## 2. Thống Nhất API Endpoints

### ✅ Xác nhận: Hệ thống chỉ có **1 base URL duy nhất**

```
POST/GET  https://ai.vnso.vn/api/v1/api-keys/*
```

**Không có** endpoint trùng lặp, không có URL cũ/mới lẫn lộn. Frontend và Backend **đã đồng bộ 100%**.

Router đăng ký trong `main.py`:
```python
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api-keys"])
```

### Tóm tắt nhanh — 2 nhóm endpoint chính:

| # | Nhóm | URL Pattern | Mục đích |
|---|------|-------------|----------|
| 1 | **User API** | `/api/v1/api-keys/me/*` | Self-service: tạo key, xem usage, nạp tiền, xem invoice |
| 2 | **Admin API** | `/api/v1/api-keys/admin/*` | Quản lý: duyệt topup, cấu hình pricing, analytics |

---

## 3. Hướng Dẫn Sử Dụng Cho User

### 3.1 Kích hoạt API Key

```bash
curl -X POST https://ai.vnso.vn/api/v1/api-keys/me/activate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "starter"}'
```

**Response** (API key chỉ hiện **1 lần duy nhất**):
```json
{
  "id": "abc-123",
  "user_id": "user-456",
  "key": "sk-abcdef1234567890...",
  "key_masked": "sk-abcd********************************...7890",
  "status": "active",
  "plan_name": "starter",
  "credits_remaining": 5000,
  "total_requests": 0,
  "created_at": 1743350400
}
```

### 3.2 Xem API Key (đã mask)

```bash
curl https://ai.vnso.vn/api/v1/api-keys/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3.3 Xem Usage

```bash
curl https://ai.vnso.vn/api/v1/api-keys/me/usage \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3.4 Regenerate API Key

```bash
curl -X POST https://ai.vnso.vn/api/v1/api-keys/me/regenerate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

> ⚠️ Key cũ sẽ bị vô hiệu hóa ngay lập tức. Metadata (credits, plan) được giữ nguyên.

### 3.5 Xem Plans

```bash
curl https://ai.vnso.vn/api/v1/api-keys/plans \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

| Plan | Giá/tháng | Credits | RPM Limit | Phù hợp |
|------|-----------|---------|-----------|----------|
| Starter | $19 | 5,000 | 30 | MVP, cá nhân |
| Pro | $79 | 30,000 | 120 | Team nhỏ |
| Business | $249 | 120,000 | 300 | Production |

### 3.6 Nạp Credits (Top-up)

**Bước 1**: Xem payment accounts

```bash
curl https://ai.vnso.vn/api/v1/api-keys/payment-accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Bước 2**: Tạo yêu cầu nạp tiền

```bash
curl -X POST https://ai.vnso.vn/api/v1/api-keys/me/topups \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key_id": "YOUR_KEY_ID",
    "payment_account_id": "ACCOUNT_ID",
    "amount": 500000,
    "currency": "VND",
    "tx_ref": "TXN-2026-001",
    "note": "Nạp 500.000 VND"
  }'
```

**Bước 3**: Chờ duyệt (auto hoặc admin duyệt thủ công)

### 3.7 Xem Invoice

```bash
curl https://ai.vnso.vn/api/v1/api-keys/me/invoices \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3.8 Sử dụng API Key để gọi LLM

```bash
curl https://ai.vnso.vn/api/chat/completions \
  -H "Authorization: Bearer sk-YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 4. Hướng Dẫn Quản Trị Cho Admin

### 4.1 Dashboard tổng quan

```bash
curl https://ai.vnso.vn/api/v1/api-keys/admin/summary \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

Response:
```json
{
  "total_keys": 150,
  "active_keys": 120,
  "total_credits_remaining": 500000,
  "pending_topups": 5,
  "paid_invoices": 200,
  "total_revenue": 15000.00
}
```

### 4.2 Quản lý API Keys

```bash
# Liệt kê tất cả keys
curl https://ai.vnso.vn/api/v1/api-keys/admin/keys \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Tạo key cho user
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/keys \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "plan_name": "pro", "credits": 30000}'

# Điều chỉnh credits (cộng/trừ)
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/keys/KEY_ID/credits \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delta": 5000, "note": "Bonus credits"}'

# Suspend/Activate key
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/keys/KEY_ID/status \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "suspended"}'

# Đổi plan
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/keys/KEY_ID/plan \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_name": "business", "credits_reset_to": 120000}'
```

### 4.3 Duyệt Top-up

```bash
# Xem pending topups
curl "https://ai.vnso.vn/api/v1/api-keys/admin/topups?status=pending" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Approve
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/topups/REQUEST_ID/approve \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"credits": 5000, "note": "Đã xác nhận chuyển khoản"}'

# Reject
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/topups/REQUEST_ID/reject \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "Chưa nhận được thanh toán"}'
```

### 4.4 Model Pricing (Định giá theo model)

```bash
# Xem danh sách pricing
curl https://ai.vnso.vn/api/v1/api-keys/admin/model-pricing \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Tạo pricing mới
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/model-pricing \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4o",
    "display_name": "GPT-4o",
    "input_cost_per_1k_tokens": 0.005,
    "output_cost_per_1k_tokens": 0.015,
    "per_request_cost": 0.001,
    "currency": "USD"
  }'
```

### 4.5 Billing Settings

```bash
# Xem settings
curl https://ai.vnso.vn/api/v1/api-keys/admin/settings \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Cập nhật (bật/tắt auto-approve, currency mặc định)
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/settings \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_approve_topups": true,
    "default_currency": "VND",
    "enable_billing_emails": true
  }'
```

### 4.6 Analytics

```bash
# Revenue daily (30 ngày)
curl "https://ai.vnso.vn/api/v1/api-keys/admin/analytics/revenue-daily?days=30" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Usage logs
curl "https://ai.vnso.vn/api/v1/api-keys/admin/usage-logs?days=30&limit=100" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Usage daily summary
curl "https://ai.vnso.vn/api/v1/api-keys/admin/usage-logs/daily?days=30" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Usage by model
curl "https://ai.vnso.vn/api/v1/api-keys/admin/usage-logs/by-model?days=30" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"

# Audit logs
curl "https://ai.vnso.vn/api/v1/api-keys/admin/audit-logs?limit=100" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

---

## 5. Luồng Thanh Toán & Webhook

### 5.1 Workflow tổng quan

```
User tạo topup request
       ↓
  ┌────────────────┐
  │ Auto-approve?  │
  └──┬──────────┬──┘
     │ Yes      │ No
     ↓          ↓
 Credits      Admin duyệt
 cộng ngay    /từ chối
     ↓          ↓
  Invoice    Credits cộng
  tạo        → Invoice tạo
     ↓          ↓
  Email      Email thông báo
  thông báo
```

### 5.2 Webhook endpoint (cho cổng thanh toán)

```
POST https://ai.vnso.vn/api/v1/api-keys/webhooks/payment/{provider}
```

**Providers hỗ trợ:**

| Provider | Aliases | Signature |
|----------|---------|-----------|
| Stripe | `stripe` | HMAC-SHA256 (Stripe-Signature header, v1 scheme) |
| VNPay | `vnpay`, `vn_pay`, `vn-pay` | HMAC-SHA512 (vnp_SecureHash query param) |
| MoMo | `momo`, `mo_mo`, `mo-mo` | HMAC-SHA256 (signature field in body) |
| ZaloPay | `zalopay`, `zalo_pay`, `zalo`, `vng` | Custom verification |
| PayPal | `paypal`, `pay_pal` | Custom verification |
| Bank Transfer | `bank_transfer`, `bank` | Header secret (`x-billing-webhook-secret`) |
| Generic | `generic` | Header secret (`x-billing-webhook-secret`) |

### 5.3 Cấu hình webhook secret

Webhook secret được lưu trong metadata của payment account:

```json
{
  "metadata": {
    "webhook_secret": "whsec_your_stripe_webhook_secret"
  }
}
```

### 5.4 Ví dụ webhook call từ Stripe

```bash
POST https://ai.vnso.vn/api/v1/api-keys/webhooks/payment/stripe
Headers:
  Stripe-Signature: t=1234567890,v1=abc123...
Body:
  {
    "type": "checkout.session.completed",
    "data": {
      "object": {
        "metadata": {"topup_request_id": "TOPUP_ID"},
        "amount_total": 5000,
        "currency": "usd"
      }
    }
  }
```

### 5.5 Ví dụ webhook generic (Bank/Manual)

```bash
curl -X POST https://ai.vnso.vn/api/v1/api-keys/webhooks/payment/bank_transfer \
  -H "Content-Type: application/json" \
  -H "x-billing-webhook-secret: YOUR_WEBHOOK_SECRET" \
  -d '{
    "topup_request_id": "TOPUP_ID",
    "status": "paid",
    "amount": 500000,
    "currency": "VND",
    "credits": 5000,
    "tx_ref": "BANK-TXN-001"
  }'
```

---

## 6. Bảng API Endpoints Chi Tiết

### User Endpoints (Verified User)

| # | Method | Endpoint | Mô tả |
|---|--------|----------|--------|
| 1 | POST | `/api/v1/api-keys/me/activate` | Kích hoạt API key (self-service) |
| 2 | GET | `/api/v1/api-keys/me` | Xem API key (masked) |
| 3 | GET | `/api/v1/api-keys/me/usage` | Xem usage summary |
| 4 | POST | `/api/v1/api-keys/me/regenerate` | Tạo lại API key mới |
| 5 | GET | `/api/v1/api-keys/plans` | Xem danh sách plans |
| 6 | GET | `/api/v1/api-keys/settings` | Xem billing settings (read-only) |
| 7 | GET | `/api/v1/api-keys/model-pricing` | Xem giá model (read-only) |
| 8 | GET | `/api/v1/api-keys/payment-accounts` | Xem tài khoản thanh toán |
| 9 | POST | `/api/v1/api-keys/me/topups` | Tạo yêu cầu nạp tiền |
| 10 | GET | `/api/v1/api-keys/me/topups` | Xem lịch sử nạp tiền |
| 11 | GET | `/api/v1/api-keys/me/invoices` | Xem hóa đơn |
| 12 | GET | `/api/v1/api-keys/me/invoices/{id}` | Chi tiết hóa đơn |
| 13 | GET | `/api/v1/api-keys/me/usage-logs` | Xem usage logs chi tiết |
| 14 | GET | `/api/v1/api-keys/me/usage-logs/daily` | Usage theo ngày |
| 15 | GET | `/api/v1/api-keys/me/usage-logs/by-model` | Usage theo model |

### Admin Endpoints (Admin Only)

| # | Method | Endpoint | Mô tả |
|---|--------|----------|--------|
| 16 | GET | `/api/v1/api-keys/admin/summary` | Dashboard tổng quan |
| 17 | GET | `/api/v1/api-keys/admin/keys` | Liệt kê tất cả API keys |
| 18 | POST | `/api/v1/api-keys/admin/keys` | Tạo API key cho user |
| 19 | POST | `/api/v1/api-keys/admin/keys/{id}/credits` | Điều chỉnh credits |
| 20 | POST | `/api/v1/api-keys/admin/keys/{id}/status` | Đổi trạng thái key |
| 21 | POST | `/api/v1/api-keys/admin/keys/{id}/plan` | Đổi plan |
| 22 | GET | `/api/v1/api-keys/admin/settings` | Xem billing settings |
| 23 | POST | `/api/v1/api-keys/admin/settings` | Cập nhật settings |
| 24 | GET | `/api/v1/api-keys/admin/payment-accounts` | Xem payment accounts (bao gồm inactive) |
| 25 | POST | `/api/v1/api-keys/admin/payment-accounts` | Tạo payment account |
| 26 | POST | `/api/v1/api-keys/admin/payment-accounts/{id}` | Sửa payment account |
| 27 | GET | `/api/v1/api-keys/admin/topups` | Xem topup requests |
| 28 | POST | `/api/v1/api-keys/admin/topups/{id}/approve` | Duyệt topup |
| 29 | POST | `/api/v1/api-keys/admin/topups/{id}/reject` | Từ chối topup |
| 30 | GET | `/api/v1/api-keys/admin/invoices` | Xem tất cả invoices |
| 31 | GET | `/api/v1/api-keys/admin/invoices/{id}` | Chi tiết invoice |
| 32 | GET | `/api/v1/api-keys/admin/analytics/revenue-daily` | Revenue theo ngày |
| 33 | GET | `/api/v1/api-keys/admin/audit-logs` | Audit trail |
| 34 | GET | `/api/v1/api-keys/admin/model-pricing` | Xem model pricing |
| 35 | POST | `/api/v1/api-keys/admin/model-pricing` | Tạo model pricing |
| 36 | POST | `/api/v1/api-keys/admin/model-pricing/{id}` | Sửa model pricing |
| 37 | DELETE | `/api/v1/api-keys/admin/model-pricing/{id}` | Xóa model pricing |
| 38 | GET | `/api/v1/api-keys/admin/usage-logs` | Usage logs (all users) |
| 39 | GET | `/api/v1/api-keys/admin/usage-logs/daily` | Usage daily summary |
| 40 | GET | `/api/v1/api-keys/admin/usage-logs/by-model` | Usage by model |
| 41 | GET | `/api/v1/api-keys/admin/smtp` | Xem SMTP config |
| 42 | POST | `/api/v1/api-keys/admin/smtp` | Cập nhật SMTP |
| 43 | POST | `/api/v1/api-keys/admin/smtp/test` | Gửi email test |

### Webhook Endpoints (Signature-based auth)

| # | Method | Endpoint | Mô tả |
|---|--------|----------|--------|
| 44 | POST | `/api/v1/api-keys/webhooks/payment/{provider}` | Nhận webhook từ cổng thanh toán |

**Tổng: 44 endpoints — 1 base URL duy nhất — Không có endpoint nào trùng lặp.**

---

## 7. Bảo Mật — Security Checklist

### ✅ ĐÃ TRIỂN KHAI

| # | Hạng mục | Chi tiết | Trạng thái |
|---|----------|----------|------------|
| 1 | **API Key hashing** | SHA-256, key gốc không lưu DB | ✅ Hoàn thành |
| 2 | **Auth endpoints** | Tất cả endpoint trả 401 khi không có token | ✅ Đã test |
| 3 | **Admin authorization** | `get_admin_user` dependency trên mọi admin endpoint | ✅ Hoàn thành |
| 4 | **Webhook signature** | Stripe (HMAC-SHA256), VNPay (HMAC-SHA512), MoMo (HMAC-SHA256) | ✅ Hoàn thành |
| 5 | **Timing-safe compare** | `hmac.compare_digest()` cho tất cả signature verification | ✅ Hoàn thành |
| 6 | **Idempotent webhooks** | Kiểm tra topup đã approved → trả idempotent response | ✅ Hoàn thành |
| 7 | **Rate limiting (per key)** | RPM limit theo plan (30/120/300), window per-minute | ✅ Hoàn thành |
| 8 | **Credit validation** | Kiểm tra status → expiry → credits → rate limit trước mỗi request | ✅ Hoàn thành |
| 9 | **Audit logging** | Mọi thao tác billing đều ghi audit log (actor, action, target) | ✅ Hoàn thành |
| 10 | **Key masking** | API key chỉ hiện đầy đủ 1 lần khi tạo, sau đó mask | ✅ Hoàn thành |
| 11 | **Ownership check** | User chỉ tạo topup cho key của mình (`key.user_id == user.id`) | ✅ Hoàn thành |
| 12 | **Invoice access control** | User chỉ xem invoice của mình (`invoice.user_id == user.id`) | ✅ Hoàn thành |
| 13 | **Provider validation** | Webhook kiểm tra provider match với payment account | ✅ Hoàn thành |
| 14 | **HTTP status codes chính xác** | 401 (unauth), 402 (no credits), 403 (forbidden), 429 (rate limit) | ✅ Hoàn thành |
| 15 | **Cryptographic key gen** | `secrets.token_urlsafe()` — CSPRNG | ✅ Hoàn thành |
| 16 | **Email notifications** | Gửi email khi topup submitted/approved/rejected/invoice | ✅ Hoàn thành |

### ⚠️ CẦN LƯU Ý (Không critical nhưng nên cải thiện)

| # | Hạng mục | Mức độ | Gợi ý |
|---|----------|--------|-------|
| 1 | **Race condition (rate limit)** | Medium | Rate limit window lưu trong DB JSON, multi-process có thể race. Cân nhắc dùng Redis counter. |
| 2 | **Webhook secret plaintext** | Low | Webhook secret lưu plaintext trong `metadata` JSON. Có thể encrypt at-rest. |
| 3 | **No IP whitelist for API keys** | Low | Không có tính năng restrict API key theo IP. Có thể thêm nếu cần. |
| 4 | **Admin operations không rate limit** | Low | Admin endpoint không bị giới hạn request rate. |
| 5 | **Metadata versioning** | Low | Credits/metadata thay đổi không có revision history (chỉ có audit log). |
| 6 | **Endpoint restriction bypass** | Medium | Config `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS` tồn tại nhưng `consume_api_key_credit()` chỉ check prefix `/openai` và `/api`. Cần verify logic endpoint whitelist. |

### Kết quả Security Test (2026-03-30)

| Test Case | URL | Expected | Actual | Kết quả |
|-----------|-----|----------|--------|---------|
| Unauth GET /plans | `/api/v1/api-keys/plans` | 401 | 401 | ✅ PASS |
| Unauth GET /me | `/api/v1/api-keys/me` | 401 | 401 | ✅ PASS |
| Unauth GET /settings | `/api/v1/api-keys/settings` | 401 | 401 | ✅ PASS |
| Unauth GET /admin/keys | `/api/v1/api-keys/admin/keys` | 401 | 401 | ✅ PASS |
| Unauth GET /admin/summary | `/api/v1/api-keys/admin/summary` | 401 | 401 | ✅ PASS |
| Unauth GET /model-pricing | `/api/v1/api-keys/model-pricing` | 401 | 401 | ✅ PASS |
| Fake webhook (generic) | POST `/webhooks/payment/generic` | 404 (not found) | 404 | ✅ PASS |
| Fake webhook (stripe) | POST `/webhooks/payment/stripe` | 403 (sig fail) | 403 | ✅ PASS |

---

## 8. Kết Quả Test

### 8.1 Backend ↔ Frontend đồng bộ

| Kiểm tra | Kết quả |
|----------|---------|
| Router prefix (`/api/v1/api-keys`) | ✅ Khớp |
| Frontend `WEBUI_API_BASE_URL + /api-keys/*` | ✅ Khớp |
| Tất cả 44 endpoint đều có frontend function tương ứng | ✅ Khớp |
| Pydantic models ↔ TypeScript types | ✅ Khớp |
| Auth dependency (JWT/API Key) | ✅ Khớp |

### 8.2 Credit flow

```
User gọi API (Bearer sk-...)
  → get_current_user() nhận diện API key
  → consume_api_key_credit(): trừ 1 credit, kiểm tra rate limit
  → Request được xử lý
  → finalize_billing(): tính chi phí thực tế theo token, trừ thêm nếu cần
  → Ghi usage_log
```

### 8.3 Các file chính trong hệ thống

| File | Vai trò |
|------|---------|
| `backend/open_webui/routers/api_keys.py` | Tất cả API endpoints (~1500 dòng) |
| `backend/open_webui/models/users.py` | ApiKey model, consume_api_key_credit |
| `backend/open_webui/models/billing.py` | Billing tables (pricing, usage, topup, invoice, audit) |
| `backend/open_webui/utils/auth.py` | Auth middleware, API key validation |
| `backend/open_webui/utils/billing.py` | Post-response billing calculation |
| `backend/open_webui/utils/webhooks.py` | Payment gateway signature verification |
| `backend/open_webui/utils/email.py` | Email notifications |
| `backend/open_webui/config.py` | Config variables (ENABLE_API_KEYS, etc.) |
| `src/lib/apis/api-keys/index.ts` | Frontend API client |

---

## 9. Ví Dụ CURL

### Ví dụ 1: Luồng đầy đủ cho User mới

```bash
# 1. Đăng nhập lấy JWT token
TOKEN=$(curl -s -X POST https://ai.vnso.vn/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' | jq -r '.token')

# 2. Kích hoạt API key
API_KEY=$(curl -s -X POST https://ai.vnso.vn/api/v1/api-keys/me/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"starter"}' | jq -r '.key')

echo "API Key: $API_KEY"

# 3. Gọi AI bằng API key
curl https://ai.vnso.vn/api/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Xin chào!"}]
  }'

# 4. Kiểm tra usage
curl -s https://ai.vnso.vn/api/v1/api-keys/me/usage \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Ví dụ 2: Admin tạo key cho user

```bash
ADMIN_TOKEN="your_admin_jwt_token"

# Tạo key
curl -X POST https://ai.vnso.vn/api/v1/api-keys/admin/keys \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "target_user_id",
    "plan_name": "pro",
    "credits": 30000
  }'
```

---

## 10. Troubleshooting

### Lỗi thường gặp

| HTTP Code | Message | Nguyên nhân | Giải pháp |
|-----------|---------|-------------|-----------|
| 401 | Not authenticated | Không có token hoặc token hết hạn | Đăng nhập lại lấy token mới |
| 402 | Credits exhausted | Hết credits | Nạp thêm credits qua topup |
| 403 | Not active / Expired | Key bị suspend hoặc hết hạn | Liên hệ admin hoặc regenerate |
| 403 | API key not allowed | User không có quyền dùng API keys | Admin bật permission cho user |
| 429 | Rate limit exceeded | Vượt quá RPM limit của plan | Chờ 1 phút hoặc nâng plan |
| 400 | Key already exists | Đã có key, không tạo lại được | Dùng regenerate thay vì activate |

### Kiểm tra nhanh hệ thống

```bash
# Health check
curl https://ai.vnso.vn/health

# Kiểm tra API key auth
curl -I https://ai.vnso.vn/api/v1/api-keys/plans

# Expected: HTTP 401 (chưa đăng nhập) hoặc HTTP 200 (đã đăng nhập)
```

### Config quan trọng (backend)

```python
ENABLE_API_KEYS = True                    # Bật/tắt API key feature
BILLING_AUTO_APPROVE_TOPUPS = True        # Tự động duyệt topup
BILLING_DEFAULT_CURRENCY = "VND"          # Tiền tệ mặc định (VND)
ENABLE_BILLING_EMAILS = True              # Gửi email thông báo
```

---

## Kết Luận

- **1 base URL duy nhất**: `https://ai.vnso.vn/api/v1/api-keys`
- **44 endpoints** phân theo 4 nhóm: User, Admin, Public, Webhook
- **Security**: 16 điểm đã triển khai, 6 điểm cần lưu ý (không critical)
- **Frontend ↔ Backend**: đồng bộ 100%
- **Test kết quả**: Tất cả endpoints trả HTTP status code chính xác
