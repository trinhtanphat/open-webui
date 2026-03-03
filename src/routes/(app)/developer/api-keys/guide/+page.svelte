<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext<any>('i18n');
	const curlExample = `curl -X POST "https://YOUR_DOMAIN/api/openai/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer sk-xxxxxxxxxxxxxxxx" \\
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'`;
	const webhookExample = `POST /api/v1/api-keys/webhooks/payment/{provider}
Header: X-BILLING-WEBHOOK-SECRET: your_webhook_secret
Body: {"topup_request_id":"...","status":"paid","tx_ref":"...","amount":12.5,"currency":"USD","credits":1200}`;
</script>

<div class="max-w-3xl mx-auto px-4 py-5 space-y-4 text-sm">
	<div>
		<div class="text-lg font-semibold">{$i18n.t('API Key Usage Guide')}</div>
		<div class="text-xs text-gray-500">{$i18n.t('How to use and top up your API key safely.')}</div>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">1. Get your key</div>
		<div class="text-gray-600 dark:text-gray-300">Open Settings → Account → API keys, create or regenerate your key, and keep it secret.</div>
		<div class="font-mono text-xs bg-gray-50 dark:bg-gray-900/40 rounded-lg px-3 py-2">Authorization: Bearer sk-xxxxxxxxxxxxxxxx</div>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">2. Call OpenAI-compatible endpoint</div>
		<div class="text-gray-600 dark:text-gray-300">Use your key against the OpenWebUI OpenAI-compatible API.</div>
		<pre class="text-xs bg-gray-50 dark:bg-gray-900/40 rounded-lg p-3 overflow-x-auto">{curlExample}</pre>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">3. Top up credits</div>
		<div class="text-gray-600 dark:text-gray-300">In Developer API Console, choose a payment account, submit amount + transaction reference, then wait for admin approval.</div>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">4. Rate limits and security</div>
		<ul class="list-disc ml-5 text-gray-600 dark:text-gray-300 space-y-1">
			<li>Each plan has per-minute request limits (RPM).</li>
			<li>Requests stop when credits are exhausted.</li>
			<li>Rotate your key immediately if you suspect leakage.</li>
		</ul>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">5. Admin payment account setup</div>
		<div class="text-gray-600 dark:text-gray-300">Admin opens Admin → API Keys and adds a payment account (bank or gateway). You can include transfer instructions and QR code URL for users.</div>
	</div>

	<div class="rounded-xl border border-gray-100 dark:border-gray-800 p-4 space-y-3">
		<div class="font-medium">6. Payment webhook setup (production)</div>
		<div class="text-gray-600 dark:text-gray-300">Set a `webhook_secret` in payment account metadata and configure your gateway webhook to call endpoint below.</div>
		<pre class="text-xs bg-gray-50 dark:bg-gray-900/40 rounded-lg p-3 overflow-x-auto">{webhookExample}</pre>
	</div>
</div>
