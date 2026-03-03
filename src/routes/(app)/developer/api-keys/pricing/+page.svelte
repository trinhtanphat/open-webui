<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getApiKeyPlans, type ApiKeyPlan } from '$lib/apis/api-keys';

	const i18n = getContext<any>('i18n');

	let loading = true;
	let plans: ApiKeyPlan[] = [];

	onMount(async () => {
		plans = await getApiKeyPlans(localStorage.token).catch(() => []);
		loading = false;
	});
</script>

<div class="max-w-5xl mx-auto px-4 py-6 space-y-5">
	<div>
		<div class="text-2xl font-semibold">{$i18n.t('API Pricing')}</div>
		<div class="text-sm text-gray-500">{$i18n.t('Transparent plans for paid API users. Choose a package, submit payment, and track usage in real time.')}</div>
	</div>

	{#if loading}
		<div class="text-sm text-gray-500">{$i18n.t('Loading...')}</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
			{#each plans as plan}
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
					<div>
						<div class="text-lg font-semibold">{plan.name}</div>
						<div class="text-xs text-gray-500">{plan.recommended_for}</div>
					</div>
					<div class="text-2xl font-bold">${plan.monthly_price_usd}<span class="text-sm font-normal text-gray-500">/month</span></div>
					<div class="space-y-1 text-sm text-gray-700 dark:text-gray-300">
						<div>• {plan.included_credits} included credits</div>
						<div>• {plan.rpm_limit} requests/minute</div>
						<div>• {plan.support_tier} support</div>
						<div>• ${plan.overage_usd_per_1k_requests}/1k overage requests</div>
					</div>
					<button class="w-full px-3 py-2 rounded-lg bg-black text-white dark:bg-white dark:text-black text-sm" on:click={() => goto('/developer/api-keys')}>
						Choose {plan.name}
					</button>
				</div>
			{/each}
		</div>

		<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-2 text-sm">
			<div class="font-medium">Workflow</div>
			<div class="text-gray-600 dark:text-gray-300">1) Pick a plan in this page.</div>
			<div class="text-gray-600 dark:text-gray-300">2) Go to Developer Console, submit payment proof for selected package.</div>
			<div class="text-gray-600 dark:text-gray-300">3) Admin approves/rejects request, system issues invoice and updates credits.</div>
			<div class="text-gray-600 dark:text-gray-300">4) Monitor usage, spend and invoices from your dashboard.</div>
		</div>
	{/if}
</div>
