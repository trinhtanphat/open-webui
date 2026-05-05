<script lang="ts">
	import { browser } from '$app/environment';
	import { getContext, onMount } from 'svelte';

	import { theme } from '$lib/stores';
	import Dropdown from '$lib/components/common/Dropdown.svelte';

	const i18n = getContext<any>('i18n');

	export let compact = false;

	type ColorScheme = 'light' | 'dark' | 'system';
	type ThemeOption = {
		id: string;
		label: string;
		swatch: string;
		preferredMode?: ColorScheme;
	};

	const PREFS_KEY = 'proxmoxai_prefs';
	const DEFAULT_PREFS = {
		theme: 'midnight',
		color_scheme: 'system' as ColorScheme,
		locale: 'vi',
		density: 'comfortable',
		reduced_motion: false,
		sidebar_collapsed: false
	};
	const LIGHT_VARIANTS: Record<string, string> = {
		anthropic: 'anthropic-light',
		v0: 'vercel-light',
		'github-dim': 'github-light'
	};
	const LIGHT_THEMES = new Set([
		'light',
		'sakura',
		'sepia',
		'paper',
		'arctic',
		'pastel-dream',
		'porcelain',
		'platinum',
		'spring',
		'summer',
		'minimal-light',
		'stripe',
		'notion',
		'vercel-light',
		'github-light',
		'anthropic-light'
	]);

	const themeOptions: ThemeOption[] = [
		{
			id: 'midnight',
			label: 'Midnight',
			swatch: 'linear-gradient(135deg,#0b0f17 50%,#3b82f6 50%)'
		},
		{
			id: 'anthropic',
			label: 'Anthropic',
			swatch: 'linear-gradient(135deg,#141311 50%,#cc785c 50%)'
		},
		{ id: 'v0', label: 'Vercel', swatch: 'linear-gradient(135deg,#000 50%,#fff 50%)' },
		{
			id: 'github-dim',
			label: 'GitHub',
			swatch: 'linear-gradient(135deg,#22272e 50%,#539bf5 50%)'
		},
		{ id: 'linear', label: 'Linear', swatch: 'linear-gradient(135deg,#08090a 50%,#5e6ad2 50%)' },
		{
			id: 'stripe',
			label: 'Stripe',
			swatch: 'linear-gradient(135deg,#fff 50%,#635bff 50%)',
			preferredMode: 'light'
		},
		{
			id: 'notion',
			label: 'Notion',
			swatch: 'linear-gradient(135deg,#fff 50%,#37352f 50%)',
			preferredMode: 'light'
		},
		{
			id: 'figma',
			label: 'Figma',
			swatch: 'linear-gradient(135deg,#1e1e1e 33%,#0d99ff 33% 66%,#a259ff 66%)'
		},
		{ id: 'raycast', label: 'Raycast', swatch: 'linear-gradient(135deg,#0d0d0d 50%,#ff6363 50%)' },
		{
			id: 'supabase',
			label: 'Supabase',
			swatch: 'linear-gradient(135deg,#1c1c1c 50%,#3ecf8e 50%)'
		},
		{ id: 'railway', label: 'Railway', swatch: 'linear-gradient(135deg,#13111c 50%,#9333ea 50%)' },
		{
			id: 'rosepine',
			label: 'Rose Pine',
			swatch: 'linear-gradient(135deg,#191724 50%,#c4a7e7 50%)'
		},
		{ id: 'nord', label: 'Nord', swatch: 'linear-gradient(135deg,#242933 50%,#88c0d0 50%)' },
		{
			id: 'tokyo-night',
			label: 'Tokyo Night',
			swatch: 'linear-gradient(135deg,#11121d 50%,#7aa2f7 50%)'
		},
		{ id: 'dracula', label: 'Dracula', swatch: 'linear-gradient(135deg,#282a36 50%,#bd93f9 50%)' },
		{ id: 'terminal', label: 'Terminal', swatch: 'linear-gradient(135deg,#020403 50%,#22c55e 50%)' }
	];
	const modeOptions: { id: ColorScheme; label: string }[] = [
		{ id: 'light', label: 'Light' },
		{ id: 'dark', label: 'Dark' },
		{ id: 'system', label: 'System' }
	];

	let showThemeMenu = false;
	let selectedTheme = DEFAULT_PREFS.theme;
	let selectedMode: ColorScheme = DEFAULT_PREFS.color_scheme;

	$: selectedThemeMeta =
		themeOptions.find((option) => option.id === selectedTheme) ?? themeOptions[0];
	$: selectedModeMeta = modeOptions.find((option) => option.id === selectedMode) ?? modeOptions[2];

	const normalizeThemeId = (id: string) => {
		if (id === 'vercel-light') return 'v0';
		if (id === 'github-light') return 'github-dim';
		if (id === 'anthropic-light') return 'anthropic';
		if (id === 'system') return 'midnight';
		return id || DEFAULT_PREFS.theme;
	};

	const systemPrefersLight = () =>
		browser && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;

	const resolveColorScheme = (prefs) => {
		const scheme = prefs.color_scheme || DEFAULT_PREFS.color_scheme;
		return scheme === 'system' ? (systemPrefersLight() ? 'light' : 'dark') : scheme;
	};

	const loadPrefs = () => {
		if (!browser) return { ...DEFAULT_PREFS };

		try {
			if ((window as any).__getThemePrefs) {
				return { ...DEFAULT_PREFS, ...(window as any).__getThemePrefs() };
			}

			const raw = localStorage.getItem(PREFS_KEY);
			if (raw) return { ...DEFAULT_PREFS, ...JSON.parse(raw) };

			const legacyTheme = localStorage.getItem('theme') as ColorScheme | null;
			if (legacyTheme === 'light' || legacyTheme === 'dark' || legacyTheme === 'system') {
				return { ...DEFAULT_PREFS, color_scheme: legacyTheme };
			}
		} catch (error) {
			console.debug('Unable to load theme preferences', error);
		}

		return { ...DEFAULT_PREFS };
	};

	const resolveTheme = (prefs) => {
		let resolvedTheme = prefs.theme || DEFAULT_PREFS.theme;
		const scheme = resolveColorScheme(prefs);

		if (resolvedTheme === 'system') {
			resolvedTheme = systemPrefersLight() ? 'light' : 'midnight';
		}

		if (scheme === 'light' && LIGHT_VARIANTS[resolvedTheme]) {
			resolvedTheme = LIGHT_VARIANTS[resolvedTheme];
		}

		return resolvedTheme;
	};

	const applyPrefsFallback = (prefs) => {
		const root = document.documentElement;
		const resolvedTheme = resolveTheme(prefs);
		const isLight = resolveColorScheme(prefs) === 'light';

		root.setAttribute('data-theme', resolvedTheme);
		root.setAttribute('data-density', prefs.density || DEFAULT_PREFS.density);
		root.lang = prefs.locale || DEFAULT_PREFS.locale;
		root.classList.toggle('light-mode', isLight);
		root.classList.toggle('light', isLight);
		root.classList.toggle('dark', !isLight);

		if (prefs.reduced_motion) root.setAttribute('data-motion', 'reduced');
		else root.removeAttribute('data-motion');

		const metaThemeColor = document.querySelector('meta[name="theme-color"]');
		metaThemeColor?.setAttribute('content', isLight ? '#ffffff' : '#171717');
	};

	const applyPrefs = (nextPrefs) => {
		if (!browser) return;

		const prefs = { ...DEFAULT_PREFS, ...loadPrefs(), ...nextPrefs };
		selectedTheme = normalizeThemeId(prefs.theme);
		selectedMode = prefs.color_scheme;

		try {
			localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
		} catch (error) {
			console.debug('Unable to persist theme preferences', error);
		}

		if ((window as any).__setTheme && (window as any).__setColorScheme) {
			(window as any).__setTheme(prefs.theme);
			(window as any).__setColorScheme(prefs.color_scheme);
		} else {
			applyPrefsFallback(prefs);
		}

		theme.set(selectedMode);
		localStorage.setItem('theme', selectedMode);
		window.dispatchEvent(new CustomEvent('vnso:theme-change', { detail: prefs }));
	};

	const setThemeFamily = (id: string) => {
		applyPrefs({ theme: id });
	};

	const setThemeMode = (mode: ColorScheme) => {
		applyPrefs({ color_scheme: mode });
	};

	onMount(() => {
		const prefs = loadPrefs();
		selectedTheme = normalizeThemeId(prefs.theme);
		selectedMode = prefs.color_scheme;
		theme.set(selectedMode);
	});
