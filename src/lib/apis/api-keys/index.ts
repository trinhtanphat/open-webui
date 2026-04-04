import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ApiKeyConsole = {
	id: string;
	user_id: string;
	key: string;
	key_masked: string;
	status: 'active' | 'suspended' | string;
	plan_name?: string;
	monthly_price_usd?: number;
	credits_remaining: number;
	total_requests: number;
	monthly_requests: number;
	usage_month?: string;
	last_used_at?: number;
	expires_at?: number;
	created_at: number;
	updated_at: number;
};

export type ApiKeyListItem = {
	id: string;
	user_id: string;
	name?: string;
	key_prefix: string;
	status: 'active' | 'suspended' | string;
	plan_name?: string;
	credits_remaining: number;
	total_requests: number;
	last_used_at?: number;
	expires_at?: number;
	created_at: number;
	updated_at: number;
};

export type PaymentAccount = {
	id: string;
	provider: string;
	account_name: string;
	account_number: string;
	qr_code_url?: string;
	instructions?: string;
	metadata?: Record<string, any>;
	is_active: string;
	created_at: number;
	updated_at: number;
};

export type TopupRequest = {
	id: string;
	user_id: string;
	user_name?: string;
	api_key_id: string;
	payment_account_id: string;
	amount: number;
	currency: string;
	tx_ref?: string;
	note?: string;
	status: 'pending' | 'approved' | 'rejected' | string;
	reviewed_by?: string;
	reviewed_note?: string;
	reviewed_at?: number;
	created_at: number;
	updated_at: number;
};

export type BillingInvoice = {
	id: string;
	user_id: string;
	user_name?: string;
	api_key_id: string;
	topup_request_id?: string;
	amount: number;
	currency: string;
	credits: number;
	status: string;
	data?: Record<string, any>;
	created_at: number;
	updated_at: number;
};

export type BillingSummary = {
	total_keys: number;
	active_keys: number;
	total_credits_remaining: number;
	pending_topups: number;
	paid_invoices: number;
	total_revenue: number;
};

export type RevenueDailyEntry = {
	date: string;
	revenue: number;
	credits: number;
	invoices: number;
};

export type BillingSettings = {
	auto_approve_topups: boolean;
	default_currency: string;
	enable_billing_emails?: boolean;
};

export type SmtpSettings = {
	smtp_host: string;
	smtp_port: number;
	smtp_user: string;
	smtp_password?: string;
	smtp_from: string;
	smtp_tls: boolean;
	enable_billing_emails: boolean;
};

export type ApiKeyPlan = {
	id: string;
	name: string;
	monthly_price_usd: number;
	included_credits: number;
	rpm_limit: number;
	overage_usd_per_1k_requests: number;
	support_tier: string;
	recommended_for: string;
};

export type UserUsageSummary = {
	plan_name?: string;
	monthly_price_usd?: number;
	credits_remaining: number;
	total_requests: number;
	monthly_requests: number;
	usage_month?: string;
	last_used_at?: number;
	pending_topups: number;
	approved_topups: number;
	rejected_topups: number;
	paid_invoices: number;
	total_spend_usd: number;
	avg_spend_per_1k_requests_usd: number;
};

// ---- Model Pricing types ----
export type ModelPricing = {
	id: string;
	model_id: string;
	display_name?: string;
	input_cost_per_1k_tokens: number;
	output_cost_per_1k_tokens: number;
	per_request_cost: number;
	currency: string;
	is_active: string;
	created_by?: string;
	updated_by?: string;
	created_at: number;
	updated_at: number;
};

// ---- Usage Log types ----
export type UsageLogEntry = {
	id: string;
	user_id: string;
	api_key_id: string;
	model: string;
	endpoint?: string;
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	input_cost: number;
	output_cost: number;
	total_cost: number;
	credits_deducted: number;
	currency: string;
	request_metadata?: Record<string, any>;
	created_at: number;
};

export type UsageDailySummary = {
	date: string;
	requests: number;
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	total_cost: number;
};

export type UsageByModelSummary = {
	model: string;
	requests: number;
	total_tokens: number;
	total_cost: number;
};

const authHeaders = (token: string) => ({
	'Content-Type': 'application/json',
	Authorization: `Bearer ${token}`
});

export const activateMyApiKey = async (
	token: string,
	planId: string = 'starter'
): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/activate`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ plan_id: planId })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to activate API key';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getMyApiKeyConsole = async (token: string): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch API key console';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getApiKeyPlans = async (token: string): Promise<ApiKeyPlan[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/plans`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch plans';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getMyUsageSummary = async (token: string): Promise<UserUsageSummary> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/usage`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch usage summary';
			return null;
		});

	if (error) throw error;
	return res;
};

