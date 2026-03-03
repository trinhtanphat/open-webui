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

const authHeaders = (token: string) => ({
	'Content-Type': 'application/json',
	Authorization: `Bearer ${token}`
});

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

export const getAdminRevenueDaily = async (token: string, days = 30): Promise<RevenueDailyEntry[]> => {
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
