<script lang="ts">
	import { mantraRoleLabel, sortMantraRoles } from '$lib/mantraRoles';

	let {
		roles,
		compact = false
	}: {
		roles: string[];
		compact?: boolean;
	} = $props();

	let sortedRoles = $derived(sortMantraRoles(roles));
</script>

{#if sortedRoles.length > 0}
	<span class="mantra-roles" class:compact>
		{#each sortedRoles as role (role)}
			<span class="mantra-role">{mantraRoleLabel(role)}</span>
		{/each}
	</span>
{/if}

<style>
	.mantra-roles {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}

	.mantra-role {
		display: inline-grid;
		place-items: center;
		padding: 0.08rem 0.32rem;
		border: 1px solid var(--border);
		border-radius: 999px;
		background: var(--muted-bg);
		color: var(--subdued);
		font-size: 0.68rem;
		font-weight: 700;
		line-height: 1.4;
	}

	.mantra-roles.compact .mantra-role {
		padding: 0.05rem 0.28rem;
		font-size: 0.62rem;
	}
</style>
