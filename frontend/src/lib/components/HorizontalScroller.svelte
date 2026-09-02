<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import { press } from '$lib/actions/press';

	let {
		ariaLabel,
		children
	}: {
		ariaLabel: string;
		children: Snippet;
	} = $props();

	const EDGE_TOLERANCE = 2;
	const WHEEL_LINE_DISTANCE = 8;
	const MINIMUM_BUTTON_STEP = 40;
	const MAXIMUM_BUTTON_STEP = 96;
	const BUTTON_STEP_RATIO = 0.09;

	let viewport = $state<HTMLDivElement>();
	let content = $state<HTMLDivElement>();
	let canScrollBackward = $state(false);
	let canScrollForward = $state(false);

	function maximumScroll(): number {
		return viewport ? Math.max(0, viewport.scrollWidth - viewport.clientWidth) : 0;
	}

	function updateControls(): void {
		if (!viewport) return;
		const maximum = maximumScroll();
		canScrollBackward = viewport.scrollLeft > EDGE_TOLERANCE;
		canScrollForward = viewport.scrollLeft < maximum - EDGE_TOLERANCE;
	}

	function scrollByPage(direction: -1 | 1): void {
		if (!viewport) return;
		const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		const distance = Math.min(
			MAXIMUM_BUTTON_STEP,
			Math.max(MINIMUM_BUTTON_STEP, viewport.clientWidth * BUTTON_STEP_RATIO)
		);
		viewport.scrollBy({
			left: direction * distance,
			behavior: reducedMotion ? 'auto' : 'smooth'
		});
	}

	onMount(() => {
		if (!viewport || !content) return;

		const currentViewport = viewport;
		const observer = new ResizeObserver(updateControls);
		observer.observe(currentViewport);
		observer.observe(content);

		function handleWheel(event: WheelEvent): void {
			// Native horizontal trackpad gestures already carry deltaX. Translate only the
			// dominant vertical wheel axis, and release it back to the page at either edge.
			if (event.ctrlKey || Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
			const maximum = maximumScroll();
			if (maximum <= EDGE_TOLERANCE) return;

			const multiplier =
				event.deltaMode === WheelEvent.DOM_DELTA_LINE
					? WHEEL_LINE_DISTANCE
					: event.deltaMode === WheelEvent.DOM_DELTA_PAGE
						? currentViewport.clientWidth
						: 1;
			const distance = event.deltaY * multiplier;
			const canMove =
				(distance < 0 && currentViewport.scrollLeft > EDGE_TOLERANCE) ||
				(distance > 0 && currentViewport.scrollLeft < maximum - EDGE_TOLERANCE);
			if (!canMove) return;

			event.preventDefault();
			currentViewport.scrollLeft = Math.max(
				0,
				Math.min(maximum, currentViewport.scrollLeft + distance)
			);
		}

		currentViewport.addEventListener('wheel', handleWheel, { passive: false });
		currentViewport.addEventListener('scroll', updateControls, { passive: true });
		updateControls();

		return () => {
			observer.disconnect();
			currentViewport.removeEventListener('wheel', handleWheel);
			currentViewport.removeEventListener('scroll', updateControls);
		};
	});
</script>

<div class="horizontal-scroller">
	<button
		type="button"
		class="rail-button previous"
		aria-label="Scorri a sinistra"
		disabled={!canScrollBackward}
		use:press={{ disabled: !canScrollBackward }}
		onclick={() => scrollByPage(-1)}
	>
		<span aria-hidden="true">‹</span>
	</button>
	<div class="rail-viewport" bind:this={viewport} role="region" aria-label={ariaLabel}>
		<div class="rail-content" bind:this={content}>{@render children()}</div>
	</div>
	<button
		type="button"
		class="rail-button next"
		aria-label="Scorri a destra"
		disabled={!canScrollForward}
		use:press={{ disabled: !canScrollForward }}
		onclick={() => scrollByPage(1)}
	>
		<span aria-hidden="true">›</span>
	</button>
</div>

<style>
	.horizontal-scroller {
		position: relative;
		min-width: 0;
	}

	.rail-viewport {
		max-width: 100%;
		overflow-x: auto;
		overflow-y: hidden;
		padding-bottom: 0.55rem;
		overscroll-behavior-inline: contain;
		touch-action: pan-x pan-y;
	}

	.rail-content {
		width: max-content;
		min-width: 100%;
	}

	.rail-button {
		position: absolute;
		top: 50%;
		z-index: 5;
		display: grid;
		place-items: center;
		width: 2.6rem;
		height: 2.6rem;
		min-height: 0;
		padding: 0;
		border: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
		border-radius: 50%;
		background: color-mix(in srgb, var(--surface) 88%, transparent);
		backdrop-filter: blur(16px) saturate(160%);
		box-shadow: 0 8px 24px -10px rgb(0 0 0 / 42%);
		color: var(--text);
		font: inherit;
		cursor: pointer;
		transform: translateY(-50%);
		transition:
			opacity 160ms ease,
			border-color 160ms ease,
			background-color 160ms ease;
	}

	.rail-button.previous {
		left: 0.55rem;
	}

	.rail-button.next {
		right: 0.55rem;
	}

	.rail-button span {
		font-size: 1.75rem;
		font-weight: 450;
		line-height: 0.8;
		transform: translateY(-0.06em);
	}

	.rail-button:hover,
	.rail-button:focus-visible {
		border-color: var(--border-hover);
		background: color-mix(in srgb, var(--input-bg) 94%, transparent);
		outline: none;
	}

	.rail-button:disabled {
		opacity: 0;
		pointer-events: none;
	}

	@media (pointer: coarse) {
		.rail-button {
			display: none;
		}
	}

	@media (prefers-reduced-transparency: reduce) {
		.rail-button {
			background: var(--surface);
			backdrop-filter: none;
		}
	}

	@media (prefers-contrast: more) {
		.rail-button {
			border-color: var(--text);
			box-shadow: none;
		}
	}
</style>
