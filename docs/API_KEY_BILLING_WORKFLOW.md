# API Key Billing Workflow (Paid Users)

This document describes the product workflow for paid API key operations in Open WebUI fork `vnso`.

## 1) User Journey (Professional Flow)

1. User opens **Pricing** page: `/developer/api-keys/pricing`
2. User picks package (Starter / Pro / Business)
3. User goes to **Developer Console**: `/developer/api-keys`
4. User submits top-up request with payment account + transaction reference
5. User tracks request status (`pending`, `approved`, `rejected`)
6. On approval, credits are added and invoice is generated
7. User exports invoice PDF and tracks usage/spend metrics

## 2) Admin Journey

1. Admin opens **Admin API Keys**: `/admin/api-keys`
2. Admin configures payment accounts (bank/gateway, QR, instructions, webhook secret)
3. Admin reviews pending top-up queue
4. Admin approves/rejects with note and credits amount
5. System writes invoice + audit logs + revenue analytics
6. Admin monitors daily revenue, key status, invoices and audit trail

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

## 5) Operational Checklist

- Configure at least one active payment account before launch
- Set strong `webhook_secret` per provider account
- Monitor `admin/audit-logs` daily
- Reconcile paid invoices vs gateway settlement report
- Alert on high reject rate or unusual top-up spikes

## 6) Suggested CI/CD Promotion Pipeline

- Stage 1: lint + typecheck + unit tests
- Stage 2: build image tagged with commit SHA
- Stage 3: run migration smoke test on staging DB
- Stage 4: deploy canary and run health checks
- Stage 5: full production rollout + rollback policy

