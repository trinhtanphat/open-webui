<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { copyToClipboard } from '$lib/utils';
	import BarChart from '$lib/components/billing/BarChart.svelte';
	import PaymentProviderIcon from '$lib/components/billing/PaymentProviderIcon.svelte';
	import {
		getApiKeyPlans,
		getBillingSettings,
		createMyTopupRequest,
		getMyApiKeyConsole,
		getMyInvoiceById,
		getMyInvoices,
		getMyTopups,
		getMyUsageSummary,
		getPublicPaymentAccounts,
		regenerateMyApiKey,
		getMyUsageDaily,
		getMyUsageByModel,
		activateMyApiKey,
		type ApiKeyConsole,
		type ApiKeyPlan,
		type BillingSettings,
		type BillingInvoice,
		type PaymentAccount,
		type TopupRequest,
		type UserUsageSummary,
		type UsageDailySummary,
		type UsageByModelSummary
	} from '$lib/apis/api-keys';

	import Bolt from '$lib/components/icons/Bolt.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import Star from '$lib/components/icons/Star.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import ChartBar from '$lib/components/icons/ChartBar.svelte';
	import Clipboard from '$lib/components/icons/Clipboard.svelte';
	import Eye from '$lib/components/icons/Eye.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import CheckCircle from '$lib/components/icons/CheckCircle.svelte';

	const i18n = getContext<any>('i18n');

	let loading = true;
	let apiKey: ApiKeyConsole | null = null;
	let copied = false;
	let showFullKey = false;
	let paymentAccounts: PaymentAccount[] = [];
	let topups: TopupRequest[] = [];
	let invoices: BillingInvoice[] = [];
	let plans: ApiKeyPlan[] = [];
	let usage: UserUsageSummary | null = null;
	let selectedPlanId = 'starter';
	let activeTab: 'overview' | 'topup' | 'invoices' = 'overview';
	let usageDays = 30;
	const usageDayOptions = [7, 30, 90];
	let topupStatusFilter: 'all' | 'pending' | 'approved' | 'rejected' = 'all';
	let invoiceStatusFilter: 'all' | 'paid' | 'pending' | 'rejected' = 'all';

	let selectedPaymentAccountId = '';
	let topupAmount = 10;
	let topupCurrency = 'USD';

	// Will be set from billing settings once loaded
	$: if (billingSettings.default_currency && topupCurrency === 'USD') {
		topupCurrency = billingSettings.default_currency;
	}
	let topupTxRef = '';
	let topupNote = '';
	let selectedPaymentAccount: PaymentAccount | null = null;

	let myUsageDaily: UsageDailySummary[] = [];
	let myUsageByModel: UsageByModelSummary[] = [];
	let billingSettings: BillingSettings = { auto_approve_topups: true, default_currency: 'USD' };
	let activating = false;
	let selectedActivationPlan = 'starter';

	$: selectedPaymentAccount = paymentAccounts.find((item) => item.id === selectedPaymentAccountId) ?? null;
	$: filteredTopups = topupStatusFilter === 'all' ? topups : topups.filter((item) => item.status === topupStatusFilter);
	$: filteredInvoices =
		invoiceStatusFilter === 'all'
			? invoices
			: invoices.filter((item) => item.status === invoiceStatusFilter);

	const planIcons = [Bolt, Sparkles, Star];
	const planColors = [
		'from-gray-500 to-gray-600',
		'from-blue-500 to-violet-600',
		'from-violet-500 to-fuchsia-600'
	];

	const loadConsole = async () => {
		apiKey = await getMyApiKeyConsole(localStorage.token).catch(() => {
			return null;
		});

		paymentAccounts = await getPublicPaymentAccounts(localStorage.token).catch(() => []);
		topups = await getMyTopups(localStorage.token).catch(() => []);
		invoices = await getMyInvoices(localStorage.token).catch(() => []);
		plans = await getApiKeyPlans(localStorage.token).catch(() => []);
		usage = await getMyUsageSummary(localStorage.token).catch(() => null);
		myUsageDaily = await getMyUsageDaily(localStorage.token, usageDays).catch(() => []);
		myUsageByModel = await getMyUsageByModel(localStorage.token, usageDays).catch(() => []);
		billingSettings = await getBillingSettings(localStorage.token).catch(() => ({
			auto_approve_topups: true, default_currency: 'USD'
		}));

		if (!selectedPaymentAccountId && paymentAccounts.length > 0) {
			selectedPaymentAccountId = paymentAccounts[0].id;
		}

		if (apiKey?.plan_name) {
			selectedPlanId = apiKey.plan_name;
		}
	};

	const refreshUsageRange = async (days: number) => {
		usageDays = days;
		myUsageDaily = await getMyUsageDaily(localStorage.token, usageDays).catch(() => []);
		myUsageByModel = await getMyUsageByModel(localStorage.token, usageDays).catch(() => []);
	};

	const activateKey = async () => {
		activating = true;
		try {
			apiKey = await activateMyApiKey(localStorage.token, selectedActivationPlan);
			showFullKey = true;
			toast.success($i18n.t('API key activated! Copy it now — it will not be shown again.'));
			await loadConsole();
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			activating = false;
		}
	};

	const selectPlan = (plan: ApiKeyPlan) => {
		selectedPlanId = plan.id;
		topupAmount = plan.monthly_price_usd;
		topupNote = `Subscribe plan ${plan.name}`;
		activeTab = 'topup';
	};

	onMount(async () => {
		await loadConsole();
		loading = false;
	});

	const regenerate = async () => {
		apiKey = await regenerateMyApiKey(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return apiKey;
		});

		showFullKey = true;
		toast.success($i18n.t('API key regenerated. Copy it now — it will not be shown again.'));
	};

	const submitTopup = async () => {
		if (!apiKey) {
			toast.error($i18n.t('No API key found'));
			return;
		}

		if (!selectedPaymentAccountId) {
			toast.error($i18n.t('Please select a payment account'));
			return;
		}

		await createMyTopupRequest(localStorage.token, {
			api_key_id: apiKey.id,
			payment_account_id: selectedPaymentAccountId,
			amount: Number(topupAmount),
			currency: topupCurrency,
			tx_ref: topupTxRef,
			note: topupNote
		})
			.then(async () => {
				toast.success($i18n.t('Top-up request created'));
				topupTxRef = '';
				topupNote = '';
				await loadConsole();
			})
			.catch((error) => toast.error(`${error}`));
	};

	const exportInvoicePdf = async (invoiceId: string) => {
		const invoice = await getMyInvoiceById(localStorage.token, invoiceId).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (!invoice) return;

		const { default: jsPDF } = await import('jspdf');
		const pdf = new jsPDF('p', 'mm', 'a4');

		let y = 18;
		pdf.setFontSize(16);
		pdf.text('OpenWebUI API Invoice', 14, y);
		y += 10;

		pdf.setFontSize(11);
		const lines = [
			`Invoice ID: ${invoice.id}`,
			`Date: ${new Date(invoice.created_at * 1000).toISOString()}`,
			`User ID: ${invoice.user_id}`,
			`API Key ID: ${invoice.api_key_id}`,
			`Amount: ${invoice.amount} ${invoice.currency}`,
			`Credits: ${invoice.credits}`,
			`Status: ${invoice.status}`,
			`Topup Request ID: ${invoice.topup_request_id ?? '-'}`
		];

		for (const line of lines) {
			pdf.text(line, 14, y);
			y += 7;
		}

		pdf.setFontSize(9);
		y += 4;
		pdf.text('Generated by OpenWebUI Billing Console', 14, y);

		pdf.save(`invoice-${invoice.id}.pdf`);
	};

	const statusColor = (status: string) => {
		switch (status) {
			case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
			case 'approved': case 'paid': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
			case 'pending': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
			case 'rejected': case 'disabled': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
			default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
		}
	};