export const regenerateMyApiKey = async (token: string): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/regenerate`, {
		method: 'POST',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to regenerate API key';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getMyApiKeys = async (token: string): Promise<ApiKeyListItem[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/keys`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch API keys';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const createMyApiKey = async (
	token: string,
	name?: string
): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/keys`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ name: name || null })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to create API key';
			return null;
		});

	if (error) throw error;
	return res;
};

export const deleteMyApiKey = async (
	token: string,
	keyId: string
): Promise<void> => {
	let error = null;

	await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/keys/${keyId}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to delete API key';
			return null;
		});

	if (error) throw error;
};

export const getAdminApiKeys = async (token: string): Promise<ApiKeyConsole[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/keys`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch API keys';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const updateAdminApiKeyCredits = async (
	token: string,
	keyId: string,
	delta: number,
	note?: string
): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/keys/${keyId}/credits`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ delta, note })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to update credits';
			return null;
		});

	if (error) throw error;
	return res;
};

export const updateAdminApiKeyStatus = async (
	token: string,
	keyId: string,
	status: 'active' | 'suspended'
): Promise<ApiKeyConsole> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/keys/${keyId}/status`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ status })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to update status';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getAdminBillingSummary = async (token: string): Promise<BillingSummary> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/summary`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch billing summary';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getAdminPaymentAccounts = async (token: string): Promise<PaymentAccount[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/payment-accounts`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch payment accounts';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getBillingSettings = async (token: string): Promise<BillingSettings> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/settings`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch billing settings';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getAdminBillingSettings = async (token: string): Promise<BillingSettings> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/settings`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch admin billing settings';
			return null;
		});

	if (error) throw error;
	return res;
};

export const updateAdminBillingSettings = async (
	token: string,
	formData: BillingSettings
): Promise<BillingSettings> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/settings`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to update admin billing settings';
			return null;
		});

	if (error) throw error;
	return res;
};

export const createAdminPaymentAccount = async (
	token: string,
	formData: {
		provider: string;
		account_name: string;
		account_number: string;
		qr_code_url?: string;
		instructions?: string;
		metadata?: Record<string, any>;
	}
): Promise<PaymentAccount> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/payment-accounts`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to create payment account';
			return null;
		});

	if (error) throw error;
	return res;
};

export const updateAdminPaymentAccount = async (
	token: string,
	accountId: string,
	formData: Record<string, any>
): Promise<PaymentAccount> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/payment-accounts/${accountId}`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to update payment account';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getAdminTopups = async (token: string, status?: string): Promise<TopupRequest[]> => {
	let error = null;

	const query = status ? `?status=${encodeURIComponent(status)}` : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/topups${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch topups';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const approveAdminTopup = async (
	token: string,
	requestId: string,
	credits: number,
	note?: string
): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/topups/${requestId}/approve`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ credits, note })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to approve topup';
			return null;
		});

	if (error) throw error;
	return res;
};

export const rejectAdminTopup = async (token: string, requestId: string, note?: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/topups/${requestId}/reject`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ note })
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to reject topup';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getAdminInvoices = async (token: string): Promise<BillingInvoice[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/invoices`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch invoices';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getAdminInvoiceById = async (token: string, invoiceId: string): Promise<BillingInvoice> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/invoices/${invoiceId}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch invoice detail';
			return null;
		});

	if (error) throw error;
	return res;
};

// ---------------------------------------------------------------------------
// Admin – Model Pricing
// ---------------------------------------------------------------------------
export const getAdminModelPricings = async (
	token: string,
	includeInactive = false
): Promise<ModelPricing[]> => {
	let error = null;
	const query = includeInactive ? '?include_inactive=true' : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/model-pricing${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch model pricings';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

export const createAdminModelPricing = async (
	token: string,
	formData: {
		model_id: string;
		display_name?: string;
		input_cost_per_1k_tokens: number;
		output_cost_per_1k_tokens: number;
		per_request_cost: number;
		currency: string;
	}
): Promise<ModelPricing> => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/model-pricing`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to create model pricing';
			return null;
		});
	if (error) throw error;
	return res;
};

export const updateAdminModelPricing = async (
	token: string,
	pricingId: string,
	formData: Record<string, any>
): Promise<ModelPricing> => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/model-pricing/${pricingId}`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to update model pricing';
			return null;
		});
	if (error) throw error;
	return res;
};

export const deleteAdminModelPricing = async (
	token: string,
	pricingId: string
): Promise<{ ok: boolean }> => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/model-pricing/${pricingId}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to delete model pricing';
			return null;
		});
	if (error) throw error;
	return res ?? { ok: false };
};

