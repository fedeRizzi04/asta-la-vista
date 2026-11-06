<script lang="ts">
	import { onMount } from 'svelte';
	import { slide } from 'svelte/transition';
	import { press } from '$lib/actions/press';
	import { motionPreferences } from '$lib/motionPreferences.svelte';
	import type { AppVersion } from '$lib/system';

	let { appVersion }: { appVersion: AppVersion } = $props();

	// Remembers the version the user dismissed: the banner comes back only for a newer one.
	const DISMISSED_KEY = 'dismissed-update';
	let dismissed = $state<string | null>(null);
	let ready = $state(false);

	onMount(() => {
		try {
			dismissed = localStorage.getItem(DISMISSED_KEY);
		} catch {
			// Storage can be unavailable (e.g. blocked site data): the banner just shows again.
		}
		ready = true;
	});

	let visible = $derived(
		ready &&
			appVersion.update_available &&
			appVersion.release_url !== null &&
			appVersion.latest_version !== dismissed
	);

	function dismiss(): void {
		dismissed = appVersion.latest_version;
		try {
			if (dismissed) localStorage.setItem(DISMISSED_KEY, dismissed);
		} catch {
			// See above: only this page view hides the banner.
		}
	}
</script>

{#if visible}
	<div
		class="update-banner"
		role="status"
		transition:slide={{ duration: motionPreferences.reducedMotion ? 0 : 220 }}
	>
		<div class="update-content">
			<p>
				È disponibile <strong>Asta la Vista {appVersion.latest_version}</strong>
				<span class="current">(stai usando la {appVersion.version})</span>
			</p>
			<div class="update-actions">
				<!-- External page on GitHub, not an app route: resolve() does not apply. -->
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
				<a href={appVersion.release_url} target="_blank" rel="noopener noreferrer" use:press>
					Scarica
				</a>
				<button
					type="button"
					aria-label="Nascondi avviso di aggiornamento"
					use:press
					onclick={dismiss}
				>
					&times;
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.update-banner {
		border-bottom: 1px solid var(--success-border);
		background: var(--primary-soft);
		color: var(--primary-soft-text);
		font-size: 0.88rem;
	}

	.update-content {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 0.5rem 1rem;
		width: min(1180px, calc(100% - 3rem));
		margin: 0 auto;
		padding: 0.6rem 0;
	}

	p {
		margin: 0;
		line-height: 1.4;
	}

	.current {
		color: var(--muted);
	}

	.update-actions {
		display: flex;
		flex: 0 0 auto;
		align-items: center;
		gap: 0.75rem;
	}

	a {
		padding: 0.35rem 0.85rem;
		border-radius: 999px;
		background: var(--primary);
		color: var(--on-primary);
		font-weight: 600;
		text-decoration: none;
	}

	a:hover {
		filter: brightness(1.1);
	}

	button {
		min-height: auto;
		padding: 0;
		border: 0;
		background: transparent;
		color: inherit;
		font-size: 1.15rem;
		line-height: 1;
		opacity: 0.7;
		cursor: pointer;
		transition: opacity 140ms ease;
	}

	button:hover {
		opacity: 1;
	}

	@media (max-width: 720px) {
		.update-content {
			width: min(100% - 2rem, 1180px);
		}
	}
</style>
