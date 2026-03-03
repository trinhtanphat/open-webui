<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getApiKeyPlans, getPublicModelPricing, type ApiKeyPlan, type ModelPricing } from '$lib/apis/api-keys';

	import Bolt from '$lib/components/icons/Bolt.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';
	import ChartBar from '$lib/components/icons/ChartBar.svelte';
	import CheckCircle from '$lib/components/icons/CheckCircle.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';
	import UserGroup from '$lib/components/icons/UserGroup.svelte';

	const i18n = getContext<any>('i18n');

	let plans: ApiKeyPlan[] = [];
	let models: ModelPricing[] = [];
	let loading = true;

	onMount(async () => {
		plans = await getApiKeyPlans(localStorage.token).catch(() => []);
		models = await getPublicModelPricing(localStorage.token).catch(() => []);
		loading = false;
	});

	const features = [
		{
			icon: 'bolt',
			title: 'Lightning Fast',
			desc: 'OpenAI-compatible API with sub-second latency. Drop-in replacement for any OpenAI SDK.'
		},
		{
			icon: 'lock',
			title: 'Secure by Default',
			desc: 'SHA-256 hashed API keys, rate limiting, and granular credit controls per user.'
		},
		{
			icon: 'globe',
			title: 'Multi-Model Access',
			desc: 'Access GPT-4o, Claude, Gemini, Llama and more through a single unified API endpoint.'
		},
		{
			icon: 'chart',
			title: 'Real-time Analytics',
			desc: 'Track token usage, costs, and performance per model with interactive dashboards.'
		},
		{
			icon: 'users',
			title: 'Team Ready',
			desc: 'Issue multiple API keys, manage credits centrally, and monitor usage across your organization.'
		},
		{
			icon: 'sparkles',
			title: 'Pay-as-you-go',
			desc: 'Token-level billing with transparent per-model pricing. Only pay for what you actually use.'
		}
	];

	const steps = [
		{ num: '01', title: 'Create Account', desc: 'Sign up and get started in seconds. No credit card required initially.' },
		{ num: '02', title: 'Choose a Plan', desc: 'Pick Starter, Pro, or Business based on your usage needs.' },
		{ num: '03', title: 'Add Credits', desc: 'Top up via bank transfer, Stripe, VNPay, or MoMo payment.' },
		{ num: '04', title: 'Start Building', desc: 'Use your API key with any OpenAI-compatible SDK or HTTP client.' }
	];
