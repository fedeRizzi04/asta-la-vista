<script lang="ts">
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { t } from '$lib/i18n';
	import { mantraRoleLabel } from '$lib/mantraRoles';

	/** The Mantra roles as chips: none selected means all of them. */
	let { codes, selected = $bindable() }: { codes: string[]; selected: string[] } = $props();

	function toggle(code: string): void {
		selected = selected.includes(code)
			? selected.filter((candidate) => candidate !== code)
			: [...selected, code];
	}
</script>

{#if codes.length > 0}
	<div class="mantra-filter" role="group" aria-label={t.common.mantraSubRoles}>
		<ToggleChip pressed={selected.length === 0} onclick={() => (selected = [])}
			>{t.common.all}</ToggleChip
		>
		{#each codes as code (code)}
			<ToggleChip pressed={selected.includes(code)} onclick={() => toggle(code)}>
				{mantraRoleLabel(code)}
			</ToggleChip>
		{/each}
	</div>
{/if}

<style>
	.mantra-filter {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
</style>
