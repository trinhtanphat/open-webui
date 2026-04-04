<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { theme } from '$lib/stores';
	import { getLanguages, changeLanguage } from '$lib/i18n';

	const i18n = getContext<any>('i18n');

	let languages: { code: string; title: string }[] = [];
	let currentLang = 'en-US';

	const themes = ['dark', 'light'];

	const applyTheme = (_theme: string) => {
		let themeToApply = _theme;
		if (_theme === 'system') {
			themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		themes.filter((item) => item !== themeToApply).forEach((item) => {
			document.documentElement.classList.remove(item);
		});
		document.documentElement.classList.add(themeToApply);

		const metaThemeColor = document.querySelector('meta[name="theme-color"]');
		if (metaThemeColor) {
			const resolvedTheme = _theme === 'system'
				? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
				: _theme;
			metaThemeColor.setAttribute('content', resolvedTheme === 'light' ? '#ffffff' : '#171717');
		}

		if (typeof window !== 'undefined' && window.applyTheme) {
			window.applyTheme();
		}
	};

	const setThemeMode = (mode: 'dark' | 'light' | 'system') => {
		theme.set(mode);
		localStorage.setItem('theme', mode);
		applyTheme(mode);
	};

	const handleLanguageChange = (e: Event) => {
		const target = e.target as HTMLSelectElement;
		currentLang = target.value;
		changeLanguage(currentLang);
		localStorage.setItem('locale', currentLang);
	};

	onMount(async () => {
		languages = await getLanguages();
		currentLang = localStorage.getItem('locale') || $i18n.language || 'en-US';
	});
</script>

<div class="flex items-center gap-2">
	<!-- Theme Toggle -->
	<div class="flex items-center gap-0.5 p-0.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/70 dark:bg-gray-900/50">
		<button
			class="p-1.5 rounded-md transition-colors {$theme === 'light' ? 'bg-gray-100 dark:bg-gray-800 text-blue-600 dark:text-blue-400' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}"
			title={$i18n.t('Light mode')}
			on:click={() => setThemeMode('light')}
		>
			<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1.5m0 15V21m8.25-9H21M3 12h1.5m13.364 6.364 1.061 1.061M5.575 5.575l1.06 1.06m10.607-1.06-1.06 1.06M6.636 17.364l-1.06 1.06M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" /></svg>
		</button>
		<button
			class="p-1.5 rounded-md transition-colors {$theme === 'dark' ? 'bg-gray-100 dark:bg-gray-800 text-violet-600 dark:text-violet-400' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}"
			title={$i18n.t('Dark mode')}
			on:click={() => setThemeMode('dark')}
		>
			<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 1 0 21.752 15.002Z" /></svg>
		</button>
		<button
			class="p-1.5 rounded-md transition-colors {$theme === 'system' ? 'bg-gray-100 dark:bg-gray-800 text-emerald-600 dark:text-emerald-400' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}"
			title={$i18n.t('System mode')}
			on:click={() => setThemeMode('system')}
		>
			<svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.5h16.5A1.5 1.5 0 0 1 21.75 6v10.5a1.5 1.5 0 0 1-1.5 1.5H3.75a1.5 1.5 0 0 1-1.5-1.5V6a1.5 1.5 0 0 1 1.5-1.5Zm6 15h4.5" /></svg>
		</button>
	</div>

	<!-- Language Selector -->
	{#if languages.length > 0}
		<select
			class="appearance-none px-2 py-1.5 rounded-lg text-xs border border-gray-200 dark:border-gray-700 bg-white/70 dark:bg-gray-900/50 text-gray-600 dark:text-gray-300 cursor-pointer hover:border-gray-300 dark:hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
			value={currentLang}
			on:change={handleLanguageChange}
		>
			{#each languages as lang}
				<option value={lang.code}>{lang.title}</option>
			{/each}
		</select>
	{/if}
</div>