</script>

<Dropdown
	bind:show={showThemeMenu}
	align="end"
	side="bottom"
	contentClass="w-[278px] rounded-2xl border border-gray-100 bg-white p-2 text-sm shadow-lg dark:border-gray-800 dark:bg-gray-850 dark:text-white"
>
	<button
		type="button"
		class="flex items-center gap-2 rounded-xl border border-gray-200 bg-white/70 p-1.5 text-gray-600 transition hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900/50 dark:text-gray-300 dark:hover:bg-gray-850"
		aria-label={$i18n.t('Theme')}
		title={$i18n.t('Theme')}
	>
		<span
			class="size-4 shrink-0 rounded-full border border-gray-200 dark:border-gray-700"
			style={`background: ${selectedThemeMeta.swatch}`}
		/>
		{#if !compact}
			<span class="max-w-28 truncate text-xs font-medium">{selectedThemeMeta.label}</span>
		{/if}
	</button>

	<div slot="content" class="space-y-2">
		<div class="px-2 pt-1 text-xs font-medium text-gray-500 dark:text-gray-400">
			{$i18n.t('Theme')}
		</div>

		<div class="grid grid-cols-2 gap-1">
			{#each themeOptions as option (option.id)}
				<button
					type="button"
					class="flex min-w-0 items-center gap-2 rounded-xl px-2 py-1.5 text-left transition {selectedTheme ===
					option.id
						? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
						: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => setThemeFamily(option.id)}
					aria-pressed={selectedTheme === option.id}
				>
					<span
						class="size-4 shrink-0 rounded-full border border-gray-200 dark:border-gray-700"
						style={`background: ${option.swatch}`}
					/>
					<span class="truncate text-xs">{option.label}</span>
				</button>
			{/each}
		</div>

		<div class="border-t border-gray-100 pt-2 dark:border-gray-800">
			<div class="mb-1 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
				{$i18n.t('Color scheme')}
			</div>
			<div class="grid grid-cols-3 gap-1 rounded-xl bg-gray-50 p-1 dark:bg-gray-900/60">
				{#each modeOptions as option (option.id)}
					<button
						type="button"
						class="rounded-lg px-2 py-1 text-xs transition {selectedMode === option.id
							? 'bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-white'
							: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
						on:click={() => setThemeMode(option.id)}
						aria-pressed={selectedMode === option.id}
					>
						{$i18n.t(option.label)}
					</button>
				{/each}
			</div>
		</div>

		<div class="px-2 pb-1 text-[11px] text-gray-500 dark:text-gray-400">
			{selectedThemeMeta.label} · {$i18n.t(selectedModeMeta.label)}
		</div>
	</div>
</Dropdown>
