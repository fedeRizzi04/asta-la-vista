<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import DialogHost from '$lib/components/DialogHost.svelte';
	import ToastStack from '$lib/components/ToastStack.svelte';
	import '../app.css';

	let { children } = $props();
	let theme = $state<'light' | 'dark'>('light');

	const navigation: { href: '/' | '/players' | '/strategies' | '/auctions'; label: string }[] = [
		{ href: '/', label: 'Home' },
		{ href: '/players', label: 'Listone' },
		{ href: '/strategies', label: 'Strategie' },
		{ href: '/auctions', label: 'Aste' }
	];

	function isCurrent(href: string): boolean {
		return href === '/' ? page.url.pathname === href : page.url.pathname.startsWith(href);
	}

	onMount(() => {
		theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
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

<header class="app-header">
	<a class="brand" href={resolve('/')} aria-label="Asta la Vista, home">Asta la Vista</a>
	<div class="header-actions">
		<nav aria-label="Navigazione principale">
			{#each navigation as item (item.href)}
				<a href={resolve(item.href)} aria-current={isCurrent(item.href) ? 'page' : undefined}>
					{item.label}
				</a>
			{/each}
		</nav>
		<button
			class="theme-toggle"
			type="button"
			onclick={toggleTheme}
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
