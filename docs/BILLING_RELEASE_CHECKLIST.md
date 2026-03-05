# Billing Release Checklist

Checklist triển khai production cho luồng API-key billing (pricing/payment/topup/webhook/model-pricing).

## 1) Pre-Deployment

- [ ] Xác nhận branch/revision deploy đã bao gồm migration `c3d4e5f6a7b8_normalize_payment_provider_values`.
- [ ] Backup database trước khi chạy migration.
- [ ] Xác nhận có ít nhất 1 payment account `is_active=true`.
- [ ] Xác nhận `webhook_secret` đã cấu hình cho từng provider cần dùng.
- [ ] Xác nhận SMTP settings (nếu bật email billing).

## 2) Schema & Data Migration

Từ thư mục `backend`:

```bash
alembic -c open_webui/alembic.ini upgrade head
```

Kỳ vọng:
- Migration chạy thành công, không lỗi.
- Dữ liệu provider cũ được normalize về canonical values (`zalopay`, `vnpay`, `momo`, `paypal`, `bank_transfer`, `stripe`, `generic`).

## 3) Frontend Asset Sync (Optional)

Từ root project:

```bash
npm run assets:payment-logos:sync
```

Ghi chú:
- Nếu môi trường không có internet, hệ thống vẫn dùng local fallback assets trong `static/assets/payments/*.svg`.
- Nếu chạy sau proxy, set `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY`.

## 4) Smoke Test (User Flow)

- [ ] User mở `/developer/api-keys/pricing` và thấy provider list đúng (MoMo/VNPay/ZaloPay(VNG)/Stripe/Bank...).
- [ ] User activate API key thành công trong `/developer/api-keys`.
- [ ] User tạo top-up request thành công với provider bất kỳ.
- [ ] Trạng thái top-up chuyển đúng (auto-approve hoặc pending theo config).
- [ ] Invoice được tạo sau approve/payment success.
- [ ] Dashboard hiển thị credits và usage đúng.

## 5) Smoke Test (Admin Flow)

- [ ] Admin tạo/sửa payment account với alias provider (vd `vng`, `zalo-pay`) và lưu thành canonical value.
- [ ] Admin cấu hình model pricing (input/output/per request) và bật/tắt model trả phí.
- [ ] Admin approve/reject top-up thủ công hoạt động đúng.
- [ ] Analytics/audit log ghi nhận đầy đủ.

## 6) Webhook Verification

- [ ] Webhook URL gọi đúng provider endpoint: `/api/v1/api-keys/webhooks/payment/{provider}`.
- [ ] Signature/secret verification pass.
- [ ] Provider-account mismatch bị từ chối đúng (HTTP 400/403).
- [ ] Event duplicate được idempotent xử lý (không cộng credits trùng).

## 7) Post-Deployment Monitoring

- [ ] Theo dõi log lỗi webhook/payment trong 24h đầu.
- [ ] Đối soát invoices vs payment gateway settlement.
- [ ] Theo dõi tỉ lệ reject/pending bất thường.
- [ ] Theo dõi support tickets liên quan credits/pricing.
