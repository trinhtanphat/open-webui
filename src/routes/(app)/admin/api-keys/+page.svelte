<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { user } from '$lib/stores';
	import {
		approveAdminTopup,
		createAdminPaymentAccount,
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
		type ApiKeyConsole,
		type ApiKeyPlan,
		type BillingInvoice,
		type BillingSummary,
		type PaymentAccount,
		type RevenueDailyEntry,
		type TopupRequest
	} from '$lib/apis/api-keys';

	const i18n = getContext<any>('i18n');

	let loading = true;
	let keys: ApiKeyConsole[] = [];
	let summary: BillingSummary | null = null;
	let paymentAccounts: PaymentAccount[] = [];
	let topups: TopupRequest[] = [];
	let invoices: BillingInvoice[] = [];
	let revenueDaily: RevenueDailyEntry[] = [];
	let auditLogs: any[] = [];
	let plans: ApiKeyPlan[] = [];

	let creditDelta = 100;
	let approveCredits = 100;

	let provider = 'bank_transfer';
	let accountName = '';
	let accountNumber = '';
	let instructions = '';
	let qrCodeUrl = '';
	let webhookSecret = '';

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
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}

		await loadData();
		loading = false;
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
</script>

<div class="px-4 lg:px-6 py-3 space-y-4">
	<div>
		<div class="text-lg font-semibold">{$i18n.t('API Key Console')}</div>
		<div class="text-xs text-gray-500">{$i18n.t('Manage API keys, billing, topups and payment accounts.')}</div>
	</div>

	{#if loading}
		<div class="text-sm text-gray-500">{$i18n.t('Loading...')}</div>
	{:else}
		{#if summary}
			<div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Keys</div><div class="font-semibold mt-1">{summary.total_keys}</div></div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Active</div><div class="font-semibold mt-1">{summary.active_keys}</div></div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Credits</div><div class="font-semibold mt-1">{summary.total_credits_remaining}</div></div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Pending topups</div><div class="font-semibold mt-1">{summary.pending_topups}</div></div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Invoices</div><div class="font-semibold mt-1">{summary.paid_invoices}</div></div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3"><div class="text-xs text-gray-500">Revenue</div><div class="font-semibold mt-1">${summary.total_revenue.toFixed(2)}</div></div>
			</div>
		{/if}

		<div class="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
			<div class="px-3 py-2 text-sm font-medium border-b border-gray-100 dark:border-gray-800">API Keys</div>
			<div class="px-3 py-2 text-xs text-gray-500 border-b border-gray-100 dark:border-gray-800">Ops workflow: Payment received → Verify proof → Approve/Reject top-up → Invoice issued → Audit log retained.</div>
			<table class="w-full text-sm">
				<thead class="bg-gray-50 dark:bg-gray-900/40">
					<tr class="text-left">
						<th class="px-3 py-2">User</th>
						<th class="px-3 py-2">Key</th>
						<th class="px-3 py-2">Plan</th>
						<th class="px-3 py-2">Credits</th>
						<th class="px-3 py-2">Requests</th>
						<th class="px-3 py-2">Status</th>
						<th class="px-3 py-2">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each keys as key}
						<tr class="border-t border-gray-100 dark:border-gray-800">
							<td class="px-3 py-2 font-mono text-xs">{key.user_id}</td>
							<td class="px-3 py-2 font-mono text-xs">{key.key_masked}</td>
							<td class="px-3 py-2">{key.plan_name ?? '-'}</td>
							<td class="px-3 py-2">{key.credits_remaining}</td>
							<td class="px-3 py-2">{key.total_requests}</td>
							<td class="px-3 py-2">
								<span
									class="px-2 py-0.5 rounded-full text-xs {key.status === 'active'
										? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
										: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'}"
								>
									{key.status}
								</span>
							</td>
							<td class="px-3 py-2">
								<div class="flex items-center gap-2">
									<button
										class="px-2 py-1 rounded-md bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
										on:click={() => adjustCredits(key, creditDelta)}
									>
										+{creditDelta}
									</button>
									<button
										class="px-2 py-1 rounded-md bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
										on:click={() => adjustCredits(key, -creditDelta)}
									>
										-{creditDelta}
									</button>
									<button
										class="px-2 py-1 rounded-md bg-black text-white dark:bg-white dark:text-black"
										on:click={() => toggleStatus(key)}
									>
										{key.status === 'active' ? 'Suspend' : 'Activate'}
									</button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
			<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3 space-y-2">
				<div class="text-sm font-medium">Published Plans</div>
				<div class="max-h-52 overflow-y-auto border border-gray-100 dark:border-gray-800 rounded-lg">
					{#if plans.length === 0}
						<div class="px-3 py-2 text-xs text-gray-500">No plans configured</div>
					{:else}
						{#each plans as plan}
							<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 text-xs">
								<div class="font-medium">{plan.name} (${plan.monthly_price_usd}/mo)</div>
								<div class="text-gray-500">{plan.included_credits} credits • RPM {plan.rpm_limit} • {plan.support_tier}</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3 space-y-2">
				<div class="text-sm font-medium">Payment Accounts</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<input class="px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={provider} placeholder="provider" />
					<input class="px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={accountName} placeholder="account name" />
					<input class="px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={accountNumber} placeholder="account number" />
					<input class="px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={qrCodeUrl} placeholder="qr code url" />
					<input class="px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" bind:value={webhookSecret} placeholder="webhook secret" />
				</div>
				<textarea class="w-full px-2.5 py-2 rounded-lg bg-transparent border border-gray-200 dark:border-gray-700 text-sm" rows="2" bind:value={instructions} placeholder="payment instructions"></textarea>
				<button class="px-3 py-1.5 rounded-lg bg-black text-white dark:bg-white dark:text-black text-xs" on:click={createPaymentAccount}>Add account</button>

				<div class="max-h-52 overflow-y-auto border border-gray-100 dark:border-gray-800 rounded-lg">
					{#if paymentAccounts.length === 0}
						<div class="px-3 py-2 text-xs text-gray-500">No payment accounts</div>
					{:else}
						{#each paymentAccounts as account}
							<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 text-xs">
								<div class="font-medium">{account.provider} • {account.account_name}</div>
								<div class="text-gray-500">{account.account_number}</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-3 space-y-2">
				<div class="text-sm font-medium">Top-up Requests</div>
				<div class="flex items-center gap-2 text-xs">
					<span>Approve credits:</span>
					<input class="w-24 px-2 py-1 rounded bg-transparent border border-gray-200 dark:border-gray-700" bind:value={approveCredits} type="number" min="1" />
				</div>
				<div class="max-h-64 overflow-y-auto border border-gray-100 dark:border-gray-800 rounded-lg">
					{#if topups.length === 0}
						<div class="px-3 py-2 text-xs text-gray-500">No topups</div>
					{:else}
						{#each topups as topup}
							<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 text-xs">
								<div class="font-medium">{topup.user_id} • {topup.amount} {topup.currency}</div>
								<div class="text-gray-500">status: {topup.status} • ref: {topup.tx_ref ?? '-'}</div>
								{#if topup.status === 'pending'}
									<div class="mt-1 flex items-center gap-1">
										<button class="px-2 py-1 rounded bg-black text-white dark:bg-white dark:text-black" on:click={() => approveTopup(topup)}>Approve</button>
										<button class="px-2 py-1 rounded bg-gray-100 dark:bg-gray-800" on:click={() => rejectTopup(topup)}>Reject</button>
									</div>
								{/if}
							</div>
						{/each}
					{/if}
				</div>
			</div>
		</div>

		<div class="rounded-xl border border-gray-100 dark:border-gray-800 overflow-x-auto">
			<div class="px-3 py-2 text-sm font-medium border-b border-gray-100 dark:border-gray-800">Revenue Daily (30 days)</div>
			<table class="w-full text-xs">
				<thead class="bg-gray-50 dark:bg-gray-900/40">
					<tr><th class="px-3 py-2 text-left">Date</th><th class="px-3 py-2 text-left">Revenue</th><th class="px-3 py-2 text-left">Credits</th><th class="px-3 py-2 text-left">Invoices</th></tr>
				</thead>
				<tbody>
					{#if revenueDaily.length === 0}
						<tr><td class="px-3 py-2 text-gray-500" colspan="4">No revenue data</td></tr>
					{:else}
						{#each revenueDaily as daily}
							<tr class="border-t border-gray-100 dark:border-gray-800"><td class="px-3 py-2">{daily.date}</td><td class="px-3 py-2">${daily.revenue.toFixed(2)}</td><td class="px-3 py-2">{daily.credits}</td><td class="px-3 py-2">{daily.invoices}</td></tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>

		<div class="rounded-xl border border-gray-100 dark:border-gray-800 overflow-x-auto">
			<div class="px-3 py-2 text-sm font-medium border-b border-gray-100 dark:border-gray-800">Invoices</div>
			<table class="w-full text-xs">
				<thead class="bg-gray-50 dark:bg-gray-900/40">
					<tr><th class="px-3 py-2 text-left">User</th><th class="px-3 py-2 text-left">Amount</th><th class="px-3 py-2 text-left">Credits</th><th class="px-3 py-2 text-left">Status</th></tr>
				</thead>
				<tbody>
					{#if invoices.length === 0}
						<tr><td class="px-3 py-2 text-gray-500" colspan="4">No invoices</td></tr>
					{:else}
						{#each invoices as invoice}
							<tr class="border-t border-gray-100 dark:border-gray-800"><td class="px-3 py-2">{invoice.user_id}</td><td class="px-3 py-2">{invoice.amount} {invoice.currency}</td><td class="px-3 py-2">{invoice.credits}</td><td class="px-3 py-2">{invoice.status}</td></tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>

		<div class="rounded-xl border border-gray-100 dark:border-gray-800 overflow-x-auto">
			<div class="px-3 py-2 text-sm font-medium border-b border-gray-100 dark:border-gray-800">Audit Trail</div>
			<table class="w-full text-xs">
				<thead class="bg-gray-50 dark:bg-gray-900/40">
					<tr><th class="px-3 py-2 text-left">When</th><th class="px-3 py-2 text-left">Actor</th><th class="px-3 py-2 text-left">Action</th><th class="px-3 py-2 text-left">Target</th></tr>
				</thead>
				<tbody>
					{#if auditLogs.length === 0}
						<tr><td class="px-3 py-2 text-gray-500" colspan="4">No audit events</td></tr>
					{:else}
						{#each auditLogs as log}
							<tr class="border-t border-gray-100 dark:border-gray-800">
								<td class="px-3 py-2">{new Date((log.created_at ?? 0) * 1000).toLocaleString()}</td>
								<td class="px-3 py-2 font-mono">{log.actor_id}</td>
								<td class="px-3 py-2">{log.action}</td>
								<td class="px-3 py-2">{log.target_type}:{log.target_id}</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>
	{/if}
</div>
