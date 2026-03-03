<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import ArrowLeft from '$lib/components/icons/ArrowLeft.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Bolt from '$lib/components/icons/Bolt.svelte';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';

	const i18n = getContext<any>('i18n');
	const curlExample = `curl -X POST "https://YOUR_DOMAIN/api/openai/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer sk-xxxxxxxxxxxxxxxx" \\
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'`;
	const webhookExample = `POST /api/v1/api-keys/webhooks/payment/{provider}
Header: X-BILLING-WEBHOOK-SECRET: your_webhook_secret
Body: {"topup_request_id":"...","status":"paid","tx_ref":"...","amount":12.5,"currency":"USD","credits":1200}`;
	const pythonExample = `from openai import OpenAI

client = OpenAI(
    api_key="sk-xxxxxxxxxxxxxxxx",
    base_url="https://YOUR_DOMAIN/api"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)`;

	const steps = [
		{
			num: '1',
			title: 'Get your API key',
			desc: 'Open Settings → Account → API keys, create or regenerate your key.',
			icon: 'key',
			color: 'blue'
		},
		{
			num: '2',
			title: 'Call the OpenAI-compatible API',
			desc: 'Use your key with any OpenAI-compatible SDK or cURL.',
			icon: 'code',
			color: 'violet'
		},
		{
			num: '3',
			title: 'Top up credits',
			desc: 'Submit payment proof in Developer Console. Admin approves or webhook auto-credits.',
			icon: 'plus',
			color: 'emerald'
		},
		{
			num: '4',
			title: 'Rate limits & security',
			desc: 'Each plan has RPM limits. Credits gate API access. Rotate keys if compromised.',
			icon: 'shield',
			color: 'amber'
		},
		{
			num: '5',
			title: 'Admin: payment accounts',
			desc: 'Admin adds bank/Stripe/VNPay/MoMo accounts with transfer instructions and QR codes.',
			icon: 'card',
			color: 'pink'
		},
		{
			num: '6',
			title: 'Webhook integration',
			desc: 'Configure gateway webhooks for auto-approval of top-up requests.',
			icon: 'webhook',
			color: 'gray'
		}
	];
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
	<!-- Header -->
	<div class="flex items-center gap-3">
		<button
			class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
			on:click={() => goto('/developer/api-keys')}
		>
			<ArrowLeft className="size-4" />
		</button>
		<div>
			<h1 class="text-2xl sm:text-3xl font-bold flex items-center gap-2">
				<svg class="size-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" /></svg>
				{$i18n.t('API Usage Guide')}
			</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Everything you need to integrate and manage your API key')}</p>
		</div>
	</div>

	<!-- Steps -->
	<div class="space-y-4">
		{#each steps as step}
			<div class="rounded-2xl border border-gray-100 dark:border-gray-800 p-5 space-y-3">
				<div class="flex items-start gap-3">
					<div class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0
						{step.color === 'blue' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' :
						 step.color === 'violet' ? 'bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400' :
						 step.color === 'emerald' ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' :
						 step.color === 'amber' ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' :
						 step.color === 'pink' ? 'bg-pink-100 text-pink-600 dark:bg-pink-900/30 dark:text-pink-400' :
						 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}">
						{step.num}
					</div>
					<div>
						<h3 class="font-semibold">{$i18n.t(step.title)}</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t(step.desc)}</p>
					</div>
				</div>

				{#if step.num === '1'}
					<div class="ml-11 rounded-xl bg-gray-900 dark:bg-gray-950 p-3 font-mono text-xs text-emerald-400">
						Authorization: Bearer sk-xxxxxxxxxxxxxxxx
					</div>
				{:else if step.num === '2'}
					<!-- Tabs for cURL / Python -->
					<div class="ml-11 space-y-2">
						<div class="text-xs font-medium text-gray-500 uppercase tracking-wider">{$i18n.t('cURL Example')}</div>
						<pre class="rounded-xl bg-gray-900 dark:bg-gray-950 p-3 text-xs text-gray-300 overflow-x-auto">{curlExample}</pre>
						<div class="text-xs font-medium text-gray-500 uppercase tracking-wider mt-3">{$i18n.t('Python (OpenAI SDK)')}</div>
						<pre class="rounded-xl bg-gray-900 dark:bg-gray-950 p-3 text-xs text-gray-300 overflow-x-auto">{pythonExample}</pre>
					</div>
				{:else if step.num === '4'}
					<ul class="ml-11 space-y-1.5 text-sm text-gray-500">
						<li class="flex items-start gap-2"><span class="text-amber-500 mt-0.5">•</span> {$i18n.t('Each plan has per-minute request limits (RPM)')}</li>
						<li class="flex items-start gap-2"><span class="text-amber-500 mt-0.5">•</span> {$i18n.t('Requests stop when credits are exhausted')}</li>
						<li class="flex items-start gap-2"><span class="text-amber-500 mt-0.5">•</span> {$i18n.t('Rotate your key immediately if you suspect leakage')}</li>
						<li class="flex items-start gap-2"><span class="text-amber-500 mt-0.5">•</span> {$i18n.t('Web chat is NOT affected by API key credits')}</li>
					</ul>
				{:else if step.num === '6'}
					<div class="ml-11">
						<pre class="rounded-xl bg-gray-900 dark:bg-gray-950 p-3 text-xs text-gray-300 overflow-x-auto">{webhookExample}</pre>
					</div>
				{/if}
			</div>
		{/each}
	</div>

	<!-- CTA -->
	<div class="text-center py-4 space-y-3">
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
				on:click={() => goto('/developer/api-keys/pricing')}
			>
				{$i18n.t('View Pricing')}
			</button>
		</div>
	</div>
</div>
