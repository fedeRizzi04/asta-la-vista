<script lang="ts">
	let {
		name,
		color = null,
		compact = false
	}: {
		name: string;
		color?: string | null;
		compact?: boolean;
	} = $props();
</script>

<span class="tier-badge" class:compact style:--tier-color={color ?? 'var(--tier-default)'}>
	<span class="tier-badge-accent" aria-hidden="true"></span>
	<span class="tier-badge-name">{name}</span>
</span>

<style>
	.tier-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		max-width: 100%;
		padding: 0.22rem 0.45rem 0.22rem 0.3rem;
		border: 1px solid var(--tier-badge-border);
		border-radius: 0.38rem;
		background: var(--tier-badge-bg);
		color: var(--text);
		font-size: 0.78rem;
		font-weight: 750;
		line-height: 1.2;
		text-align: left;
	}

	.tier-badge-accent {
		width: 0.55rem;
		align-self: stretch;
		min-height: 1.15rem;
		flex: 0 0 auto;
		border: 1px solid rgb(0 0 0 / 14%);
		border-radius: 0.18rem;
		background: var(--tier-color);
	}

	.tier-badge-name {
		overflow-wrap: anywhere;
	}

	.tier-badge.compact {
		font-size: 0.72rem;
	}

	.tier-badge.compact .tier-badge-accent {
		width: 0.48rem;
		min-height: 1rem;
	}
</style>