// ---------------------------------------------------------------------------
// Admin – Usage Logs
// ---------------------------------------------------------------------------
export const getAdminUsageLogs = async (
	token: string,
	params?: { user_id?: string; model?: string; days?: number; limit?: number }
): Promise<UsageLogEntry[]> => {
	let error = null;
	const qs = new URLSearchParams();
	if (params?.user_id) qs.set('user_id', params.user_id);
	if (params?.model) qs.set('model', params.model);
	if (params?.days) qs.set('days', String(params.days));
	if (params?.limit) qs.set('limit', String(params.limit));
	const query = qs.toString() ? `?${qs.toString()}` : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/usage-logs${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch usage logs';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

export const getAdminUsageDaily = async (
	token: string,
	params?: { user_id?: string; days?: number }
): Promise<UsageDailySummary[]> => {
	let error = null;
	const qs = new URLSearchParams();
	if (params?.user_id) qs.set('user_id', params.user_id);
	if (params?.days) qs.set('days', String(params.days));
	const query = qs.toString() ? `?${qs.toString()}` : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/usage-logs/daily${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch daily usage';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

export const getAdminUsageByModel = async (
	token: string,
	params?: { user_id?: string; days?: number }
): Promise<UsageByModelSummary[]> => {
	let error = null;
	const qs = new URLSearchParams();
	if (params?.user_id) qs.set('user_id', params.user_id);
	if (params?.days) qs.set('days', String(params.days));
	const query = qs.toString() ? `?${qs.toString()}` : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/usage-logs/by-model${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch usage by model';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

// ---------------------------------------------------------------------------
// Public – Model Pricing (read-only)
// ---------------------------------------------------------------------------
export const getPublicModelPricing = async (token: string): Promise<ModelPricing[]> => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/model-pricing`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch model pricing';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

// ---------------------------------------------------------------------------
// User – My Usage Logs
// ---------------------------------------------------------------------------
export const getMyUsageLogs = async (
	token: string,
	params?: { model?: string; days?: number; limit?: number }
): Promise<UsageLogEntry[]> => {
	let error = null;
	const qs = new URLSearchParams();
	if (params?.model) qs.set('model', params.model);
	if (params?.days) qs.set('days', String(params.days));
	if (params?.limit) qs.set('limit', String(params.limit));
	const query = qs.toString() ? `?${qs.toString()}` : '';
	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/usage-logs${query}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch my usage logs';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

export const getMyUsageDaily = async (
	token: string,
	days = 30
): Promise<UsageDailySummary[]> => {
	let error = null;
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/api-keys/me/usage-logs/daily?days=${days}`,
		{ method: 'GET', headers: authHeaders(token) }
	)
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch my daily usage';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};

export const getMyUsageByModel = async (
	token: string,
	days = 30
): Promise<UsageByModelSummary[]> => {
	let error = null;
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/api-keys/me/usage-logs/by-model?days=${days}`,
		{ method: 'GET', headers: authHeaders(token) }
	)
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to fetch my usage by model';
			return null;
		});
	if (error) throw error;
	return res ?? [];
};export const getAdminRevenueDaily = async (token: string, days = 30): Promise<RevenueDailyEntry[]> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/api-keys/admin/analytics/revenue-daily?days=${encodeURIComponent(days)}`,
		{
			method: 'GET',
			headers: authHeaders(token)
		}
	)
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch revenue analytics';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getAdminAuditLogs = async (token: string, limit = 100): Promise<any[]> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/api-keys/admin/audit-logs?limit=${encodeURIComponent(limit)}`,
		{
			method: 'GET',
			headers: authHeaders(token)
		}
	)
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch audit logs';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getPublicPaymentAccounts = async (token: string): Promise<PaymentAccount[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/payment-accounts`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch payment accounts';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const createMyTopupRequest = async (
	token: string,
	formData: {
		api_key_id: string;
		payment_account_id: string;
		amount: number;
		currency: string;
		tx_ref?: string;
		note?: string;
	}
): Promise<TopupRequest> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/topups`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to create topup request';
			return null;
		});

	if (error) throw error;
	return res;
};

export const getMyTopups = async (token: string): Promise<TopupRequest[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/topups`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch my topups';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getMyInvoices = async (token: string): Promise<BillingInvoice[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/invoices`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch my invoices';
			return null;
		});

	if (error) throw error;
	return res ?? [];
};

export const getMyInvoiceById = async (token: string, invoiceId: string): Promise<BillingInvoice> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/me/invoices/${invoiceId}`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch invoice detail';
			return null;
		});

	if (error) throw error;
	return res;
};

// ---------------------------------------------------------------------------
// SMTP Settings (Admin)
// ---------------------------------------------------------------------------

export const getAdminSmtpSettings = async (token: string): Promise<SmtpSettings> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/smtp`, {
		method: 'GET',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to fetch SMTP settings';
			return null;
		});

	if (error) throw error;
	return res;
};

export const updateAdminSmtpSettings = async (
	token: string,
	formData: SmtpSettings
): Promise<SmtpSettings> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/smtp`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(formData)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'Failed to update SMTP settings';
			return null;
		});

	if (error) throw error;
	return res;
};

export const testAdminSmtp = async (token: string): Promise<{ status: string; message: string }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/api-keys/admin/smtp/test`, {
		method: 'POST',
		headers: authHeaders(token)
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? 'SMTP test failed';
			return null;
		});

	if (error) throw error;
	return res;
};