</script>

<div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold flex items-center gap-2">
				<svg class="size-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" /></svg>
				{$i18n.t('Developer Console')}
			</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t('Manage your API key, credits, and usage')}</p>
		</div>
		<div class="flex items-center gap-2">
			<button class="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" on:click={() => goto('/developer/api-keys/pricing')}>
				{$i18n.t('Pricing')}
			</button>
			<button class="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" on:click={() => goto('/developer/api-keys/guide')}>
				{$i18n.t('Guide')}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="text-center py-20 text-gray-500">
			<div class="animate-spin w-6 h-6 border-2 border-gray-300 border-t-gray-800 rounded-full mx-auto mb-3"></div>
			{$i18n.t('Loading console...')}
		</div>
	{:else if !apiKey}
		<!-- Self-service Activation Flow -->
		<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-8 space-y-6">
			<div class="text-center space-y-3">
				<div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center mx-auto shadow-lg">
					<Bolt className="size-7 text-white" />
				</div>
				<h2 class="text-xl font-bold">{$i18n.t('Activate your API Key')}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">{$i18n.t('Get instant access to the OpenAI-compatible API. Choose a plan and start building — no admin approval needed.')}</p>
			</div>

			<!-- Plan Selector -->
			{#if plans.length > 0}
				<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
					{#each plans as plan, i}
						<button
							class="text-left rounded-xl border-2 p-4 transition-all {selectedActivationPlan === plan.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm' : 'border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-600'}"
							on:click={() => selectedActivationPlan = plan.id}
						>
							<div class="flex items-center gap-2 mb-2">
								<div class="w-7 h-7 rounded-lg bg-gradient-to-br {planColors[i] ?? planColors[0]} flex items-center justify-center">
									<svelte:component this={planIcons[i] ?? planIcons[0]} className="size-3.5 text-white" />
								</div>
								<span class="font-semibold text-sm">{plan.name}</span>
								{#if i === 1}
									<span class="ml-auto px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-[10px] font-bold">Popular</span>
								{/if}
							</div>
							<div class="text-lg font-bold">${plan.monthly_price_usd}<span class="text-xs font-normal text-gray-500">/mo</span></div>
							<div class="text-xs text-gray-500 mt-1">{plan.included_credits.toLocaleString()} credits • {plan.rpm_limit} RPM</div>
						</button>
					{/each}
				</div>
			{/if}

			<!-- Activate Button -->
			<div class="text-center space-y-3">
				<button
					class="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-black dark:bg-white text-white dark:text-black font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
					on:click={activateKey}
					disabled={activating}
				>
					{#if activating}
						<div class="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></div>
						{$i18n.t('Activating...')}
					{:else}
						<Bolt className="size-4" />
						{$i18n.t('Activate API Key')}
					{/if}
				</button>
				<div class="text-xs text-gray-400">{$i18n.t('You can upgrade your plan or top up credits at any time')}</div>
			</div>

			<!-- What you get -->
			<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-4 space-y-2">
				<h3 class="text-sm font-semibold">{$i18n.t('What you get')}</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs text-gray-600 dark:text-gray-400">
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('OpenAI-compatible API endpoint')}</div>
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('Access to all enabled models')}</div>
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('Usage tracking & analytics')}</div>
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('Top-up with multiple payment methods')}</div>
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('Per-model token-based billing')}</div>
					<div class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> {$i18n.t('Web chat is NOT affected')}</div>
				</div>
			</div>
		</div>
	{:else}
		<!-- Secret Key Card -->
		<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
			<div class="flex items-center justify-between">
				<h2 class="font-semibold flex items-center gap-2">
					<LockClosed className="size-4 text-amber-500" />
					{$i18n.t('API Key')}
				</h2>
				<span class="px-2.5 py-0.5 rounded-full text-xs font-medium {statusColor(apiKey.status)}">{apiKey.status}</span>
			</div>

			{#if showFullKey}
				<div class="rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-3 flex items-start gap-2.5">
					<svg class="size-4 text-amber-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>
					<div class="text-xs text-amber-800 dark:text-amber-200">
						<strong>{$i18n.t('Important')}:</strong> {$i18n.t('Copy your API key now. For security, you will not be able to see the full key again.')}
					</div>
				</div>
			{/if}

			<div class="flex gap-2">
				<div class="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800 font-mono text-xs">
					<span class="truncate select-all">{showFullKey && apiKey.key ? apiKey.key : apiKey.key_masked}</span>
				</div>
				{#if apiKey.key}
					<button
						class="px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
						title={showFullKey ? $i18n.t('Hide') : $i18n.t('Show')}
						on:click={() => (showFullKey = !showFullKey)}
					>
						{#if showFullKey}
							<EyeSlash className="size-4" />
						{:else}
							<Eye className="size-4" />
						{/if}
					</button>
					<button
						class="px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
						title={$i18n.t('Copy')}
						on:click={() => {
							copyToClipboard(apiKey!.key);
							copied = true;
							setTimeout(() => (copied = false), 1200);
						}}
					>
						{#if copied}
							<CheckCircle className="size-4 text-emerald-500" />
						{:else}
							<Clipboard className="size-4" />
						{/if}
					</button>
				{/if}
				<button
					class="px-4 py-2.5 rounded-xl bg-black dark:bg-white text-white dark:text-black text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-1.5"
					on:click={regenerate}
				>
					<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" /></svg>
					{$i18n.t('Regenerate')}
				</button>
			</div>

			<div class="flex items-center gap-2 text-xs text-gray-400">
				<span>{$i18n.t('Created')}: {apiKey.created_at ? new Date(apiKey.created_at * 1000).toLocaleDateString() : '-'}</span>
				<span>·</span>
				<span>{$i18n.t('Masked')}: {apiKey.key_masked}</span>
			</div>
		</div>

		<!-- Stats Cards -->
		<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="flex items-center gap-2 mb-2">
					<div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
						<Star className="size-4 text-blue-600 dark:text-blue-400" />
					</div>
				</div>
				<div class="text-xs text-gray-500">{$i18n.t('Plan')}</div>
				<div class="text-lg font-bold mt-0.5 capitalize">{apiKey.plan_name ?? 'starter'}</div>
			</div>
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="flex items-center gap-2 mb-2">
					<div class="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
						<Bolt className="size-4 text-emerald-600 dark:text-emerald-400" />
					</div>
				</div>
				<div class="text-xs text-gray-500">{$i18n.t('Credits')}</div>
				<div class="text-lg font-bold mt-0.5">{apiKey.credits_remaining.toLocaleString()}</div>
			</div>
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="flex items-center gap-2 mb-2">
					<div class="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
						<ChartBar className="size-4 text-violet-600 dark:text-violet-400" />
					</div>
				</div>
				<div class="text-xs text-gray-500">{$i18n.t('This Month')}</div>
				<div class="text-lg font-bold mt-0.5">{apiKey.monthly_requests.toLocaleString()}</div>
			</div>
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="flex items-center gap-2 mb-2">
					<div class="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
						<Sparkles className="size-4 text-amber-600 dark:text-amber-400" />
					</div>
				</div>
				<div class="text-xs text-gray-500">{$i18n.t('Total Requests')}</div>
				<div class="text-lg font-bold mt-0.5">{apiKey.total_requests.toLocaleString()}</div>
			</div>
		</div>

		<!-- Low Credit Warning -->
		{#if apiKey.credits_remaining < 100}
			<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 flex items-center gap-2.5">
				<svg class="size-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>
				<div class="text-xs text-red-800 dark:text-red-200 flex-1">
					<strong>{$i18n.t('Low Balance')}:</strong> {$i18n.t('You have {{count}} credits remaining. Top up to avoid service interruption.', { count: apiKey.credits_remaining })}
				</div>
				<button class="px-3 py-1 rounded-lg bg-red-100 dark:bg-red-800/50 text-red-700 dark:text-red-300 text-xs font-medium hover:bg-red-200 dark:hover:bg-red-700/50 transition-colors" on:click={() => (activeTab = 'topup')}>
					{$i18n.t('Top Up Now')}
				</button>
			</div>
		{/if}

		<!-- API Endpoint Quick-start -->
		<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
			<h3 class="font-semibold text-sm flex items-center gap-2">
				<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" /></svg>
				{$i18n.t('Quick Start')}
			</h3>
			<div class="rounded-xl bg-gray-900 dark:bg-black p-4 text-xs text-gray-100 font-mono overflow-x-auto">
				<div class="text-gray-500"># {$i18n.t('OpenAI-compatible endpoint')}</div>
				<div class="mt-1">curl {window.location.origin}/api/v1/chat/completions \</div>
				<div class="pl-4">-H "Authorization: Bearer YOUR_API_KEY" \</div>
				<div class="pl-4">-H "Content-Type: application/json" \</div>
				<div class="pl-4">-d '{"{"}\"model\": \"gpt-4\", \"messages\": [{"{"}\"role\": \"user\", \"content\": \"Hello!\"{"}"}]{"}"}'</div>
			</div>
			<div class="flex items-center gap-3 text-xs text-gray-500">
				<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> {$i18n.t('Base URL')}: <code class="text-gray-700 dark:text-gray-300">{window.location.origin}/api/v1</code></span>
			</div>
		</div>

		<!-- Tab Navigation -->
		<div class="flex items-center gap-1 p-1 rounded-xl bg-gray-50 dark:bg-gray-900/40 w-fit">
			<button
				class="px-4 py-1.5 rounded-lg text-xs font-medium transition-colors {activeTab === 'overview' ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
				on:click={() => (activeTab = 'overview')}
			>
				<span class="flex items-center gap-1.5">
					<ChartBar className="size-3.5" />
					{$i18n.t('Overview')}
				</span>
			</button>
			<button
				class="px-4 py-1.5 rounded-lg text-xs font-medium transition-colors {activeTab === 'topup' ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
				on:click={() => (activeTab = 'topup')}
			>
				<span class="flex items-center gap-1.5">
					<Plus className="size-3.5" />
					{$i18n.t('Top Up')}
				</span>
			</button>
			<button
				class="px-4 py-1.5 rounded-lg text-xs font-medium transition-colors {activeTab === 'invoices' ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
				on:click={() => (activeTab = 'invoices')}
			>
				<span class="flex items-center gap-1.5">
					<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
					{$i18n.t('Invoices')}
				</span>
			</button>
		</div>

		<!-- Overview Tab -->
		{#if activeTab === 'overview'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
				<h3 class="font-semibold flex items-center gap-2">
					<Sparkles className="size-4 text-violet-500" />
					{$i18n.t('Workflow')}
				</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
					<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
						<div class="text-[11px] text-gray-500">1. {$i18n.t('Choose Plan')}</div>
						<div class="font-medium mt-1">{$i18n.t('Pricing & tiers')}</div>
					</div>
					<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
						<div class="text-[11px] text-gray-500">2. {$i18n.t('Add Credits')}</div>
						<div class="font-medium mt-1">{$i18n.t('Submit top-up')}</div>
					</div>
					<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
						<div class="text-[11px] text-gray-500">3. {$i18n.t('Processing')}</div>
						<div class="font-medium mt-1">
							{billingSettings.auto_approve_topups ? $i18n.t('Auto-approved instantly') : $i18n.t('Pending admin review')}
						</div>
					</div>
					<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
						<div class="text-[11px] text-gray-500">4. {$i18n.t('Track')}</div>
						<div class="font-medium mt-1">{$i18n.t('Usage + invoices')}</div>
					</div>
				</div>
				<div class="flex flex-wrap gap-2 pt-1">
					<button class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs hover:bg-gray-50 dark:hover:bg-gray-800" on:click={() => goto('/developer/api-keys/pricing')}>{$i18n.t('Open Pricing')}</button>
					<button class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs hover:bg-gray-50 dark:hover:bg-gray-800" on:click={() => goto('/developer/api-keys/guide')}>{$i18n.t('Open Guide')}</button>
					<button class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs hover:bg-gray-50 dark:hover:bg-gray-800" on:click={() => (activeTab = 'topup')}>{$i18n.t('Go to Top Up')}</button>
					<button class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs hover:bg-gray-50 dark:hover:bg-gray-800" on:click={() => (activeTab = 'invoices')}>{$i18n.t('Go to Invoices')}</button>
				</div>
			</div>

			<!-- Usage Summary -->
			{#if usage}
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
					<h3 class="font-semibold flex items-center gap-2">
						<ChartBar className="size-4 text-blue-500" />
						{$i18n.t('Usage & Billing')}
					</h3>
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
						<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
							<div class="text-xs text-gray-500">{$i18n.t('Monthly Requests')}</div>
							<div class="text-base font-bold mt-0.5">{usage.monthly_requests.toLocaleString()}</div>
						</div>
						<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
							<div class="text-xs text-gray-500">{$i18n.t('Pending Topups')}</div>
							<div class="text-base font-bold mt-0.5">{usage.pending_topups}</div>
						</div>
						<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
							<div class="text-xs text-gray-500">{$i18n.t('Paid Invoices')}</div>
							<div class="text-base font-bold mt-0.5">{usage.paid_invoices}</div>
						</div>
						<div class="rounded-xl bg-gray-50 dark:bg-gray-900/40 p-3">
							<div class="text-xs text-gray-500">{$i18n.t('Total Spend')}</div>
							<div class="text-base font-bold mt-0.5">${usage.total_spend_usd.toFixed(2)}</div>
						</div>
					</div>
					<p class="text-xs text-gray-400">{$i18n.t('Avg spend / 1K requests')}: ${usage.avg_spend_per_1k_requests_usd.toFixed(4)} · {$i18n.t('Period')}: {usage.usage_month ?? '-'}</p>
				</div>
			{/if}

			<!-- Usage Charts -->
			{#if myUsageDaily.length > 0 || myUsageByModel.length > 0}
				<div class="flex items-center justify-between">
					<h3 class="text-sm font-semibold">{$i18n.t('Usage Window')}</h3>
					<div class="flex items-center gap-1 p-1 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800">
						{#each usageDayOptions as option}
							<button
								class="px-2.5 py-1 rounded-lg text-xs font-medium transition-colors {usageDays === option
									? 'bg-white dark:bg-gray-800 shadow-sm'
									: 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
								on:click={() => refreshUsageRange(option)}
							>
								{option}d
							</button>
						{/each}
					</div>
				</div>

				<div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
					{#if myUsageDaily.length > 0}
						<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5">
							<h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
								<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" /></svg>
								{$i18n.t('Daily Usage')}
							</h3>
							<BarChart
								data={myUsageDaily.map((d) => ({ label: d.date, value: d.requests, secondary: d.total_cost }))}
								valueLabel="Requests"
								secondaryLabel="Cost ($)"
								barColor="#3b82f6"
								secondaryColor="#f59e0b"
								height={200}
							/>
						</div>
					{/if}
					{#if myUsageByModel.length > 0}
						<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5">
							<h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
								<Sparkles className="size-4 text-violet-500" />
								{$i18n.t('By Model')}
							</h3>
							<BarChart
								data={myUsageByModel.map((m) => ({ label: m.model.length > 18 ? m.model.slice(0, 16) + '..' : m.model, value: m.requests, secondary: m.total_tokens }))}
								valueLabel="Requests"
								secondaryLabel="Tokens"
								barColor="#8b5cf6"
								secondaryColor="#10b981"
								height={200}
							/>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Plans -->
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
				<h3 class="font-semibold flex items-center gap-2">
					<Star className="size-4 text-violet-500" />
					{$i18n.t('Available Plans')}
				</h3>
				<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
					{#each plans as plan, i}
						{@const isActive = selectedPlanId === plan.id}
						<button
							class="rounded-xl border text-left p-4 transition-all duration-200 space-y-2
								{isActive ? 'border-blue-500 dark:border-blue-400 bg-blue-50/50 dark:bg-blue-900/10' : 'border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700'}"
							on:click={() => selectPlan(plan)}
						>
							<div class="flex items-center gap-2.5">
								<div class="w-8 h-8 rounded-lg bg-gradient-to-br {planColors[i]} flex items-center justify-center text-white flex-shrink-0">
									{#if i === 0}<Bolt className="size-4" />
									{:else if i === 1}<Sparkles className="size-4" />
									{:else}<Star className="size-4" />
									{/if}
								</div>
								<div>
									<div class="font-semibold text-sm">{plan.name}</div>
									<div class="text-xs text-gray-500">${plan.monthly_price_usd}/{$i18n.t('month')}</div>
								</div>
							</div>
							<div class="flex flex-wrap gap-1.5 text-xs text-gray-500">
								<span class="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800">{plan.included_credits.toLocaleString()} credits</span>
								<span class="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800">{plan.rpm_limit} RPM</span>
							</div>
						</button>
					{/each}
				</div>
			</div>

		<!-- Top Up Tab -->
		{:else if activeTab === 'topup'}
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
				<!-- Top-up Form -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-4">
					<h3 class="font-semibold flex items-center gap-2">
						<Plus className="size-4 text-emerald-500" />
						{$i18n.t('Add Credits')}
					</h3>
					<div class="text-xs">
						<span class="px-2 py-1 rounded-full font-medium {billingSettings.auto_approve_topups
							? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
							: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'}">
							{billingSettings.auto_approve_topups ? $i18n.t('Instant auto-approval enabled') : $i18n.t('Manual admin approval enabled')}
						</span>
					</div>

					<div class="space-y-3">
						<div>
							<div class="text-xs font-medium text-gray-500 mb-1">{$i18n.t('Quick amount')}</div>
							<div class="flex flex-wrap gap-2">
								{#each [10, 25, 50, 100, 250] as amountOption}
									<button
										type="button"
										class="px-2.5 py-1 rounded-lg text-xs border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
										on:click={() => (topupAmount = amountOption)}
									>
										${amountOption}
									</button>
								{/each}
							</div>
						</div>

						<div>
						<label for="topup-payment-account" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Payment Account')}</label>
						<div class="relative">
							<select id="topup-payment-account" class="w-full appearance-none px-3 py-3 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-200 dark:border-gray-700 text-sm font-medium pr-10 focus:outline-hidden focus:ring-2 focus:ring-blue-500/40" bind:value={selectedPaymentAccountId}>
								{#if paymentAccounts.length === 0}
									<option value="">{$i18n.t('No payment accounts available')}</option>
								{:else}
									{#each paymentAccounts as pa}
										<option value={pa.id}>{pa.provider.toUpperCase()} · {pa.account_name} · {pa.account_number}</option>
									{/each}
								{/if}
							</select>
							<div class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-gray-400">
								<svg class="size-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
							</div>
						</div>
						{#if selectedPaymentAccount}
							<div class="mt-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-900/30 p-3 text-xs space-y-1">
								<div class="font-medium text-gray-700 dark:text-gray-200 flex items-center gap-2">
									<PaymentProviderIcon provider={selectedPaymentAccount.provider} size="size-5" />
									{selectedPaymentAccount.provider.toUpperCase()} · {selectedPaymentAccount.account_name}
								</div>
								<div class="text-gray-500 font-mono">{selectedPaymentAccount.account_number}</div>
								{#if selectedPaymentAccount.instructions}
									<div class="text-gray-500">{selectedPaymentAccount.instructions}</div>
								{/if}
							</div>
						{/if}
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<label for="topup-amount" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Amount')}</label>
								<input id="topup-amount" type="number" min="1" step="1" class="w-full px-3 py-2.5 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={topupAmount} />
							</div>
							<div>
								<label for="topup-currency" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Currency')}</label>
								<select id="topup-currency" class="w-full appearance-none px-3 py-2.5 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={topupCurrency}>
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

						<div>
							<label for="topup-tx-ref" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Transaction Reference')}</label>
							<input id="topup-tx-ref" class="w-full px-3 py-2.5 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={topupTxRef} placeholder={$i18n.t('e.g. bank transfer ref or receipt ID')} />
						</div>

						<div>
							<label for="topup-note" class="text-xs font-medium text-gray-500 mb-1 block">{$i18n.t('Note')}</label>
							<textarea id="topup-note" rows="2" class="w-full px-3 py-2.5 rounded-xl bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={topupNote} placeholder={$i18n.t('Optional note about this payment')}></textarea>
						</div>

						<button class="w-full px-4 py-2.5 rounded-xl bg-black dark:bg-white text-white dark:text-black text-sm font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2" on:click={submitTopup}>
							<Plus className="size-4" />
							{$i18n.t('Submit Top-up Request')}
						</button>
					</div>
				</div>

				<!-- Top-up History -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
					<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<svg class="size-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
							{$i18n.t('Request History')}
						</div>
						<select class="text-xs rounded-lg px-2 py-1 bg-gray-50 dark:bg-gray-900/40 border border-gray-200 dark:border-gray-700" bind:value={topupStatusFilter}>
							<option value="all">{$i18n.t('All')}</option>
							<option value="pending">{$i18n.t('Pending')}</option>
							<option value="approved">{$i18n.t('Approved')}</option>
							<option value="rejected">{$i18n.t('Rejected')}</option>
						</select>
					</div>
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Amount')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Ref')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Status')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if filteredTopups.length === 0}
								<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="3">{$i18n.t('No top-up requests yet')}</td></tr>
							{:else}
								{#each filteredTopups as topup}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-2.5 font-medium">{topup.amount} {topup.currency}</td>
										<td class="px-4 py-2.5 text-gray-500 font-mono">{topup.tx_ref ?? '-'}</td>
										<td class="px-4 py-2.5">
											<span class="px-2 py-0.5 rounded-full text-xs font-medium {statusColor(topup.status)}">{topup.status}</span>
										</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

		<!-- Invoices Tab -->
		{:else if activeTab === 'invoices'}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 font-semibold text-sm flex items-center justify-between gap-2">
					<div class="flex items-center gap-2">
						<svg class="size-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
						{$i18n.t('Invoices')}
					</div>
					<select class="text-xs rounded-lg px-2 py-1 bg-gray-50 dark:bg-gray-900/40 border border-gray-200 dark:border-gray-700" bind:value={invoiceStatusFilter}>
						<option value="all">{$i18n.t('All')}</option>
						<option value="paid">{$i18n.t('Paid')}</option>
						<option value="pending">{$i18n.t('Pending')}</option>
						<option value="rejected">{$i18n.t('Rejected')}</option>
					</select>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-xs">
						<thead class="bg-gray-50 dark:bg-gray-900/40">
							<tr>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Date')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Amount')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Credits')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Status')}</th>
								<th class="px-4 py-2.5 text-left font-medium text-gray-500">{$i18n.t('Export')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#if filteredInvoices.length === 0}
								<tr><td class="px-4 py-6 text-gray-400 text-center" colspan="5">{$i18n.t('No invoices yet')}</td></tr>
							{:else}
								{#each filteredInvoices as invoice}
									<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
										<td class="px-4 py-2.5 text-gray-500">{new Date(invoice.created_at * 1000).toLocaleDateString()}</td>
										<td class="px-4 py-2.5 font-medium">{invoice.amount} {invoice.currency}</td>
										<td class="px-4 py-2.5">{invoice.credits}</td>
										<td class="px-4 py-2.5">
											<span class="px-2 py-0.5 rounded-full text-xs font-medium {statusColor(invoice.status)}">{invoice.status}</span>
										</td>
										<td class="px-4 py-2.5">
											<button
												class="px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center gap-1"
												on:click={() => exportInvoicePdf(invoice.id)}
											>
												<svg class="size-3" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
												PDF
											</button>
										</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	{/if}
</div>
