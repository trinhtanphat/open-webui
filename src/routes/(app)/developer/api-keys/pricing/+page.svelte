<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getApiKeyPlans,
		getPublicModelPricing,
		type ApiKeyPlan,
		type ModelPricing
	} from '$lib/apis/api-keys';

	import CheckCircle from '$lib/components/icons/CheckCircle.svelte';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';
	import ArrowLeft from '$lib/components/icons/ArrowLeft.svelte';
	import Bolt from '$lib/components/icons/Bolt.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import Star from '$lib/components/icons/Star.svelte';

	const i18n = getContext<any>('i18n');

	let loading = true;
	let plans: ApiKeyPlan[] = [];
	let models: ModelPricing[] = [];

	onMount(async () => {
		plans = await getApiKeyPlans(localStorage.token).catch(() => []);
		models = await getPublicModelPricing(localStorage.token).catch(() => []);
		loading = false;
	});

	const planColors = [
		'from-gray-500 to-gray-600',
		'from-blue-500 to-violet-600',
		'from-violet-500 to-fuchsia-600'
	];
</script>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
	<!-- Header -->
	<div class="flex items-center gap-3">
		<button
			class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
			on:click={() => goto('/developer/api-keys/landing')}
		>
			<ArrowLeft className="size-4" />
		</button>
		<div>
			<h1 class="text-2xl sm:text-3xl font-bold">{$i18n.t('Pricing')}</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Transparent plans for every stage of your project')}</p>
		</div>
	</div>

	{#if loading}
		<div class="text-center py-20 text-gray-500">
			<div class="animate-spin w-6 h-6 border-2 border-gray-300 border-t-gray-800 rounded-full mx-auto mb-3"></div>
			{$i18n.t('Loading plans...')}
		</div>
	{:else}
		<!-- Plan Cards -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-5">
			{#each plans as plan, i}
				{@const isPopular = i === 1}
				<div class="relative rounded-2xl border overflow-hidden transition-all duration-200
					{isPopular ? 'border-blue-500 dark:border-blue-400 shadow-lg shadow-blue-500/10' : 'border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700'}">

					{#if isPopular}
						<div class="bg-gradient-to-r {planColors[i]} px-4 py-1.5 text-center text-xs font-semibold text-white uppercase tracking-wider">
							{$i18n.t('Most Popular')}
						</div>
					{/if}

					<div class="p-6 space-y-5">
						<!-- Plan header -->
						<div class="flex items-start gap-3">
							<div class="w-11 h-11 rounded-xl bg-gradient-to-br {planColors[i]} flex items-center justify-center text-white flex-shrink-0">
								{#if i === 0}<Bolt className="size-5" />
								{:else if i === 1}<Sparkles className="size-5" />
								{:else}<Star className="size-5" />
								{/if}
							</div>
							<div>
								<h3 class="text-lg font-bold">{plan.name}</h3>
								<p class="text-xs text-gray-500 dark:text-gray-400">{plan.recommended_for}</p>
							</div>
						</div>

						<!-- Price -->
						<div class="flex items-baseline gap-1">
							<span class="text-4xl font-bold">${plan.monthly_price_usd}</span>
							<span class="text-gray-500">/{$i18n.t('month')}</span>
						</div>

						<!-- Features -->
						<ul class="space-y-3">
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span><strong>{plan.included_credits.toLocaleString()}</strong> {$i18n.t('credits included')}</span>
							</li>
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span><strong>{plan.rpm_limit}</strong> {$i18n.t('requests per minute')}</span>
							</li>
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span><strong>{plan.support_tier}</strong> {$i18n.t('support')}</span>
							</li>
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span>${plan.overage_usd_per_1k_requests} {$i18n.t('per 1K overage requests')}</span>
							</li>
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span>{$i18n.t('OpenAI-compatible API')}</span>
							</li>
							<li class="flex items-start gap-2.5 text-sm">
								<CheckCircle className="size-4 text-emerald-500 mt-0.5 flex-shrink-0" />
								<span>{$i18n.t('Real-time usage dashboard')}</span>
							</li>
						</ul>

						<!-- CTA -->
						<button
							class="w-full py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all
								{isPopular ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white hover:opacity-90' : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'}"
							on:click={() => goto('/developer/api-keys')}
						>
							{$i18n.t('Get Started')}
							<ArrowRight className="size-3.5" />
						</button>
					</div>
				</div>
			{/each}
		</div>

		<!-- Model Pricing Table with Tiers -->
		{#if models.length > 0}
			{@const budgetModels = models.filter(m => m.per_request_cost === 0 && m.input_cost_per_1k_tokens < 0.01)}
			{@const standardModels = models.filter(m => m.per_request_cost > 0 || (m.input_cost_per_1k_tokens >= 0.01 && m.input_cost_per_1k_tokens < 0.05))}
			{@const premiumModels = models.filter(m => m.input_cost_per_1k_tokens >= 0.05)}
			{@const allCategorized = budgetModels.length + standardModels.length + premiumModels.length}

			<div class="space-y-6">
				<div class="text-center space-y-2">
					<h2 class="text-xl font-bold">{$i18n.t('Per-model token pricing')}</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Credits are consumed based on actual token usage. Expensive models cost more credits per token.')}
					</p>
				</div>

				<!-- Model Tier Summary -->
				<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
					<div class="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10 p-4 text-center">
						<div class="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-2">
							<CheckCircle className="size-4 text-emerald-600" />
						</div>
						<div class="font-semibold text-sm text-emerald-700 dark:text-emerald-400">{$i18n.t('Budget')}</div>
						<div class="text-xs text-gray-500 mt-0.5">{$i18n.t('Low cost, great for testing')}</div>
						<div class="text-lg font-bold mt-1">{budgetModels.length} {$i18n.t('models')}</div>
					</div>
					<div class="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10 p-4 text-center">
						<div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mx-auto mb-2">
							<Sparkles className="size-4 text-blue-600" />
						</div>
						<div class="font-semibold text-sm text-blue-700 dark:text-blue-400">{$i18n.t('Standard')}</div>
						<div class="text-xs text-gray-500 mt-0.5">{$i18n.t('Balanced price/performance')}</div>
						<div class="text-lg font-bold mt-1">{standardModels.length} {$i18n.t('models')}</div>
					</div>
					<div class="rounded-xl border border-violet-200 dark:border-violet-800 bg-violet-50/50 dark:bg-violet-900/10 p-4 text-center">
						<div class="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center mx-auto mb-2">
							<Star className="size-4 text-violet-600" />
						</div>
						<div class="font-semibold text-sm text-violet-700 dark:text-violet-400">{$i18n.t('Premium')}</div>
						<div class="text-xs text-gray-500 mt-0.5">{$i18n.t('Most capable, higher cost')}</div>
						<div class="text-lg font-bold mt-1">{premiumModels.length} {$i18n.t('models')}</div>
					</div>
				</div>

				<!-- Full Model Table -->
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-gray-50 dark:bg-gray-900/40">
								<th class="px-5 py-3 text-left font-medium text-gray-500">{$i18n.t('Model')}</th>
								<th class="px-5 py-3 text-left font-medium text-gray-500">{$i18n.t('Tier')}</th>
								<th class="px-5 py-3 text-right font-medium text-gray-500">{$i18n.t('Input / 1K tok')}</th>
								<th class="px-5 py-3 text-right font-medium text-gray-500">{$i18n.t('Output / 1K tok')}</th>
								<th class="px-5 py-3 text-right font-medium text-gray-500">{$i18n.t('Per Request')}</th>
								<th class="px-5 py-3 text-right font-medium text-gray-500">{$i18n.t('≈ Credits/1K tok')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							{#each models as m}
								{@const tier = m.input_cost_per_1k_tokens >= 0.05 ? 'premium' : (m.per_request_cost > 0 || m.input_cost_per_1k_tokens >= 0.01) ? 'standard' : 'budget'}
								{@const tierColor = tier === 'premium' ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400' : tier === 'standard' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'}
								{@const dotColor = tier === 'premium' ? 'bg-violet-500' : tier === 'standard' ? 'bg-blue-500' : 'bg-emerald-500'}
								<tr class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
									<td class="px-5 py-3">
										<div class="flex items-center gap-2">
											<span class="w-2 h-2 rounded-full {dotColor} flex-shrink-0"></span>
											<div>
												<div class="font-medium">{m.display_name || m.model_id}</div>
												{#if m.display_name && m.display_name !== m.model_id}
													<div class="text-xs text-gray-400 font-mono">{m.model_id}</div>
												{/if}
											</div>
										</div>
									</td>
									<td class="px-5 py-3">
										<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase {tierColor}">{tier}</span>
									</td>
									<td class="px-5 py-3 text-right font-mono text-gray-600 dark:text-gray-300">${m.input_cost_per_1k_tokens.toFixed(4)}</td>
									<td class="px-5 py-3 text-right font-mono text-gray-600 dark:text-gray-300">${m.output_cost_per_1k_tokens.toFixed(4)}</td>
									<td class="px-5 py-3 text-right font-mono text-gray-600 dark:text-gray-300">${m.per_request_cost.toFixed(4)}</td>
									<td class="px-5 py-3 text-right font-mono text-gray-600 dark:text-gray-300">
										~{Math.max(1, Math.round(((m.input_cost_per_1k_tokens + m.output_cost_per_1k_tokens) / 2 + m.per_request_cost) / 0.001))}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				{#if allCategorized === 0}
					<div class="text-center text-sm text-gray-400 py-6">
						{$i18n.t('No model pricing configured yet. Admin will set up per-model costs.')}
					</div>
				{/if}
			</div>
		{:else}
			<div class="rounded-2xl border border-dashed border-gray-200 dark:border-gray-700 p-8 text-center space-y-2">
				<Bolt className="size-8 text-gray-300 mx-auto" />
				<h3 class="font-medium">{$i18n.t('Model pricing coming soon')}</h3>
				<p class="text-sm text-gray-500">{$i18n.t('Admin will configure per-model token costs. Meanwhile, flat 1 credit per request applies.')}</p>
			</div>
		{/if}

		<!-- How Billing Works -->
		<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-6 space-y-4">
			<h2 class="text-lg font-bold flex items-center gap-2">
				<svg class="size-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
				{$i18n.t('How billing works')}
			</h2>
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
				<div class="flex items-start gap-3">
					<div class="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xs flex-shrink-0">1</div>
					<div><span class="font-medium">{$i18n.t('Choose plan')}</span><p class="text-gray-500 text-xs mt-0.5">{$i18n.t('Pick a tier that matches your usage')}</p></div>
				</div>
				<div class="flex items-start gap-3">
					<div class="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xs flex-shrink-0">2</div>
					<div><span class="font-medium">{$i18n.t('Submit payment')}</span><p class="text-gray-500 text-xs mt-0.5">{$i18n.t('Bank, Stripe, VNPay, or MoMo')}</p></div>
				</div>
				<div class="flex items-start gap-3">
					<div class="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xs flex-shrink-0">3</div>
					<div><span class="font-medium">{$i18n.t('Credits activated')}</span><p class="text-gray-500 text-xs mt-0.5">{$i18n.t('Admin approves or auto-webhook')}</p></div>
				</div>
				<div class="flex items-start gap-3">
					<div class="w-7 h-7 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-xs flex-shrink-0">4</div>
					<div><span class="font-medium">{$i18n.t('Start calling API')}</span><p class="text-gray-500 text-xs mt-0.5">{$i18n.t('Track usage in real-time')}</p></div>
				</div>
			</div>
		</div>

		<!-- FAQ -->
		<div class="space-y-4">
			<h2 class="text-xl font-bold text-center">{$i18n.t('Frequently asked questions')}</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4">
					<h3 class="font-medium text-sm">{$i18n.t('Can I still chat normally if my API credits run out?')}</h3>
					<p class="text-xs text-gray-500 mt-1.5">{$i18n.t('Yes! The web chat interface works independently. API credits only affect external API calls via')} <code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">Authorization: Bearer sk-...</code></p>
				</div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4">
					<h3 class="font-medium text-sm">{$i18n.t('How do credits translate to actual usage?')}</h3>
					<p class="text-xs text-gray-500 mt-1.5">{$i18n.t('1 credit ≈ $0.001. Actual cost depends on the model used — cheaper models use fewer credits per token.')}</p>
				</div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4">
					<h3 class="font-medium text-sm">{$i18n.t('Can I top up mid-cycle?')}</h3>
					<p class="text-xs text-gray-500 mt-1.5">{$i18n.t('Yes, submit a top-up request anytime. Credits are added immediately after approval.')}</p>
				</div>
				<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4">
					<h3 class="font-medium text-sm">{$i18n.t('What payment methods are accepted?')}</h3>
					<p class="text-xs text-gray-500 mt-1.5">{$i18n.t('Bank transfer, Stripe, VNPay, and MoMo. Admin configures available methods.')}</p>
				</div>
			</div>
		</div>

		<!-- CTA -->
		<div class="text-center py-8 space-y-3">
			<h2 class="text-xl font-bold">{$i18n.t('Ready to get started?')}</h2>
			<div class="flex items-center justify-center gap-3">
				<button
					class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-black dark:bg-white text-white dark:text-black font-medium text-sm hover:opacity-90 transition-opacity"
					on:click={() => goto('/developer/api-keys')}
				>
					{$i18n.t('Open Developer Console')}
					<ArrowRight className="size-4" />
				</button>
				<button
					class="px-6 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
					on:click={() => goto('/developer/api-keys/guide')}
				>
					{$i18n.t('Read the Guide')}
				</button>
			</div>
		</div>
	{/if}
</div>
