<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import DialogHost from '$lib/components/DialogHost.svelte';
	import ToastStack from '$lib/components/ToastStack.svelte';
	import { press } from '$lib/actions/press';
	import { slidingIndicator } from '$lib/actions/slidingIndicator.svelte';
	import '../app.css';

	let { children } = $props();
	let theme = $state<'light' | 'dark'>('light');
	let scrolled = $state(false);
	let navEl = $state<HTMLElement>();
	let activeNavEl = $state<HTMLElement>();
	let headerEl = $state<HTMLElement>();

	const navigation: { href: '/' | '/players' | '/strategies' | '/auctions'; label: string }[] = [
		{ href: '/', label: 'Home' },
		{ href: '/players', label: 'Listone' },
		{ href: '/strategies', label: 'Strategie' },
		{ href: '/auctions', label: 'Aste' }
	];

	function isCurrent(href: string): boolean {
		return href === '/' ? page.url.pathname === href : page.url.pathname.startsWith(href);
	}

	$effect(() => {
		// Re-measure whenever the route changes, so the indicator glides to the new tab.
		void page.url.pathname;
		activeNavEl = navEl?.querySelector<HTMLElement>('a[aria-current="page"]') ?? undefined;
	});

	onMount(() => {
		theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';

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
	<meta
		name="description"
		content="Assistente locale per preparare e seguire le aste Classic del fantacalcio."
	/>
</svelte:head>

<header class="app-header" class:is-scrolled={scrolled} bind:this={headerEl}>
	<a class="brand" href={resolve('/')} aria-label="Asta la Vista, home" use:press>Asta la Vista</a>
	<div class="header-actions">
		<nav aria-label="Navigazione principale" bind:this={navEl}>
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
		<button
			class="theme-toggle"
			type="button"
			onclick={toggleTheme}
			use:press
			aria-label={theme === 'light' ? 'Attiva tema scuro' : 'Attiva tema chiaro'}
			aria-pressed={theme === 'dark'}
		>
			<span aria-hidden="true"></span>
			{theme === 'light' ? 'Tema scuro' : 'Tema chiaro'}
		</button>
	</div>
</header>

<main>
	{@render children()}
</main>

<ToastStack />
<DialogHost />
