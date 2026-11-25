<script lang="ts">
	import { onMount } from 'svelte';
	import { slide } from 'svelte/transition';
	import { press } from '$lib/actions/press';
	import Button from '$lib/components/ui/Button.svelte';
	import { t } from '$lib/i18n';
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
				{t.common.updateAvailable}
				<strong>Asta la Vista {appVersion.latest_version}</strong>
				<span class="current">{t.common.currentVersion(appVersion.version)}</span>
			</p>
			<div class="update-actions">
				<!-- External page on GitHub, not an app route: resolve() does not apply. -->
				<Button
					href={appVersion.release_url ?? undefined}
					target="_blank"
					rel="noopener noreferrer"
				>
					{t.common.download}
				</Button>
				<button
					class="dismiss-button"
					type="button"
					aria-label={t.common.dismissUpdate}
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

	@media (max-width: 720px) {
		.update-content {
			width: min(100% - 2rem, 1180px);
		}
	}
</style>
