# API Key Billing Workflow (Paid Users)

This document describes the product workflow for paid API key operations in Open WebUI fork `vnso`.

## 1) User Journey (Professional Flow)

1. User opens **Pricing** page: `/developer/api-keys/pricing`
2. User picks package (Starter / Pro / Business / VIP-style tiers)
3. User opens **Developer Console**: `/developer/api-keys`
4. User completes payment/top-up (MoMo / VNPay / ZaloPay(VNG) / Stripe / Bank transfer)
5. Payment is confirmed (`approved` or webhook `paid`) then credits are activated
6. User receives API key in console, starts API calls, and tracks usage/spend
7. When using paid models, token costs are deducted based on admin-configured model pricing

## 2) Admin Journey

1. Admin opens **Admin API Keys**: `/admin/api-keys`
2. Admin configures payment accounts (MoMo/VNPay/ZaloPay(VNG)/Stripe/bank, QR, instructions, webhook secret)
3. Admin reviews pending top-up queue
4. Admin approves/rejects with note and credits amount
5. Admin configures paid/free models and per-model pricing (input/output/request cost)
6. System writes invoice + audit logs + revenue analytics
7. Admin monitors daily revenue, key status, invoices and audit trail

## 3) API Endpoints (Core)

### User
- `GET /api/v1/api-keys/plans`
- `GET /api/v1/api-keys/me`
- `GET /api/v1/api-keys/me/usage`
- `POST /api/v1/api-keys/me/regenerate`
- `GET /api/v1/api-keys/payment-accounts`
- `POST /api/v1/api-keys/me/topups`
- `GET /api/v1/api-keys/me/topups`
- `GET /api/v1/api-keys/me/invoices`
- `GET /api/v1/api-keys/me/invoices/{invoice_id}`

### Admin
- `GET /api/v1/api-keys/admin/summary`
- `GET /api/v1/api-keys/admin/keys`
- `POST /api/v1/api-keys/admin/keys/{key_id}/status`
- `POST /api/v1/api-keys/admin/keys/{key_id}/credits`
- `POST /api/v1/api-keys/admin/payment-accounts`
- `POST /api/v1/api-keys/admin/topups/{request_id}/approve`
- `POST /api/v1/api-keys/admin/topups/{request_id}/reject`
- `GET /api/v1/api-keys/admin/invoices`
- `GET /api/v1/api-keys/admin/analytics/revenue-daily`
- `GET /api/v1/api-keys/admin/audit-logs`

## 4) Payment/Webhook Pipeline

1. Gateway sends event to `POST /api/v1/api-keys/webhooks/payment/{provider}`
2. Webhook secret is validated from payment account metadata
3. Matching top-up request is resolved
4. Credits are applied to API key
5. Top-up status is moved to `approved`
6. Invoice and audit logs are created (idempotent handling included)

## 4.1) Pro/VIP Capability Pack (Suggested)

- Priority request queue and higher RPM by plan
- Access control by model tier (Free / Pro / VIP)
- Higher context window + advanced models for Pro/VIP plans
- Dedicated support SLA for Business/VIP plans
- Monthly included credits + top-up + overage protection alerts

## 5) Operational Checklist

- Configure at least one active payment account before launch
- Set strong `webhook_secret` per provider account
- Monitor `admin/audit-logs` daily
- Reconcile paid invoices vs gateway settlement report
- Alert on high reject rate or unusual top-up spikes

## 5.1) Payment Logo Operations

- Fallback local assets are in `static/assets/payments/*.svg`
- Sync external/public logo sources with `npm run assets:payment-logos:sync`
- If server is behind proxy, configure `HTTPS_PROXY`/`HTTP_PROXY`/`ALL_PROXY`
- Trademark usage remains property of each provider (MoMo/VNPay/ZaloPay)

## 5.2) Provider Normalization (Backend Hardening)

- Backend normalizes provider aliases to canonical values before save/verification:
	- `vng`, `zalo_pay`, `zalo-pay` -> `zalopay`
	- `vn_pay`, `vn-pay` -> `vnpay`
	- `mo_mo`, `mo-mo` -> `momo`
	- `pay_pal`, `pay-pal` -> `paypal`
	- `bank`, `banktransfer`, `bank-transfer` -> `bank_transfer`
- Webhook endpoint also applies normalization and validates provider-account match.

## 6) Suggested CI/CD Promotion Pipeline

- Stage 1: lint + typecheck + unit tests
- Stage 2: build image tagged with commit SHA
- Stage 3: run migration smoke test on staging DB
- Stage 4: deploy canary and run health checks
- Stage 5: full production rollout + rollback policy

## 7) Release Checklist Reference

- Use `docs/BILLING_RELEASE_CHECKLIST.md` as the deployment runbook for billing-related releases.

