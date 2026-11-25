<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import DialogHost from '$lib/components/DialogHost.svelte';
	import ShortcutsPanel from '$lib/components/ShortcutsPanel.svelte';
	import ToastStack from '$lib/components/ToastStack.svelte';
	import UpdateBanner from '$lib/components/UpdateBanner.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { press } from '$lib/actions/press';
	import { slidingIndicator } from '$lib/actions/slidingIndicator.svelte';
	import { locale, setLocale, t, type Locale } from '$lib/i18n';
	import { installShortcuts, registerShortcuts, shortcutsPanel } from '$lib/shortcuts.svelte';
	import type { AppVersion } from '$lib/system';
	import { watchVersion } from '$lib/versionWatcher';
	import '../app.css';

	let { children } = $props();
	let theme = $state<'light' | 'dark'>('light');
	let scrolled = $state(false);
	let navEl = $state<HTMLElement>();
	let activeNavEl = $state<HTMLElement>();
	let headerEl = $state<HTMLElement>();
	let appVersion = $state<AppVersion>();

	const navigation: { href: '/' | '/players' | '/strategies' | '/auctions'; label: string }[] = [
		{ href: '/', label: t.navigation.home },
		{ href: '/players', label: t.navigation.playerList },
		{ href: '/strategies', label: t.navigation.strategies },
		{ href: '/auctions', label: t.navigation.auctions }
	];

	function isCurrent(href: string): boolean {
		return href === '/' ? page.url.pathname === href : page.url.pathname.startsWith(href);
	}

	$effect(() => {
		// Re-measure whenever the route changes, so the indicator glides to the new tab.
		void page.url.pathname;
		activeNavEl = navEl?.querySelector<HTMLElement>('a[aria-current="page"]') ?? undefined;
	});

	$effect(() =>
		registerShortcuts([
			{
				keys: '?',
				description: t.shortcuts.showShortcuts,
				group: t.shortcuts.general,
				handler: () => (shortcutsPanel.open = true)
			}
		])
	);
	onMount(installShortcuts);

	onMount(() => {
		theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';

		const stopWatchingVersion = watchVersion((version) => (appVersion = version));

		function onScroll(): void {
			scrolled = window.scrollY > 4;
		}
		onScroll();
		window.addEventListener('scroll', onScroll, { passive: true });

		// Exposed as --header-height so sticky elements further down a page (e.g. the
		// strategy screen's role tabs) can pin themselves just below the header without
		// hard-coding its height, which changes between the desktop and mobile layouts.
		function updateHeaderHeight(): void {
			document.documentElement.style.setProperty(
				'--header-height',
				`${headerEl?.offsetHeight ?? 0}px`
			);
		}
		updateHeaderHeight();
		const headerObserver = new ResizeObserver(updateHeaderHeight);
		if (headerEl) headerObserver.observe(headerEl);

		return () => {
			window.removeEventListener('scroll', onScroll);
			headerObserver.disconnect();
			stopWatchingVersion();
		};
	});

	function toggleTheme(): void {
		theme = theme === 'light' ? 'dark' : 'light';
		document.documentElement.dataset.theme = theme;
		document.documentElement.style.colorScheme = theme;
		localStorage.setItem('theme', theme);
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Asta la Vista</title>
	<meta name="description" content={t.navigation.appDescription} />
</svelte:head>

<header class="app-header" class:is-scrolled={scrolled} bind:this={headerEl}>
	<a class="brand" href={resolve('/')} aria-label="Asta la Vista, home" use:press>Asta la Vista</a>
	<div class="header-actions">
		<nav aria-label={t.navigation.mainNavigation} bind:this={navEl}>
			{#each navigation as item (item.href)}
				<a
					href={resolve(item.href)}
					aria-current={isCurrent(item.href) ? 'page' : undefined}
					use:press
				>
					{item.label}
				</a>
			{/each}
			<span class="tab-indicator" use:slidingIndicator={activeNavEl} aria-hidden="true"></span>
		</nav>
		<Select
			class="language-select"
			aria-label={t.navigation.language}
			value={locale}
			onchange={(event) => setLocale(event.currentTarget.value as Locale)}
		>
			<option value="en" lang="en">English</option>
			<option value="it" lang="it">Italiano</option>
		</Select>
		<Button
			variant="secondary"
			size="sm"
			class="theme-toggle"
			onclick={toggleTheme}
			aria-label={theme === 'light'
				? t.navigation.switchToDarkTheme
				: t.navigation.switchToLightTheme}
			aria-pressed={theme === 'dark'}
		>
			<span aria-hidden="true"></span>
			{theme === 'light' ? t.navigation.darkTheme : t.navigation.lightTheme}
		</Button>
	</div>
</header>

{#if appVersion}
	<UpdateBanner {appVersion} />
{/if}

<main>
	{@render children()}
</main>

<footer class="app-footer">
	{#if appVersion}
		<span>Asta la Vista v{appVersion.version}</span>
	{/if}
</footer>

<ToastStack />
<DialogHost />
<ShortcutsPanel />

<style>
	.header-actions :global(.language-select) {
		align-self: center;
		width: auto;
		min-height: 1.75rem;
		padding: 0 0.55rem;
		border-radius: var(--radius-xs);
		font-size: 0.8rem;
	}

	/* Beside the brand, so that the navigation keeps its room on narrow screens. */
	@media (max-width: 720px) {
		.header-actions :global(.language-select) {
			position: absolute;
			top: 0.4rem;
			right: 1rem;
		}
	}
</style>
