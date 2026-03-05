import { mkdir, writeFile, access, constants, readFile } from 'fs/promises';
import { setGlobalDispatcher, ProxyAgent } from 'undici';

const outputDir = 'static/assets/payments';

const providers = [
	{
		name: 'momo',
		target: `${outputDir}/momo.svg`,
		fallbackTarget: `${outputDir}/momo.svg`,
		urls: [
			'https://upload.wikimedia.org/wikipedia/vi/f/fe/MoMo_Logo.png',
			'https://upload.wikimedia.org/wikipedia/commons/4/48/MoMo_logo.svg'
		]
	},
	{
		name: 'vnpay',
		target: `${outputDir}/vnpay.svg`,
		fallbackTarget: `${outputDir}/vnpay.svg`,
		urls: ['https://upload.wikimedia.org/wikipedia/commons/5/5b/VNPay_logo.svg']
	},
	{
		name: 'zalopay',
		target: `${outputDir}/zalopay.svg`,
		fallbackTarget: `${outputDir}/zalopay.svg`,
		urls: [
			'https://upload.wikimedia.org/wikipedia/vi/7/77/ZaloPay_Logo.png',
			'https://upload.wikimedia.org/wikipedia/commons/8/85/ZaloPay_logo.svg'
		]
	}
];

function initNetworkProxyFromEnv() {
	const allProxy = process.env.all_proxy || process.env.ALL_PROXY;
	const httpsProxy = process.env.https_proxy || process.env.HTTPS_PROXY;
	const httpProxy = process.env.http_proxy || process.env.HTTP_PROXY;
	const preferredProxy = httpsProxy || allProxy || httpProxy;

	if (!preferredProxy || !preferredProxy.startsWith('http')) return;

	let proxyUrl;
	try {
		proxyUrl = new URL(preferredProxy).toString();
	} catch {
		console.warn(`Invalid proxy URL: ${preferredProxy}`);
		return;
	}

	setGlobalDispatcher(new ProxyAgent({ uri: proxyUrl }));
	console.log(`Using network proxy: ${proxyUrl}`);
}

async function exists(filePath) {
	try {
		await access(filePath, constants.F_OK);
		return true;
	} catch {
		return false;
	}
}

async function saveBuffer(filePath, data) {
	await writeFile(filePath, data);
	const stats = await readFile(filePath);
	return stats.length;
}

async function tryDownload(url) {
	const response = await fetch(url, {
		headers: {
			'User-Agent': 'open-webui-payment-logo-sync/1.0'
		}
	});

	if (!response.ok) {
		throw new Error(`HTTP ${response.status}`);
	}

	const arrayBuffer = await response.arrayBuffer();
	return Buffer.from(arrayBuffer);
}

async function syncProvider(provider, force = false) {
	const alreadyExists = await exists(provider.target);
	if (alreadyExists && !force) {
		console.log(`${provider.name}: skipped (already exists)`);
		return;
	}

	for (const url of provider.urls) {
		try {
			const data = await tryDownload(url);
			const size = await saveBuffer(provider.target, data);
			console.log(`${provider.name}: downloaded from ${url} (${size} bytes)`);
			return;
		} catch (error) {
			console.warn(`${provider.name}: failed ${url} -> ${error}`);
		}
	}

	const fallbackExists = await exists(provider.fallbackTarget);
	if (fallbackExists) {
		console.log(`${provider.name}: kept local fallback asset`);
		return;
	}

	throw new Error(`${provider.name}: no downloadable source and no fallback asset`);
}

async function main() {
	initNetworkProxyFromEnv();

	const force = process.argv.includes('--force');
	await mkdir(outputDir, { recursive: true });

	for (const provider of providers) {
		await syncProvider(provider, force);
	}

	console.log('Payment logo sync completed.');
}

await main();
