<script lang="ts">
	let expanded = $state(false);
</script>

<footer class="compare-strip">
	<button type="button" class="toggle" onclick={() => (expanded = !expanded)}>
		COMPARE <span class="arrow" class:expanded>▸</span>
	</button>
	{#if expanded}
		<div class="cards">
			<div class="card"><span class="number">1</span> Vanilla</div>
			<div class="card"><span class="number">2</span> Graph</div>
			<div class="card"><span class="number">3</span> Agentic</div>
		</div>
	{/if}
</footer>

<style>
	.compare-strip {
		background: var(--surface);
		border-top: 1px solid var(--structure);
		padding: 0.5rem 1rem;
	}

	.toggle {
		background: transparent;
		border: none;
		color: var(--structure);
		font-family: var(--font-data);
		font-size: 0.75rem;
		letter-spacing: 0.05em;
		cursor: pointer;
	}

	.toggle:hover {
		color: var(--text);
	}

	.arrow {
		display: inline-block;
		transition: transform 0.15s ease;
	}

	.arrow.expanded {
		transform: rotate(90deg);
	}

	.cards {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.5rem;
		overflow-x: auto;
	}

	.card {
		flex: 1;
		min-width: 8rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: var(--ink);
		border: 1px solid var(--structure);
		border-radius: 0.375rem;
		padding: 0.5rem 0.75rem;
		font-family: var(--font-data);
		color: var(--structure);
	}

	.card .number {
		font-weight: 600;
		color: var(--signal);
	}

	@media (prefers-reduced-motion: reduce) {
		.arrow {
			transition: none;
		}
	}
</style>
