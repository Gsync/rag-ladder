<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import AskBar from '$lib/components/AskBar.svelte';
	import RungNav from '$lib/components/RungNav.svelte';
	import GuidedPanel from '$lib/components/GuidedPanel.svelte';
	import CompareStrip from '$lib/components/CompareStrip.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="shell">
	<header class="top-bar">
		<h1>RAG LADDER</h1>
		<span class="dataset">dataset: npm ▾</span>
		<div class="ask-bar-slot"><AskBar /></div>
	</header>

	<div class="nav-slot"><RungNav /></div>

	<main class="canvas">
		{@render children()}
	</main>

	<div class="guided-slot"><GuidedPanel /></div>

	<div class="compare-slot"><CompareStrip /></div>
</div>

<style>
	.shell {
		display: grid;
		grid-template-columns: 12rem 1fr 18rem;
		grid-template-rows: auto 1fr auto;
		grid-template-areas:
			'top top top'
			'nav canvas guided'
			'compare compare compare';
		min-height: 100vh;
	}

	.top-bar {
		grid-area: top;
		display: flex;
		align-items: center;
		gap: 1.5rem;
		background: var(--surface);
		border-bottom: 1px solid var(--structure);
		padding: 0.75rem 1rem;
	}

	.top-bar h1 {
		font-size: 1rem;
		letter-spacing: 0.1em;
		white-space: nowrap;
	}

	.dataset {
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
		white-space: nowrap;
	}

	.ask-bar-slot {
		flex: 1;
		min-width: 0;
	}

	.nav-slot {
		grid-area: nav;
		border-right: 1px solid var(--structure);
		padding: 1rem 0;
	}

	.canvas {
		grid-area: canvas;
		padding: 1.5rem;
		min-width: 0;
	}

	.guided-slot {
		grid-area: guided;
	}

	.compare-slot {
		grid-area: compare;
	}

	@media (max-width: 768px) {
		.shell {
			grid-template-columns: 1fr;
			grid-template-rows: auto auto 1fr auto auto;
			grid-template-areas:
				'top'
				'canvas'
				'guided'
				'compare'
				'nav';
		}

		.top-bar {
			flex-wrap: wrap;
		}

		.nav-slot {
			border-right: none;
			border-top: 1px solid var(--structure);
			padding: 0;
			position: sticky;
			bottom: 0;
			background: var(--surface);
		}
	}
</style>
