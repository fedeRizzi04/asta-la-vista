<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import favicon from '$lib/assets/favicon.svg';
	import '../app.css';

	let { children } = $props();

	const navigation: { href: '/' | '/players' | '/strategies' | '/auctions'; label: string }[] = [
		{ href: '/', label: 'Home' },
		{ href: '/players', label: 'Listone' },
		{ href: '/strategies', label: 'Strategie' },
		{ href: '/auctions', label: 'Aste' }
	];

	function isCurrent(href: string): boolean {
		return href === '/' ? page.url.pathname === href : page.url.pathname.startsWith(href);
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
	<nav aria-label="Navigazione principale">
		{#each navigation as item (item.href)}
			<a href={resolve(item.href)} aria-current={isCurrent(item.href) ? 'page' : undefined}>
				{item.label}
			</a>
		{/each}
	</nav>
</header>

<main>
	{@render children()}
</main>
