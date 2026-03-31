# Project workflow

- [API Key Billing Workflow](API_KEY_BILLING_WORKFLOW.md)

[![API Key Billing Workflow](https://mermaid.ink/img/pako:eNq1k01rAjEQhv_KkFNLFe1N9iAUevFSRVl6Cci4Gd1ANtlmsmtF_O_N7iqtHxR76ClhMu87zwyZvcicIpEIpo-KbEavGjceC2lL9EFnukQbIGXygNye5y9TY7DAZTpZLsjXXVYXg3dapRM4hh9mu5A7-3hTfSXtAtJK21Tsj8dPl3USmJZkGVbebWNKD2rNOjAYl6HJHYdkNBwNpb3U9aNZvzFNYE6h8tFiSyZzBUGJG4K1dwVwTSYQrCptlLRvLt5dA5i2la5Ruk51Ux0VKQjuxPVbAwuyiuFlNgHfzJ5DoxtgqQf1813gnZRLZ5lAYcD7WT1lpGtiQKug9C4jZrrp-Fd-1-Y1bdzo4dvnZDLz7lPHyj8sOgfg4x84E7RTuEaZt8yRZqtDfgT_rwG2u3Dv_ERPFOQL1Cqu2F5aAClCTgVJkcSrojVWJkgh7SGmYhXcYmczkQRfUU9UZfQ4baRI1miYDl_QqlPg?type=png)](https://mermaid.live/edit#pako:eNq1k01rAjEQhv_KkFNLFe1N9iAUevFSRVl6Cci4Gd1ANtlmsmtF_O_N7iqtHxR76ClhMu87zwyZvcicIpEIpo-KbEavGjceC2lL9EFnukQbIGXygNye5y9TY7DAZTpZLsjXXVYXg3dapRM4hh9mu5A7-3hTfSXtAtJK21Tsj8dPl3USmJZkGVbebWNKD2rNOjAYl6HJHYdkNBwNpb3U9aNZvzFNYE6h8tFiSyZzBUGJG4K1dwVwTSYQrCptlLRvLt5dA5i2la5Ruk51Ux0VKQjuxPVbAwuyiuFlNgHfzJ5DoxtgqQf1813gnZRLZ5lAYcD7WT1lpGtiQKug9C4jZrrp-Fd-1-Y1bdzo4dvnZDLz7lPHyj8sOgfg4x84E7RTuEaZt8yRZqtDfgT_rwG2u3Dv_ERPFOQL1Cqu2F5aAClCTgVJkcSrojVWJkgh7SGmYhXcYmczkQRfUU9UZfQ4baRI1miYDl_QqlPg)

---

## Changelog

### 2026-03-31 — Fix: Thống nhất API endpoint và sửa lỗi API key không gọi được

**Vấn đề:** API key tạo qua route cũ (`/api/v1/auths/api_key`) không có billing metadata
→ `credits_remaining = 0` → mọi request đều bị chặn HTTP 402 "credits exhausted".

**Root cause:**
1. Hai hệ thống API key xung đột — route cũ tạo key **không có** billing metadata, route mới thì có
2. `consume_api_key_credit` tính credit cho cả endpoint quản lý key (`/api/v1/api-keys/*`)
3. `Account.svelte` vẫn đang gọi route cũ

**Files đã thay đổi:**

#### `backend/open_webui/models/users.py` — `consume_api_key_credit()`
- Legacy key (không có `plan_name` / `credits_remaining`): cho qua, không trừ credit
- Endpoint quản lý key (`/api/v1/api-keys/*`): bỏ qua credit deduction
- Thêm `/ollama` vào điều kiện tính credit
- Gộp logic thành biến `should_deduct` cho rõ ràng

#### `backend/open_webui/routers/auths.py` — `generate_api_key()` (route cũ `/api/v1/auths/api_key`)
- Sau khi tạo key, tự inject billing metadata mặc định (starter plan, 5000 credits, rpm_limit 60, `activated_by: "legacy"`)
- Backward compatible: key tạo từ route cũ nay hoạt động bình thường với billing system

#### `src/lib/components/chat/Settings/Account.svelte`
- Chuyển từ `createAPIKey`/`getAPIKey` (route cũ) sang `activateMyApiKey` / `regenerateMyApiKey` / `getMyApiKeyConsole`
- Xử lý case "key already exists" → tự động fallback sang regenerate

**Endpoint thống nhất toàn bộ frontend dùng: `/api/v1/api-keys/*`**

| Chức năng | Method | Endpoint |
|---|---|---|
| Tạo key lần đầu | POST | `/api/v1/api-keys/me/activate` |
| Xem key (masked) | GET | `/api/v1/api-keys/me` |
| Tạo lại key | POST | `/api/v1/api-keys/me/regenerate` |
| Xem plans | GET | `/api/v1/api-keys/plans` |
| Xem usage | GET | `/api/v1/api-keys/me/usage` |
| Topup | POST | `/api/v1/api-keys/me/topups` |
| Admin: all keys | GET | `/api/v1/api-keys/admin/keys` |
| Admin: add credits | POST | `/api/v1/api-keys/admin/keys/{id}/credits` |
| Admin: set status | POST | `/api/v1/api-keys/admin/keys/{id}/status` |
| Admin: approve topup | POST | `/api/v1/api-keys/admin/topups/{id}/approve` |

> **Lưu ý:** Route cũ `/api/v1/auths/api_key` vẫn còn trong codebase (backward compat) nhưng đã patch để inject metadata. Có thể deprecated sau.
