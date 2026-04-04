<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { user } from '$lib/stores';
	import BarChart from '$lib/components/billing/BarChart.svelte';
	import PaymentProviderIcon from '$lib/components/billing/PaymentProviderIcon.svelte';
	import PageToolbar from '$lib/components/billing/PageToolbar.svelte';
	import Bolt from '$lib/components/icons/Bolt.svelte';
	import Star from '$lib/components/icons/Star.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import ChartBar from '$lib/components/icons/ChartBar.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import CheckCircle from '$lib/components/icons/CheckCircle.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import {
		approveAdminTopup,
		createAdminPaymentAccount,
		getAdminBillingSettings,
		getAdminAuditLogs,
		getApiKeyPlans,
		getAdminRevenueDaily,
		getAdminBillingSummary,
		getAdminInvoices,
		getAdminPaymentAccounts,
		getAdminTopups,
		rejectAdminTopup,
		getAdminApiKeys,
		updateAdminApiKeyCredits,
		updateAdminApiKeyStatus,
		updateAdminBillingSettings,
		getAdminModelPricings,
		createAdminModelPricing,
		updateAdminModelPricing,
		deleteAdminModelPricing,
		getAdminUsageLogs,
		getAdminUsageDaily,
		getAdminUsageByModel,
		getAdminSmtpSettings,
		updateAdminSmtpSettings,
		testAdminSmtp,
		type ApiKeyConsole,
		type ApiKeyPlan,
		type BillingSettings,
		type BillingInvoice,
		type BillingSummary,
		type PaymentAccount,
		type RevenueDailyEntry,
		type TopupRequest,
		type ModelPricing,
		type UsageLogEntry,
		type UsageDailySummary,
		type UsageByModelSummary,
		type SmtpSettings
	} from '$lib/apis/api-keys';

	const i18n = getContext<any>('i18n');

	let loading = true;
	let adminTab: 'keys' | 'pricing' | 'payments' | 'topups' | 'analytics' | 'audit' | 'email' = 'keys';
	let keys: ApiKeyConsole[] = [];
	let summary: BillingSummary | null = null;
	let paymentAccounts: PaymentAccount[] = [];
	let topups: TopupRequest[] = [];
	let invoices: BillingInvoice[] = [];
	let revenueDaily: RevenueDailyEntry[] = [];
	let auditLogs: any[] = [];
	let plans: ApiKeyPlan[] = [];
	let modelPricings: ModelPricing[] = [];
	let usageLogs: UsageLogEntry[] = [];
	let usageDaily: UsageDailySummary[] = [];
	let usageByModel: UsageByModelSummary[] = [];
	let billingSettings: BillingSettings = { auto_approve_topups: true, default_currency: 'VND' };
	let savingBillingSettings = false;

	// SMTP / Email settings
	let smtpSettings: SmtpSettings = {
		smtp_host: '', smtp_port: 587, smtp_user: '', smtp_from: '',
		smtp_tls: true, enable_billing_emails: true
	};
	let smtpPassword = '';
	let savingSmtp = false;
	let testingSmtp = false;

	let creditDelta = 100;
	let approveCredits = 100;

	// Model Pricing form
	let mpModelId = '';
	let mpDisplayName = '';
	let mpInputCost = 0;
	let mpOutputCost = 0;
	let mpRequestCost = 0;
	let mpCurrency = 'VND';

	let provider = 'bank_transfer';
	let providerMenuOpen = false;
	let providerMenuRef: HTMLDivElement;
	let accountName = '';
	let accountNumber = '';
	let instructions = '';
	let qrCodeUrl = '';
	let webhookSecret = '';

	// Editing model pricing
	let editingPricingId: string | null = null;

	// QR file input ref
	let qrFileInput: HTMLInputElement;

	const statusColor = (status: string) => {
		switch (status) {
			case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
			case 'approved': case 'paid': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
			case 'pending': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
			case 'rejected': case 'disabled': case 'suspended': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
			default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
		}
	};

	const getPaymentProviderByTopupId = (topupId?: string) => {
		if (!topupId) return 'generic';
		const topup = topups.find((item) => item.id === topupId);
		if (!topup) return 'generic';
		const account = paymentAccounts.find((item) => item.id === topup.payment_account_id);
		return account?.provider || 'generic';
	};

	const getPaymentProviderByAccountId = (accountId?: string) => {
		if (!accountId) return 'generic';
		const account = paymentAccounts.find((item) => item.id === accountId);
		return account?.provider || 'generic';
	};

	const providerOptions = [
		{ value: 'generic', label: 'Generic' },
		{ value: 'bank_transfer', label: 'Bank Transfer' },
		{ value: 'stripe', label: 'Stripe' },
		{ value: 'vnpay', label: 'VNPay' },
		{ value: 'momo', label: 'MoMo' },
		{ value: 'zalopay', label: 'ZaloPay (VNG)' },
		{ value: 'vng', label: 'VNG (ZaloPay)' },
		{ value: 'paypal', label: 'PayPal' }
	];

	const getProviderLabel = (providerValue: string) => {
		if (providerValue === 'vng') return 'VNG (ZaloPay)';
		return providerOptions.find((item) => item.value === providerValue)?.label || providerValue;
	};

	const loadData = async () => {
		keys = await getAdminApiKeys(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return [];
		});

		summary = await getAdminBillingSummary(localStorage.token).catch(() => null);
		paymentAccounts = await getAdminPaymentAccounts(localStorage.token).catch(() => []);
		topups = await getAdminTopups(localStorage.token).catch(() => []);
		invoices = await getAdminInvoices(localStorage.token).catch(() => []);
		revenueDaily = await getAdminRevenueDaily(localStorage.token, 30).catch(() => []);
		auditLogs = await getAdminAuditLogs(localStorage.token, 30).catch(() => []);
		plans = await getApiKeyPlans(localStorage.token).catch(() => []);
		modelPricings = await getAdminModelPricings(localStorage.token, true).catch(() => []);
		usageDaily = await getAdminUsageDaily(localStorage.token, { days: 30 }).catch(() => []);
		usageByModel = await getAdminUsageByModel(localStorage.token, { days: 30 }).catch(() => []);
		billingSettings = await getAdminBillingSettings(localStorage.token).catch(() => ({
			auto_approve_topups: true, default_currency: 'VND'
		}));
		smtpSettings = await getAdminSmtpSettings(localStorage.token).catch(() => ({
			smtp_host: '', smtp_port: 587, smtp_user: '', smtp_from: '',
			smtp_tls: true, enable_billing_emails: true
		}));
	};

	const toggleAutoApproveTopups = async () => {
		savingBillingSettings = true;
		await updateAdminBillingSettings(localStorage.token, {
			auto_approve_topups: !billingSettings.auto_approve_topups,
			default_currency: billingSettings.default_currency
		})
			.then((settings) => {
				billingSettings = settings;
				toast.success($i18n.t('Billing automation settings updated'));
			})
			.catch((error) => toast.error(`${error}`));
		savingBillingSettings = false;
	};

	onMount(() => {
		const handleDocumentClick = (event: MouseEvent) => {
			if (!providerMenuOpen) return;
			const target = event.target as Node;
			if (providerMenuRef && !providerMenuRef.contains(target)) {
				providerMenuOpen = false;
			}
		};

		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				providerMenuOpen = false;
			}
		};

		document.addEventListener('click', handleDocumentClick);
		document.addEventListener('keydown', handleEscape);

		(async () => {
			if ($user?.role !== 'admin') {
				await goto('/');
				return;
			}

			await loadData();
			loading = false;
		})();

		return () => {
			document.removeEventListener('click', handleDocumentClick);
			document.removeEventListener('keydown', handleEscape);
		};
	});

	const toggleStatus = async (key: ApiKeyConsole) => {
		const nextStatus = key.status === 'active' ? 'suspended' : 'active';
		await updateAdminApiKeyStatus(localStorage.token, key.id, nextStatus)
			.then(async () => {
				toast.success($i18n.t('API key status updated'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const adjustCredits = async (key: ApiKeyConsole, delta: number) => {
		await updateAdminApiKeyCredits(localStorage.token, key.id, delta, 'manual adjustment')
			.then(async () => {
				toast.success($i18n.t('Credits updated'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const createPaymentAccount = async () => {
		if (!accountName || !accountNumber) {
			toast.error($i18n.t('Account name and number are required'));
			return;
		}

		await createAdminPaymentAccount(localStorage.token, {
			provider,
			account_name: accountName,
			account_number: accountNumber,
			instructions,
			qr_code_url: qrCodeUrl,
			metadata: webhookSecret
				? {
					webhook_secret: webhookSecret
				}
				: undefined
		})
			.then(async () => {
				toast.success($i18n.t('Payment account created'));
				accountName = '';
				accountNumber = '';
				instructions = '';
				qrCodeUrl = '';
				webhookSecret = '';
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const approveTopup = async (topup: TopupRequest) => {
		await approveAdminTopup(localStorage.token, topup.id, approveCredits)
			.then(async () => {
				toast.success($i18n.t('Top-up approved'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const rejectTopup = async (topup: TopupRequest) => {
		await rejectAdminTopup(localStorage.token, topup.id, 'Rejected by admin')
			.then(async () => {
				toast.success($i18n.t('Top-up rejected'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const createModelPricing = async () => {
		if (!mpModelId) {
			toast.error($i18n.t('Model ID is required'));
			return;
		}

		if (editingPricingId) {
			// Update existing pricing
			await updateAdminModelPricing(localStorage.token, editingPricingId, {
				model_id: mpModelId,
				display_name: mpDisplayName || undefined,
				input_cost_per_1k_tokens: mpInputCost,
				output_cost_per_1k_tokens: mpOutputCost,
				per_request_cost: mpRequestCost,
				currency: mpCurrency
			})
				.then(async () => {
					toast.success($i18n.t('Model pricing updated'));
					cancelEditPricing();
					await loadData();
				})
				.catch((error) => toast.error(`${error}`));
			return;
		}

		await createAdminModelPricing(localStorage.token, {
			model_id: mpModelId,
			display_name: mpDisplayName || undefined,
			input_cost_per_1k_tokens: mpInputCost,
			output_cost_per_1k_tokens: mpOutputCost,
			per_request_cost: mpRequestCost,
			currency: mpCurrency
		})
			.then(async () => {
				toast.success($i18n.t('Model pricing created'));
				mpModelId = '';
				mpDisplayName = '';
				mpInputCost = 0;
				mpOutputCost = 0;
				mpRequestCost = 0;
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const startEditPricing = (pricing: ModelPricing) => {
		editingPricingId = pricing.id;
		mpModelId = pricing.model_id;
		mpDisplayName = pricing.display_name || '';
		mpInputCost = pricing.input_cost_per_1k_tokens;
		mpOutputCost = pricing.output_cost_per_1k_tokens;
		mpRequestCost = pricing.per_request_cost;
		mpCurrency = pricing.currency;
	};

	const cancelEditPricing = () => {
		editingPricingId = null;
		mpModelId = '';
		mpDisplayName = '';
		mpInputCost = 0;
		mpOutputCost = 0;
		mpRequestCost = 0;
		mpCurrency = 'VND';
	};

	const toggleModelPricingActive = async (pricing: ModelPricing) => {
		const nextActive = pricing.is_active === 'true' ? false : true;
		await updateAdminModelPricing(localStorage.token, pricing.id, { is_active: nextActive })
			.then(async () => {
				toast.success($i18n.t('Model pricing updated'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const removeModelPricing = async (pricing: ModelPricing) => {
		await deleteAdminModelPricing(localStorage.token, pricing.id)
			.then(async () => {
				toast.success($i18n.t('Model pricing deleted'));
				await loadData();
			})
			.catch((error) => toast.error(`${error}`));
	};
</script>

<div class="px-4 lg:px-6 py-5 space-y-5">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-xl font-bold flex items-center gap-2">
				<svg class="size-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" /></svg>
				{$i18n.t('Billing Admin')}
			</h1>
			<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Manage API keys, model pricing, payments and revenue')}</p>
		</div>
		<PageToolbar />
	</div>

	{#if loading}
		<div class="text-center py-20 text-gray-500">
			<div class="animate-spin w-6 h-6 border-2 border-gray-300 border-t-gray-800 rounded-full mx-auto mb-3"></div>
			{$i18n.t('Loading...')}
		</div>
	{:else}
		<!-- Summary Cards -->
		{#if summary}
			<div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
							<LockClosed className="size-3.5 text-blue-600 dark:text-blue-400" />
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Total Keys')}</div>
					<div class="text-lg font-bold">{summary.total_keys}</div>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
							<CheckCircle className="size-3.5 text-emerald-600 dark:text-emerald-400" />
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Active')}</div>
					<div class="text-lg font-bold">{summary.active_keys}</div>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
							<Bolt className="size-3.5 text-violet-600 dark:text-violet-400" />
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Credits')}</div>
					<div class="text-lg font-bold">{summary.total_credits_remaining.toLocaleString()}</div>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
							<svg class="size-3.5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Pending')}</div>
					<div class="text-lg font-bold">{summary.pending_topups}</div>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center">
							<svg class="size-3.5 text-pink-600 dark:text-pink-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Invoices')}</div>
					<div class="text-lg font-bold">{summary.paid_invoices}</div>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-3.5">
					<div class="flex items-center gap-2 mb-1.5">
						<div class="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
							<svg class="size-3.5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
						</div>
					</div>
					<div class="text-[10px] text-gray-500 uppercase tracking-wider">{$i18n.t('Revenue')}</div>
					<div class="text-lg font-bold">${summary.total_revenue.toFixed(2)}</div>
				</div>
			</div>
		{/if}

		<!-- Tab Navigation -->
		<div class="flex items-center gap-1 p-1 rounded-xl bg-gray-50 dark:bg-gray-900/40 overflow-x-auto">
			{#each [
				{ id: 'keys', label: 'API Keys', icon: 'key' },
				{ id: 'pricing', label: 'Pricing', icon: 'tag' },
				{ id: 'payments', label: 'Payments', icon: 'card' },
				{ id: 'topups', label: 'Top-ups', icon: 'plus' },
				{ id: 'analytics', label: 'Analytics', icon: 'chart' },
				{ id: 'audit', label: 'Audit', icon: 'log' },
				{ id: 'email', label: 'Email', icon: 'mail' }
			] as tab}
				<button
					class="px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5
						{adminTab === tab.id ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					on:click={() => (adminTab = tab.id as typeof adminTab)}
				>
					{#if tab.icon === 'key'}<LockClosed className="size-3.5" />
					{:else if tab.icon === 'tag'}<Sparkles className="size-3.5" />
					{:else if tab.icon === 'card'}<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" /></svg>
					{:else if tab.icon === 'plus'}<Plus className="size-3.5" />
					{:else if tab.icon === 'chart'}<ChartBar className="size-3.5" />
					{:else if tab.icon === 'mail'}<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
					{:else}<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
					{/if}
					{$i18n.t(tab.label)}
				</button>
			{/each}
		</div>

		<!-- Keys Tab -->
		{#if adminTab === 'keys'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<LockClosed className="size-4 text-blue-500" />
						{$i18n.t('API Keys')}
					</h3>
					<div class="flex items-center gap-2 text-xs">
						<span class="text-gray-500">{$i18n.t('Credit delta')}:</span>
						<input class="w-20 px-2 py-1 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-xs" bind:value={creditDelta} type="number" min="1" />
					</div>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('User')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Key')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Plan')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Credits')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Requests')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Status')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Actions')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#each keys as key}
								<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
									<td class="px-4 py-2.5 font-mono text-gray-500 max-w-[120px] truncate">{key.user_id}</td>
									<td class="px-4 py-2.5 font-mono text-gray-500">{key.key_masked}</td>
									<td class="px-4 py-2.5 capitalize">{key.plan_name ?? '-'}</td>
									<td class="px-4 py-2.5 text-right font-medium">{key.credits_remaining.toLocaleString()}</td>
									<td class="px-4 py-2.5 text-right">{key.total_requests.toLocaleString()}</td>
									<td class="px-4 py-2.5">
										<span class="px-2 py-0.5 rounded-full text-xs font-medium {statusColor(key.status)}">{key.status}</span>
									</td>
									<td class="px-4 py-2.5">
										<div class="flex items-center gap-1.5 justify-end">
											<button
												class="px-2 py-1 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-800/40 text-xs font-medium transition-colors"
												on:click={() => adjustCredits(key, creditDelta)}
											>+{creditDelta}</button>
											<button
												class="px-2 py-1 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-800/40 text-xs font-medium transition-colors"
												on:click={() => adjustCredits(key, -creditDelta)}
											>-{creditDelta}</button>
											<button
												class="px-2.5 py-1 rounded-lg text-xs font-medium transition-colors
													{key.status === 'active' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 hover:bg-amber-200' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-200'}"
												on:click={() => toggleStatus(key)}
											>
												{key.status === 'active' ? $i18n.t('Suspend') : $i18n.t('Activate')}
											</button>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>

		<!-- Pricing Tab -->
		{:else if adminTab === 'pricing'}
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
				<!-- Plans (read-only) -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<Star className="size-4 text-violet-500" />
						{$i18n.t('Published Plans')}
					</h3>
					{#if plans.length === 0}
						<p class="text-xs text-gray-500">{$i18n.t('No plans configured')}</p>
					{:else}
						<div class="space-y-2">
							{#each plans as plan, i}
								<div class="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-900/40">
									<div class="w-9 h-9 rounded-lg bg-gradient-to-br {i === 0 ? 'from-gray-500 to-gray-600' : i === 1 ? 'from-blue-500 to-violet-600' : 'from-violet-500 to-fuchsia-600'} flex items-center justify-center text-white flex-shrink-0">
										{#if i === 0}<Bolt className="size-4" />
										{:else if i === 1}<Sparkles className="size-4" />
										{:else}<Star className="size-4" />
										{/if}
									</div>
									<div class="flex-1 min-w-0">
										<div class="font-medium text-sm">{plan.name} · <span class="text-gray-500">${plan.monthly_price_usd}/mo</span></div>
										<div class="text-xs text-gray-500">{plan.included_credits.toLocaleString()} credits · RPM {plan.rpm_limit} · {plan.support_tier}</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Model Pricing -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<Sparkles className="size-4 text-amber-500" />
						{$i18n.t('Model Pricing')}
						{#if editingPricingId}
							<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">{$i18n.t('Editing')}</span>
						{/if}
					</h3>
					<p class="text-xs text-gray-500">{$i18n.t('Set token-based pricing per model. Use glob patterns (e.g. gpt-4*) for families.')}</p>

					<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
						<input class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpModelId} placeholder="model_id" />
						<input class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpDisplayName} placeholder="display name" />
						<input class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpInputCost} type="number" step="0.0001" placeholder="input $/1K" />
						<input class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpOutputCost} type="number" step="0.0001" placeholder="output $/1K" />
						<input class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpRequestCost} type="number" step="0.0001" placeholder="per-req $" />
						<select class="px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={mpCurrency}>
							<option value="USD">🇺🇸 USD</option>
							<option value="VND">🇻🇳 VND</option>
							<option value="EUR">🇪🇺 EUR</option>
							<option value="GBP">🇬🇧 GBP</option>
							<option value="JPY">🇯🇵 JPY</option>
							<option value="CNY">🇨🇳 CNY</option>
							<option value="KRW">🇰🇷 KRW</option>
							<option value="SGD">🇸🇬 SGD</option>
							<option value="THB">🇹🇭 THB</option>
							<option value="AUD">🇦🇺 AUD</option>
							<option value="INR">🇮🇳 INR</option>
							<option value="MYR">🇲🇾 MYR</option>
							<option value="PHP">🇵🇭 PHP</option>
							<option value="IDR">🇮🇩 IDR</option>
						</select>
					</div>
					<button class="px-4 py-2 rounded-xl bg-black text-white dark:bg-white dark:text-black text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-1.5" on:click={createModelPricing}>
						{#if editingPricingId}
							<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
							{$i18n.t('Update Pricing')}
						{:else}
							<Plus className="size-3.5" />
							{$i18n.t('Add Pricing')}
						{/if}
					</button>
					{#if editingPricingId}
						<button class="px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-xs font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" on:click={cancelEditPricing}>
							{$i18n.t('Cancel')}
						</button>
					{/if}

					<div class="space-y-1.5 max-h-64 overflow-y-auto">
						{#if modelPricings.length === 0}
							<p class="text-xs text-gray-400 py-2">{$i18n.t('No model pricing configured. Flat 1-credit-per-request is used.')}</p>
						{:else}
							{#each modelPricings as mp}
								<div class="flex items-center justify-between p-2.5 rounded-xl transition-colors {editingPricingId === mp.id ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-300 dark:ring-blue-700' : 'bg-gray-50 dark:bg-gray-900/40'}">
									<div class="min-w-0">
										<div class="flex items-center gap-1.5">
											<span class="w-2 h-2 rounded-full {mp.is_active === 'true' ? 'bg-emerald-500' : 'bg-gray-400'} flex-shrink-0"></span>
											<span class="font-medium text-xs">{mp.display_name || mp.model_id}</span>
											<span class="text-[10px] text-gray-400">{mp.currency}</span>
										</div>
										<div class="text-[10px] text-gray-500 font-mono mt-0.5 ml-3.5">{mp.model_id} · in: ${mp.input_cost_per_1k_tokens} · out: ${mp.output_cost_per_1k_tokens} · req: ${mp.per_request_cost}</div>
									</div>
									<div class="flex items-center gap-1 flex-shrink-0">
										<button class="p-1 rounded-lg text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors" title={$i18n.t('Edit')} on:click={() => startEditPricing(mp)}>
											<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" /></svg>
										</button>
										<button class="px-2 py-1 rounded-lg text-xs font-medium transition-colors {mp.is_active === 'true' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30'}" on:click={() => toggleModelPricingActive(mp)}>
											{mp.is_active === 'true' ? $i18n.t('Disable') : $i18n.t('Enable')}
										</button>
										<button class="p-1 rounded-lg text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors" on:click={() => removeModelPricing(mp)}>
											<GarbageBin className="size-3.5" />
										</button>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				</div>
			</div>

		<!-- Payments Tab -->
		{:else if adminTab === 'payments'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 mb-4">
				<div class="flex items-start justify-between gap-3">
					<div>
						<h3 class="font-semibold text-sm flex items-center gap-2">
							<Sparkles className="size-4 text-violet-500" />
							{$i18n.t('Billing Workflow Automation')}
						</h3>
						<p class="text-xs text-gray-500 mt-1">{$i18n.t('When enabled, top-up requests are approved instantly and invoices are issued automatically.')}</p>
					</div>
					<button
						class="px-3 py-1.5 rounded-xl text-xs font-medium transition-colors {billingSettings.auto_approve_topups
							? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
							: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'}"
						on:click={toggleAutoApproveTopups}
						disabled={savingBillingSettings}
					>
						{billingSettings.auto_approve_topups ? $i18n.t('Auto-Approve: ON') : $i18n.t('Auto-Approve: OFF')}
					</button>
				</div>
			</div>

			<!-- Default Currency Setting -->
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 mb-4">
				<div class="flex items-start justify-between gap-3">
					<div>
						<h3 class="font-semibold text-sm flex items-center gap-2">
							<svg class="size-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
							{$i18n.t('Default Currency')}
						</h3>
						<p class="text-xs text-gray-500 mt-1">{$i18n.t('Used as the default currency for user top-up forms and model pricing.')}</p>
					</div>
					<div class="flex items-center gap-2">
						<select
							class="px-3 py-1.5 rounded-xl text-xs font-medium border border-gray-200 dark:border-gray-700 bg-transparent"
							bind:value={billingSettings.default_currency}
							on:change={async () => {
								savingBillingSettings = true;
								await updateAdminBillingSettings(localStorage.token, billingSettings)
									.then((settings) => {
										billingSettings = settings;
										toast.success($i18n.t('Default currency updated'));
									})
									.catch((error) => toast.error(`${error}`));
								savingBillingSettings = false;
							}}
						>
							<option value="USD">🇺🇸 USD ($)</option>
							<option value="VND">🇻🇳 VND (₫)</option>
							<option value="EUR">🇪🇺 EUR (€)</option>
							<option value="GBP">🇬🇧 GBP (£)</option>
							<option value="JPY">🇯🇵 JPY (¥)</option>
							<option value="CNY">🇨🇳 CNY (¥)</option>
							<option value="KRW">🇰🇷 KRW (₩)</option>
							<option value="SGD">🇸🇬 SGD (S$)</option>
							<option value="THB">🇹🇭 THB (฿)</option>
							<option value="AUD">🇦🇺 AUD (A$)</option>
							<option value="CAD">🇨🇦 CAD (C$)</option>
							<option value="INR">🇮🇳 INR (₹)</option>
							<option value="MYR">🇲🇾 MYR (RM)</option>
							<option value="PHP">🇵🇭 PHP (₱)</option>
							<option value="IDR">🇮🇩 IDR (Rp)</option>
							<option value="TWD">🇹🇼 TWD (NT$)</option>
							<option value="HKD">🇭🇰 HKD (HK$)</option>
							<option value="CHF">🇨🇭 CHF (Fr)</option>
							<option value="BRL">🇧🇷 BRL (R$)</option>
						</select>
					</div>
				</div>
			</div>

			<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
				<!-- Add Payment Account -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" /></svg>
						{$i18n.t('Add Payment Account')}
					</h3>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
						<div>
							<label for="billing-provider" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Provider')}</label>
							<div class="relative" bind:this={providerMenuRef}>
								<button
									id="billing-provider"
									type="button"
									class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm flex items-center justify-between"
									on:click={() => (providerMenuOpen = !providerMenuOpen)}
								>
									<span class="flex items-center gap-2 min-w-0">
										<PaymentProviderIcon provider={provider} size="size-6" />
										<span class="truncate">{getProviderLabel(provider)}</span>
									</span>
									<svg class="size-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
								</button>
								{#if providerMenuOpen}
									<div class="absolute z-20 mt-1 w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg p-1">
										{#each providerOptions as option}
											<button
												type="button"
												class="w-full px-2.5 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors {provider === option.value ? 'bg-gray-100 dark:bg-gray-800' : ''}"
												on:click={() => {
													provider = option.value;
													providerMenuOpen = false;
												}}
											>
												<PaymentProviderIcon provider={option.value} size="size-5" />
												<span>{option.label}</span>
											</button>
										{/each}
									</div>
								{/if}
							</div>
						</div>
						<div>
							<label for="billing-account-name" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Account Name')}</label>
							<input id="billing-account-name" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={accountName} />
						</div>
						<div>
							<label for="billing-account-number" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Account Number')}</label>
							<input id="billing-account-number" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={accountNumber} />
						</div>
						<div>
							<label for="billing-qr-url" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('QR Code')}</label>
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									<input id="billing-qr-url" class="flex-1 px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={qrCodeUrl} placeholder={$i18n.t('Paste URL or upload image')} />
									<input type="file" accept="image/*" class="hidden" bind:this={qrFileInput}
										on:change={(e) => {
											const input = e.target as HTMLInputElement;
											const file = input?.files?.[0];
											if (file) {
												if (file.size > 2 * 1024 * 1024) {
													toast.error($i18n.t('Image must be under 2MB'));
													return;
												}
												const reader = new FileReader();
												reader.onload = () => { qrCodeUrl = reader.result as string; };
												reader.readAsDataURL(file);
											}
										}}
									/>
									<button type="button" class="px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-xs font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1.5 whitespace-nowrap"
										on:click={() => qrFileInput?.click()}>
										<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" /></svg>
										{$i18n.t('Upload')}
									</button>
								</div>
								{#if qrCodeUrl}
									<div class="relative inline-block">
										<img src={qrCodeUrl} alt="QR Preview" class="w-24 h-24 rounded-lg border border-gray-200 dark:border-gray-700 object-contain bg-white" />
										<button type="button" class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
											on:click={() => {
												qrCodeUrl = '';
												if (qrFileInput) { qrFileInput.value = ''; }
											}}>
											×
										</button>
									</div>
								{/if}
							</div>
						</div>
						<div class="sm:col-span-2">
							<label for="billing-webhook-secret" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Webhook Secret')}</label>
							<input id="billing-webhook-secret" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm font-mono" bind:value={webhookSecret}
								placeholder={provider === 'stripe' ? 'whsec_...' : provider === 'vnpay' ? 'VNPay hash secret' : provider === 'momo' ? 'MoMo secret key' : 'webhook secret'} />
						</div>
					</div>

					{#if provider !== 'generic' && provider !== 'bank_transfer'}
						<div class="rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-3 text-xs text-blue-800 dark:text-blue-200 space-y-1">
							<div class="font-medium flex items-center gap-1">
								<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" /></svg>
								Webhook URL:
							</div>
							<code class="block bg-blue-100 dark:bg-blue-800/50 px-2 py-1 rounded-lg text-[10px] break-all">{window.location.origin}/api/v1/api-keys/webhooks/payment/{provider}</code>
							{#if provider === 'stripe'}
								<p>Configure in Stripe Dashboard → Webhooks. Events: <code>checkout.session.completed</code>, <code>payment_intent.succeeded</code>.</p>
							{:else if provider === 'vnpay'}
								<p>Set as VNPay IPN URL. Hash secret = <code>vnp_HashSecret</code>. Pass topup ID as <code>vnp_OrderInfo</code>.</p>
							{:else if provider === 'momo'}
								<p>Set as MoMo IPN/notify URL. Pass topup ID as <code>orderId</code>.</p>
							{:else if provider === 'paypal'}
								<p>Configure in PayPal Developer Dashboard → Webhooks. Event: <code>PAYMENT.CAPTURE.COMPLETED</code>.</p>
							{/if}
						</div>
					{/if}

					<div>
						<label for="billing-instructions" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Instructions')}</label>
						<textarea id="billing-instructions" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" rows="2" bind:value={instructions} placeholder={$i18n.t('Payment instructions for users')}></textarea>
					</div>

					<button class="px-4 py-2 rounded-xl bg-black text-white dark:bg-white dark:text-black text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-1.5" on:click={createPaymentAccount}>
						<Plus className="size-3.5" />
						{$i18n.t('Add Account')}
					</button>
				</div>

				<!-- Existing accounts -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<svg class="size-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" /></svg>
						{$i18n.t('Existing Accounts')}
						<span class="text-xs font-normal text-gray-400">({paymentAccounts.length})</span>
					</h3>
					{#if paymentAccounts.length === 0}
						<p class="text-xs text-gray-400">{$i18n.t('No payment accounts configured')}</p>
					{:else}
						<div class="space-y-2.5">
							{#each paymentAccounts as account}
								<div class="flex items-start gap-3 p-4 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800">
									<PaymentProviderIcon provider={account.provider} size="size-10" />
									<div class="flex-1 min-w-0">
										<div class="font-medium text-sm flex items-center gap-1.5">
											<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase
												{account.provider === 'stripe' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' :
												 account.provider === 'vnpay' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' :
												 account.provider === 'momo' ? 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300' :
												 account.provider === 'paypal' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' :
												 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'}">{account.provider}</span>
											{account.account_name}
										</div>
										<div class="text-xs text-gray-500 font-mono mt-0.5">{account.account_number}</div>
										{#if account.instructions}
											<div class="text-[11px] text-gray-400 mt-1 italic">{account.instructions}</div>
										{/if}
									</div>
									{#if account.qr_code_url}
										<img src={account.qr_code_url} alt="QR" class="w-14 h-14 rounded-lg border border-gray-200 dark:border-gray-700 object-contain bg-white flex-shrink-0" />
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- Invoices -->
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center justify-between">
					<div class="flex items-center gap-2">
						<svg class="size-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
						{$i18n.t('Invoices')}
					</div>
					<span class="text-xs font-normal text-gray-400">{invoices.length} {$i18n.t('total')}</span>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Invoice')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('User')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Provider')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Amount')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Credits')}</th>
								<th class="px-4 py-2.5 text-center font-medium text-gray-500">{$i18n.t('Status')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Date')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if invoices.length === 0}
								<tr><td class="px-4 py-8 text-gray-400 text-center" colspan="7">
									<div class="flex flex-col items-center gap-2">
										<svg class="size-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
										{$i18n.t('No invoices yet')}
									</div>
								</td></tr>
							{:else}
								{#each invoices as invoice}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-3">
											<div class="flex items-center gap-2">
												<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center flex-shrink-0">
													<svg class="size-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
												</div>
												<div>
													<div class="font-mono text-[10px] text-gray-400">#{invoice.id.slice(0, 8)}</div>
												</div>
											</div>
										</td>
										<td class="px-4 py-3">
											<div class="flex items-center gap-2">
												<div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-violet-500 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
													{(invoice.user_name || invoice.user_id || '?').charAt(0).toUpperCase()}
												</div>
												<div>
													<div class="font-medium text-xs">{invoice.user_name || invoice.user_id.slice(0, 8)}</div>
													<div class="text-[10px] text-gray-400 font-mono">{invoice.user_id.slice(0, 8)}...</div>
												</div>
											</div>
										</td>
										<td class="px-4 py-3">
											<div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg bg-gray-100 dark:bg-gray-800">
												<PaymentProviderIcon provider={getPaymentProviderByTopupId(invoice.topup_request_id)} size="size-4" />
												<span class="text-[10px] uppercase font-semibold text-gray-600 dark:text-gray-300">{getPaymentProviderByTopupId(invoice.topup_request_id)}</span>
											</div>
										</td>
										<td class="px-4 py-3 text-right">
											<span class="font-semibold text-sm">{invoice.amount.toLocaleString()}</span>
											<span class="text-[10px] text-gray-400 ml-0.5">{invoice.currency}</span>
										</td>
										<td class="px-4 py-3 text-right">
											<span class="px-2 py-0.5 rounded-lg bg-violet-50 text-violet-700 dark:bg-violet-900/20 dark:text-violet-300 text-xs font-medium">{invoice.credits.toLocaleString()}</span>
										</td>
										<td class="px-4 py-3 text-center">
											<span class="px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wide {statusColor(invoice.status)}">{invoice.status}</span>
										</td>
										<td class="px-4 py-3 text-right text-gray-500 text-[11px]">{new Date((invoice.created_at ?? 0) * 1000).toLocaleDateString()}</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

		<!-- Top-ups Tab -->
		{:else if adminTab === 'topups'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<Plus className="size-4 text-emerald-500" />
						{$i18n.t('Top-up Requests')}
						<span class="text-xs font-normal text-gray-400">({topups.length})</span>
					</h3>
					<div class="flex items-center gap-2 text-xs">
						<span class="text-gray-500">{$i18n.t('Credits to approve')}:</span>
						<input class="w-20 px-2 py-1 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-xs" bind:value={approveCredits} type="number" min="1" />
					</div>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('User')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Provider')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Amount')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Ref')}</th>
								<th class="px-4 py-2.5 text-center font-medium text-gray-500">{$i18n.t('Status')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Date')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Actions')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if topups.length === 0}
								<tr><td class="px-4 py-8 text-gray-400 text-center" colspan="7">
									<div class="flex flex-col items-center gap-2">
										<svg class="size-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
										{$i18n.t('No top-up requests')}
									</div>
								</td></tr>
							{:else}
								{#each topups as topup}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-3">
											<div class="flex items-center gap-2">
												<div class="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
													{(topup.user_name || topup.user_id || '?').charAt(0).toUpperCase()}
												</div>
												<div>
													<div class="font-medium text-xs">{topup.user_name || topup.user_id.slice(0, 8)}</div>
													<div class="text-[10px] text-gray-400 font-mono">{topup.user_id.slice(0, 8)}...</div>
												</div>
											</div>
										</td>
										<td class="px-4 py-3">
											<div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg bg-gray-100 dark:bg-gray-800">
												<PaymentProviderIcon provider={getPaymentProviderByAccountId(topup.payment_account_id)} size="size-4" />
												<span class="text-[10px] uppercase font-semibold text-gray-600 dark:text-gray-300">{getPaymentProviderByAccountId(topup.payment_account_id)}</span>
											</div>
										</td>
										<td class="px-4 py-3 text-right">
											<span class="font-semibold text-sm">{topup.amount.toLocaleString()}</span>
											<span class="text-[10px] text-gray-400 ml-0.5">{topup.currency}</span>
										</td>
										<td class="px-4 py-3 font-mono text-gray-500">{topup.tx_ref ?? '-'}</td>
										<td class="px-4 py-3 text-center">
											<span class="px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wide {statusColor(topup.status)}">{topup.status}</span>
										</td>
										<td class="px-4 py-3 text-right text-gray-500 text-[11px]">{new Date((topup.created_at ?? 0) * 1000).toLocaleDateString()}</td>
										<td class="px-4 py-3">
											{#if topup.status === 'pending'}
												<div class="flex items-center gap-1.5 justify-end">
													<button
														class="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-200 text-xs font-medium transition-colors flex items-center gap-1"
														on:click={() => approveTopup(topup)}
													>
														<CheckCircle className="size-3" />
														{$i18n.t('Approve')}
													</button>
													<button
														class="px-2.5 py-1 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-200 text-xs font-medium transition-colors"
														on:click={() => rejectTopup(topup)}
													>
														{$i18n.t('Reject')}
													</button>
												</div>
											{/if}
										</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

		<!-- Analytics Tab -->
		{:else if adminTab === 'analytics'}
			<!-- Usage Charts -->
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5">
					<h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
						<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" /></svg>
						{$i18n.t('Daily Usage (30 days)')}
					</h3>
					<BarChart
						data={usageDaily.map((d) => ({ label: d.date, value: d.requests, secondary: d.total_cost }))}
						valueLabel="Requests"
						secondaryLabel="Cost ($)"
						barColor="#3b82f6"
						secondaryColor="#f59e0b"
						height={220}
					/>
				</div>
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5">
					<h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
						<Sparkles className="size-4 text-violet-500" />
						{$i18n.t('Usage by Model')}
					</h3>
					<BarChart
						data={usageByModel.map((m) => ({ label: m.model.length > 20 ? m.model.slice(0, 18) + '..' : m.model, value: m.requests, secondary: m.total_tokens }))}
						valueLabel="Requests"
						secondaryLabel="Tokens"
						barColor="#8b5cf6"
						secondaryColor="#10b981"
						height={220}
					/>
				</div>
			</div>

			<!-- Revenue Table -->
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center gap-2">
					<svg class="size-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
					{$i18n.t('Revenue Daily (30 days)')}
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Date')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Revenue')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Credits')}</th>
								<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Invoices')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if revenueDaily.length === 0}
								<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="4">{$i18n.t('No revenue data')}</td></tr>
							{:else}
								{#each revenueDaily as daily}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-2.5">{daily.date}</td>
										<td class="px-4 py-2.5 text-right font-medium">${daily.revenue.toFixed(2)}</td>
										<td class="px-4 py-2.5 text-right">{daily.credits.toLocaleString()}</td>
										<td class="px-4 py-2.5 text-right">{daily.invoices}</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

			<!-- Usage Analytics Tables -->
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
					<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center gap-2">
						<ChartBar className="size-4 text-blue-500" />
						{$i18n.t('Usage Daily')}
					</div>
					<div class="overflow-x-auto">
						<table class="w-full text-xs">
							<thead class="bg-gray-50 dark:bg-gray-900/40">
								<tr>
									<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Date')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Reqs')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Prompt')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Compl')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Cost')}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
								{#if usageDaily.length === 0}
									<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="5">{$i18n.t('No usage data')}</td></tr>
								{:else}
									{#each usageDaily as ud}
										<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
											<td class="px-4 py-2.5">{ud.date}</td>
											<td class="px-4 py-2.5 text-right">{ud.requests.toLocaleString()}</td>
											<td class="px-4 py-2.5 text-right">{ud.prompt_tokens.toLocaleString()}</td>
											<td class="px-4 py-2.5 text-right">{ud.completion_tokens.toLocaleString()}</td>
											<td class="px-4 py-2.5 text-right font-mono">${ud.total_cost.toFixed(4)}</td>
										</tr>
									{/each}
								{/if}
							</tbody>
						</table>
					</div>
				</div>

				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
					<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center gap-2">
						<Sparkles className="size-4 text-violet-500" />
						{$i18n.t('Usage by Model')}
					</div>
					<div class="overflow-x-auto">
						<table class="w-full text-xs">
							<thead class="bg-gray-50 dark:bg-gray-900/40">
								<tr>
									<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Model')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Requests')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Tokens')}</th>
									<th class="px-4 py-2.5 text-right font-medium text-gray-500">{$i18n.t('Cost')}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
								{#if usageByModel.length === 0}
									<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="4">{$i18n.t('No usage data')}</td></tr>
								{:else}
									{#each usageByModel as um}
										<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
											<td class="px-4 py-2.5 font-mono">{um.model}</td>
											<td class="px-4 py-2.5 text-right">{um.requests.toLocaleString()}</td>
											<td class="px-4 py-2.5 text-right">{um.total_tokens.toLocaleString()}</td>
											<td class="px-4 py-2.5 text-right font-mono">${um.total_cost.toFixed(4)}</td>
										</tr>
									{/each}
								{/if}
							</tbody>
						</table>
					</div>
				</div>
			</div>

		<!-- Audit Tab -->
		{:else if adminTab === 'audit'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center gap-2">
					<svg class="size-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
					{$i18n.t('Audit Trail')}
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('When')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Actor')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Action')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Target')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if auditLogs.length === 0}
								<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="4">{$i18n.t('No audit events')}</td></tr>
							{:else}
								{#each auditLogs as log}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-2.5 text-gray-500">{new Date((log.created_at ?? 0) * 1000).toLocaleString()}</td>
										<td class="px-4 py-2.5">
											<div class="flex items-center gap-1.5">
												<div class="w-5 h-5 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center text-white text-[8px] font-bold flex-shrink-0">
													{(log.actor_name || log.actor_id || '?').charAt(0).toUpperCase()}
												</div>
												<span class="text-xs font-medium">{log.actor_name || log.actor_id.slice(0, 8)}</span>
											</div>
										</td>
										<td class="px-4 py-2.5">
											<span class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">{log.action}</span>
										</td>
										<td class="px-4 py-2.5 text-gray-500">{log.target_type}:{log.target_id}</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

		<!-- Email / SMTP Tab -->
		{:else if adminTab === 'email'}
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
				<!-- SMTP Configuration -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
						{$i18n.t('SMTP Configuration')}
					</h3>
					<p class="text-xs text-gray-500">{$i18n.t('Configure email server for billing notifications (top-up receipts, invoices, low credit warnings).')}</p>

					<div class="space-y-3">
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label for="smtp-host" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('SMTP Host')}</label>
								<input id="smtp-host" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={smtpSettings.smtp_host} placeholder="smtp.gmail.com" />
							</div>
							<div>
								<label for="smtp-port" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('SMTP Port')}</label>
								<input id="smtp-port" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" type="number" bind:value={smtpSettings.smtp_port} placeholder="587" />
							</div>
						</div>
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label for="smtp-user" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Username')}</label>
								<input id="smtp-user" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={smtpSettings.smtp_user} placeholder="user@example.com" />
							</div>
							<div>
								<label for="smtp-pass" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Password')}</label>
								<input id="smtp-pass" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" type="password" bind:value={smtpPassword} placeholder="••••••••" />
							</div>
						</div>
						<div>
							<label for="smtp-from" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('From Address')}</label>
							<input id="smtp-from" class="w-full px-3 py-2 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={smtpSettings.smtp_from} placeholder="noreply@yourcompany.com" />
						</div>
						<div class="flex items-center gap-3">
							<label class="flex items-center gap-2 cursor-pointer">
								<input type="checkbox" class="rounded border-gray-300 dark:border-gray-600" bind:checked={smtpSettings.smtp_tls} />
								<span class="text-xs font-medium text-gray-600 dark:text-gray-400">{$i18n.t('Use TLS')}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer">
								<input type="checkbox" class="rounded border-gray-300 dark:border-gray-600" bind:checked={smtpSettings.enable_billing_emails} />
								<span class="text-xs font-medium text-gray-600 dark:text-gray-400">{$i18n.t('Enable Billing Emails')}</span>
							</label>
						</div>
					</div>

					<div class="flex items-center gap-2">
						<button
							class="px-4 py-2 rounded-xl bg-black text-white dark:bg-white dark:text-black text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-1.5"
							disabled={savingSmtp}
							on:click={async () => {
								savingSmtp = true;
								const payload = { ...smtpSettings };
								if (smtpPassword) payload.smtp_password = smtpPassword;
								await updateAdminSmtpSettings(localStorage.token, payload)
									.then((res) => {
										smtpSettings = res;
										smtpPassword = '';
										toast.success($i18n.t('SMTP settings saved'));
									})
									.catch((error) => toast.error(`${error}`));
								savingSmtp = false;
							}}
						>
							{savingSmtp ? $i18n.t('Saving...') : $i18n.t('Save SMTP Settings')}
						</button>
						<button
							class="px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-xs font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1.5"
							disabled={testingSmtp || !smtpSettings.smtp_host}
							on:click={async () => {
								testingSmtp = true;
								await testAdminSmtp(localStorage.token)
									.then((res) => toast.success(res.message))
									.catch((error) => toast.error(`${error}`));
								testingSmtp = false;
							}}
						>
							{testingSmtp ? $i18n.t('Sending...') : $i18n.t('Send Test Email')}
						</button>
					</div>
				</div>

				<!-- Email Notifications Info -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
					<h3 class="font-semibold text-sm flex items-center gap-2">
						<svg class="size-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" /></svg>
						{$i18n.t('Notification Events')}
					</h3>
					<p class="text-xs text-gray-500">{$i18n.t('When SMTP is configured and billing emails are enabled, the following notifications are sent automatically:')}</p>

					<div class="space-y-2.5">
						{#each [
							{ event: 'Top-up Submitted', desc: 'User receives confirmation when they submit a top-up request', badge: 'badge-info' },
							{ event: 'Top-up Approved', desc: 'User is notified when credits are added to their account', badge: 'badge-success' },
							{ event: 'Top-up Rejected', desc: 'User is informed if their top-up request is declined', badge: 'badge-danger' },
							{ event: 'Invoice Issued', desc: 'User receives invoice details after payment is processed', badge: 'badge-info' },
							{ event: 'Low Credits', desc: 'User receives a warning when credits fall below threshold', badge: 'badge-warning' },
							{ event: 'Admin Alert', desc: 'Admin receives notification of new pending top-up requests', badge: 'badge-info' },
						] as item}
							<div class="flex items-start gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-900/40">
								<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap
									{item.badge === 'badge-success' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30' : ''}
									{item.badge === 'badge-danger' ? 'bg-red-100 text-red-700 dark:bg-red-900/30' : ''}
									{item.badge === 'badge-warning' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30' : ''}
									{item.badge === 'badge-info' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30' : ''}
								">{item.event}</span>
								<span class="text-xs text-gray-500">{$i18n.t(item.desc)}</span>
							</div>
						{/each}
					</div>

					<div class="rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 p-3.5">
						<p class="text-xs text-blue-700 dark:text-blue-300 font-medium mb-1">{$i18n.t('Gmail Quick Setup')}</p>
						<p class="text-[11px] text-blue-600 dark:text-blue-400 leading-relaxed">
							{$i18n.t('Host')}: <code class="bg-blue-100 dark:bg-blue-900/30 px-1 rounded">smtp.gmail.com</code> · 
							{$i18n.t('Port')}: <code class="bg-blue-100 dark:bg-blue-900/30 px-1 rounded">587</code> · 
							TLS: ✓ · {$i18n.t('Use an App Password from Google Account settings.')}
						</p>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>