</script>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
	<!-- Hero -->
	<div class="text-center py-16 sm:py-24 space-y-6">
		<div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-medium">
			<Sparkles className="size-3.5" />
			OpenAI-Compatible API Platform
		</div>

		<h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
			Build with AI,<br />
			<span class="bg-gradient-to-r from-blue-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
				Scale with Confidence
			</span>
		</h1>

		<p class="text-lg sm:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
			Access the world's best AI models through a single API. Real-time usage tracking,
			transparent token-based billing, and enterprise-grade security.
		</p>

		<div class="flex flex-wrap items-center justify-center gap-3 pt-2">
			<button
				class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-black dark:bg-white text-white dark:text-black font-medium text-sm hover:opacity-90 transition-opacity"
				on:click={() => goto('/developer/api-keys')}
			>
				Get Started
				<ArrowRight className="size-4" />
			</button>
			<button
				class="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
				on:click={() => goto('/developer/api-keys/pricing')}
			>
				View Pricing
			</button>
		</div>

		<div class="flex items-center justify-center gap-6 pt-4 text-xs text-gray-400">
			<span class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> No setup fee</span>
			<span class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> Pay as you go</span>
			<span class="flex items-center gap-1.5"><CheckCircle className="size-3.5 text-emerald-500" /> Cancel anytime</span>
		</div>
	</div>

	<!-- Features Grid -->
	<div class="py-12 space-y-8">
		<div class="text-center space-y-2">
			<h2 class="text-2xl sm:text-3xl font-bold">Everything you need to build with AI</h2>
			<p class="text-gray-500 dark:text-gray-400">Production-ready API platform with built-in billing & analytics</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each features as f}
				<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3 hover:border-gray-200 dark:hover:border-gray-700 transition-colors">
					<div class="w-10 h-10 rounded-xl flex items-center justify-center
						{f.icon === 'bolt' ? 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400' :
						 f.icon === 'lock' ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' :
						 f.icon === 'globe' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' :
						 f.icon === 'chart' ? 'bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400' :
						 f.icon === 'users' ? 'bg-pink-50 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400' :
						 'bg-fuchsia-50 dark:bg-fuchsia-900/30 text-fuchsia-600 dark:text-fuchsia-400'}"
					>
						{#if f.icon === 'bolt'}<Bolt className="size-5" />
						{:else if f.icon === 'lock'}<LockClosed className="size-5" />
						{:else if f.icon === 'globe'}<GlobeAlt className="size-5" />
						{:else if f.icon === 'chart'}<ChartBar className="size-5" />
						{:else if f.icon === 'users'}<UserGroup className="size-5" />
						{:else}<Sparkles className="size-5" />
						{/if}
					</div>
					<h3 class="font-semibold">{f.title}</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">{f.desc}</p>
				</div>
			{/each}
		</div>
	</div>

	<!-- How it works -->
	<div class="py-12 space-y-8">
		<div class="text-center space-y-2">
			<h2 class="text-2xl sm:text-3xl font-bold">Get started in minutes</h2>
			<p class="text-gray-500 dark:text-gray-400">Four simple steps from sign-up to API call</p>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each steps as step, i}
				<div class="relative rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-2">
					<div class="text-3xl font-bold text-gray-100 dark:text-gray-800">{step.num}</div>
					<h3 class="font-semibold">{step.title}</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">{step.desc}</p>
					{#if i < steps.length - 1}
						<div class="hidden lg:block absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10">
							<ArrowRight className="size-4 text-gray-300 dark:text-gray-600" />
						</div>
					{/if}
				</div>
			{/each}
		</div>
	</div>

	<!-- Pricing Preview -->
	{#if plans.length > 0}
		<div class="py-12 space-y-8">
			<div class="text-center space-y-2">
				<h2 class="text-2xl sm:text-3xl font-bold">Simple, transparent pricing</h2>
				<p class="text-gray-500 dark:text-gray-400">Choose a plan that fits your needs. Upgrade or downgrade anytime.</p>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each plans as plan, i}
					<div class="rounded-2xl border p-6 space-y-4 {i === 1 ? 'border-blue-500 dark:border-blue-400 ring-1 ring-blue-500/20 relative' : 'border-gray-100 dark:border-gray-800'}">
						{#if i === 1}
							<div class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-blue-500 text-white text-[10px] font-semibold uppercase tracking-wide">Popular</div>
						{/if}
						<div>
							<h3 class="text-lg font-semibold">{plan.name}</h3>
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{plan.recommended_for}</p>
						</div>
						<div class="flex items-baseline gap-1">
							<span class="text-3xl font-bold">${plan.monthly_price_usd}</span>
							<span class="text-sm text-gray-500">/month</span>
						</div>
						<ul class="space-y-2 text-sm">
							<li class="flex items-center gap-2">
								<CheckCircle className="size-4 text-emerald-500 flex-shrink-0" />
								<span>{plan.included_credits.toLocaleString()} credits included</span>
							</li>
							<li class="flex items-center gap-2">
								<CheckCircle className="size-4 text-emerald-500 flex-shrink-0" />
								<span>{plan.rpm_limit} requests/minute</span>
							</li>
							<li class="flex items-center gap-2">
								<CheckCircle className="size-4 text-emerald-500 flex-shrink-0" />
								<span>{plan.support_tier} support</span>
							</li>
							<li class="flex items-center gap-2">
								<CheckCircle className="size-4 text-emerald-500 flex-shrink-0" />
								<span>${plan.overage_usd_per_1k_requests}/1k overage</span>
							</li>
						</ul>
						<button
							class="w-full py-2.5 rounded-xl text-sm font-medium transition-colors
								{i === 1 ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'}"
							on:click={() => goto('/developer/api-keys')}
						>
							Get Started
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Model Pricing Table -->
	{#if models.length > 0}
		<div class="py-12 space-y-6">
			<div class="text-center space-y-2">
				<h2 class="text-2xl sm:text-3xl font-bold">Per-model token pricing</h2>
				<p class="text-gray-500 dark:text-gray-400">You only pay for the tokens you consume. Pricing varies by model.</p>
			</div>

			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
				<table class="w-full text-sm">
					<thead class="bg-gray-50 dark:bg-gray-900/40">
						<tr>
							<th class="px-4 py-3 text-left font-medium text-gray-500">Model</th>
							<th class="px-4 py-3 text-right font-medium text-gray-500">Input / 1K tokens</th>
							<th class="px-4 py-3 text-right font-medium text-gray-500">Output / 1K tokens</th>
							<th class="px-4 py-3 text-right font-medium text-gray-500">Per request</th>
						</tr>
					</thead>
					<tbody>
						{#each models as m}
							<tr class="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
								<td class="px-4 py-3">
									<div class="font-medium">{m.display_name || m.model_id}</div>
									{#if m.display_name && m.display_name !== m.model_id}
										<div class="text-xs text-gray-400 font-mono">{m.model_id}</div>
									{/if}
								</td>
								<td class="px-4 py-3 text-right font-mono">${m.input_cost_per_1k_tokens.toFixed(4)}</td>
								<td class="px-4 py-3 text-right font-mono">${m.output_cost_per_1k_tokens.toFixed(4)}</td>
								<td class="px-4 py-3 text-right font-mono">${m.per_request_cost.toFixed(4)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}

	<!-- Code Example -->
	<div class="py-12 space-y-6">
		<div class="text-center space-y-2">
			<h2 class="text-2xl sm:text-3xl font-bold">Drop-in compatible</h2>
			<p class="text-gray-500 dark:text-gray-400">Works with any OpenAI SDK. Just change the base URL.</p>
		</div>

		<div class="max-w-2xl mx-auto rounded-2xl bg-gray-950 dark:bg-gray-900 p-5 space-y-1 overflow-x-auto">
			<div class="flex items-center gap-2 pb-3 border-b border-gray-800">
				<span class="w-3 h-3 rounded-full bg-red-500/80"></span>
				<span class="w-3 h-3 rounded-full bg-yellow-500/80"></span>
				<span class="w-3 h-3 rounded-full bg-green-500/80"></span>
				<span class="ml-2 text-xs text-gray-500">Python</span>
			</div>
			<pre class="text-sm text-gray-300 leading-relaxed"><code><span class="text-violet-400">from</span> openai <span class="text-violet-400">import</span> OpenAI

client = OpenAI(
    base_url=<span class="text-emerald-400">"{typeof window !== 'undefined' ? window.location.origin : 'https://your-domain.com'}/api"</span>,
    api_key=<span class="text-emerald-400">"sk-your-api-key"</span>,
)

response = client.chat.completions.create(
    model=<span class="text-emerald-400">"gpt-4o-mini"</span>,
    messages=[<span class="text-gray-500">&#123;</span><span class="text-emerald-400">"role"</span>: <span class="text-emerald-400">"user"</span>, <span class="text-emerald-400">"content"</span>: <span class="text-emerald-400">"Hello!"</span><span class="text-gray-500">&#125;</span>]
)

<span class="text-violet-400">print</span>(response.choices[<span class="text-amber-400">0</span>].message.content)</code></pre>
		</div>
	</div>

	<!-- CTA -->
	<div class="py-16 text-center space-y-4">
		<h2 class="text-2xl sm:text-3xl font-bold">Ready to start building?</h2>
		<p class="text-gray-500 dark:text-gray-400">Create your account and make your first API call in under 5 minutes.</p>
		<button
			class="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-black dark:bg-white text-white dark:text-black font-medium hover:opacity-90 transition-opacity"
			on:click={() => goto('/developer/api-keys')}
		>
			Get your API key
			<ArrowRight className="size-4" />
		</button>
	</div>
</div>
