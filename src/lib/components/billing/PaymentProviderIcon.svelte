<script lang="ts">
	export let provider: string = 'generic';
	export let accountName: string = '';
	export let size: string = 'size-5';

	const normalize = (value: string) =>
		(value || '')
			.toLowerCase()
			.trim()
			.replace(/[^a-z0-9]/g, ' ')
			.replace(/\s+/g, ' ');

	const detectProvider = (rawProvider: string, rawAccountName: string) => {
		const p = normalize(rawProvider);
		const n = normalize(rawAccountName);
		const haystack = `${p} ${n}`;

		if (haystack.includes('momo')) return 'momo';
		if (haystack.includes('vnpay') || haystack.includes('vn pay')) return 'vnpay';
		if (haystack.includes('zalopay') || haystack.includes('zalo pay') || haystack.includes('vng')) return 'zalopay';
		if (haystack.includes('techcombank') || haystack.includes(' tcb ')) return 'techcombank';
		if (haystack.includes('vietcombank') || haystack.includes(' vcb ')) return 'vietcombank';
		if (haystack.includes('sacombank') || haystack.includes(' stb ')) return 'sacombank';

		return p || 'generic';
	};

	const normalizedProvider = detectProvider(provider, accountName);
	const logoSrcByProvider: Record<string, string> = {
		momo: '/assets/payments/momo.svg',
		vnpay: '/assets/payments/vnpay.svg',
		zalopay: '/assets/payments/zalopay.svg',
		vng: '/assets/payments/zalopay.svg',
		techcombank: '/assets/payments/techcombank.svg',
		vietcombank: '/assets/payments/vietcombank.svg',
		sacombank: '/assets/payments/sacombank.svg'
	};
</script>

{#if logoSrcByProvider[normalizedProvider]}
	<img
		src={logoSrcByProvider[normalizedProvider]}
		alt={`${provider} logo`}
		class={`${size} rounded-md object-contain bg-white`}
		loading="lazy"
	/>
{:else}

{#if normalizedProvider === 'stripe'}
	<!-- Stripe logo -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#635BFF"/>
		<path d="M11.2 9.65c0-.68.56-.94 1.49-.94.95 0 2.15.29 3.1.8V6.7A8.27 8.27 0 0 0 12.69 6c-2.53 0-4.21 1.32-4.21 3.53 0 3.44 4.73 2.89 4.73 4.37 0 .81-.7 1.07-1.68 1.07-1.45 0-2.83-.6-3.85-1.41v2.89a9.77 9.77 0 0 0 3.85.82c2.59 0 4.37-1.28 4.37-3.52-.01-3.72-4.76-3.06-4.76-4.5Z" fill="white"/>
	</svg>
{:else if normalizedProvider === 'vnpay'}
	<!-- VNPay logo -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#0066CC"/>
		<text x="12" y="15" text-anchor="middle" fill="white" font-size="7" font-weight="bold" font-family="sans-serif">VN</text>
	</svg>
{:else if normalizedProvider === 'momo'}
	<!-- MoMo logo -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#A50064"/>
		<circle cx="12" cy="12" r="5.5" stroke="white" stroke-width="1.8" fill="none"/>
		<circle cx="12" cy="12" r="2.2" fill="white"/>
	</svg>
{:else if normalizedProvider === 'paypal'}
	<!-- PayPal logo -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#003087"/>
		<text x="12" y="15" text-anchor="middle" fill="white" font-size="7" font-weight="bold" font-family="sans-serif">PP</text>
	</svg>
{:else if normalizedProvider === 'bank_transfer'}
	<!-- Bank transfer icon -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#374151"/>
		<path d="M12 5L5 9v1h14V9L12 5Z" fill="white"/>
		<rect x="7" y="11" width="2" height="5" rx="0.5" fill="white"/>
		<rect x="11" y="11" width="2" height="5" rx="0.5" fill="white"/>
		<rect x="15" y="11" width="2" height="5" rx="0.5" fill="white"/>
		<rect x="5" y="17" width="14" height="2" rx="0.5" fill="white"/>
	</svg>
{:else}
	<!-- Generic payment icon -->
	<svg class={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<rect width="24" height="24" rx="4" fill="#6B7280"/>
		<path d="M4 9h16M4 9v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9M4 9V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
		<rect x="6" y="13" width="4" height="2" rx="0.5" fill="white"/>
	</svg>
{/if}
{/if}
