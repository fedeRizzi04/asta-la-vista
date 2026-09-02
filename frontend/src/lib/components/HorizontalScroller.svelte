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
	const BUTTON_STEP_RATIO = 0.9;
	/** Pointer movement, in px, before a mouse press counts as a drag rather than a click. */
	const DRAG_THRESHOLD = 6;

	let viewport = $state<HTMLDivElement>();
	let content = $state<HTMLDivElement>();
	let canScrollBackward = $state(false);
	let canScrollForward = $state(false);
	let dragging = $state(false);

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
		viewport.scrollBy({
			left: direction * viewport.clientWidth * BUTTON_STEP_RATIO,
			behavior: reducedMotion ? 'auto' : 'smooth'
		});
	}

	onMount(() => {
		if (!viewport || !content) return;

		const currentViewport = viewport;
		const currentContent = content;
		const observer = new ResizeObserver(updateControls);
		observer.observe(currentViewport);
		observer.observe(currentContent);

		// Mouse-only click-and-drag scrolling. Touch/pen keep the native `touch-action: pan-x`
		// swipe below; a real scrollbar drag never reaches these listeners since it's chrome
		// painted around `currentViewport`, outside `currentContent`'s box.
		let dragPointerId: number | null = null;
		let dragStartX = 0;
		let dragStartScrollLeft = 0;
		let isDragGesture = false;
		let suppressNextClick = false;

		function handlePointerDown(event: PointerEvent): void {
			if (event.pointerType !== 'mouse' || event.button !== 0) return;
			dragPointerId = event.pointerId;
			dragStartX = event.clientX;
			dragStartScrollLeft = currentViewport.scrollLeft;
			isDragGesture = false;
		}

		function handlePointerMove(event: PointerEvent): void {
			if (dragPointerId === null || event.pointerId !== dragPointerId) return;
			const delta = event.clientX - dragStartX;
			if (!isDragGesture) {
				if (Math.abs(delta) < DRAG_THRESHOLD) return;
				isDragGesture = true;
				dragging = true;
				currentContent.setPointerCapture(dragPointerId);
			}
			event.preventDefault();
			currentViewport.scrollLeft = dragStartScrollLeft - delta;
		}

		function endDrag(event: PointerEvent): void {
			if (dragPointerId === null || event.pointerId !== dragPointerId) return;
			if (isDragGesture) {
				// The pointerup after a drag would otherwise still fire a click on whatever
				// element ended up under the cursor (e.g. a strategy tier's "call player"
				// button) — swallow exactly that one click.
				suppressNextClick = true;
				currentContent.releasePointerCapture(dragPointerId);
			}
			dragPointerId = null;
			isDragGesture = false;
			dragging = false;
		}

		function handleClickCapture(event: MouseEvent): void {
			if (!suppressNextClick) return;
			suppressNextClick = false;
			event.preventDefault();
			event.stopPropagation();
		}

		currentContent.addEventListener('pointerdown', handlePointerDown);
		currentContent.addEventListener('pointermove', handlePointerMove);
		currentContent.addEventListener('pointerup', endDrag);
		currentContent.addEventListener('pointercancel', endDrag);
		currentContent.addEventListener('click', handleClickCapture, { capture: true });
		currentViewport.addEventListener('scroll', updateControls, { passive: true });
		updateControls();

		return () => {
			observer.disconnect();
			currentContent.removeEventListener('pointerdown', handlePointerDown);
			currentContent.removeEventListener('pointermove', handlePointerMove);
			currentContent.removeEventListener('pointerup', endDrag);
			currentContent.removeEventListener('pointercancel', endDrag);
			currentContent.removeEventListener('click', handleClickCapture, { capture: true });
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
		<div class="rail-content" class:dragging bind:this={content}>{@render children()}</div>
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

	@media (pointer: fine) {
		.rail-content {
			cursor: grab;
		}

		.rail-content.dragging {
			cursor: grabbing;
			user-select: none;
		}
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
