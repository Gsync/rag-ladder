<script lang="ts">
	import { guidedPanel } from '$lib/stores/shell.svelte';
</script>

<aside class="guided-panel" aria-label="Guided panel">
	<h2>Guided</h2>
	<section>
		<h3>What this shows</h3>
		<p>{guidedPanel.whatThisShows}</p>
	</section>
	<section>
		<h3>Try this</h3>
		<p>{guidedPanel.tryThis}</p>
	</section>
	{#if guidedPanel.aha}
		<section>
			<h3>The aha</h3>
			<p>{guidedPanel.aha}</p>
		</section>
	{/if}
</aside>

<style>
	.guided-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		background: var(--surface);
		border-left: 1px solid var(--structure);
		padding: 1rem;
		min-width: 0;
	}

	h2 {
		font-size: 0.875rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--structure);
	}

	h3 {
		font-size: 0.75rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--signal);
		margin-bottom: 0.25rem;
	}

	p {
		font-family: var(--font-body);
		color: var(--text);
		font-size: 0.875rem;
		line-height: 1.4;
	}

	@media (max-width: 768px) {
		.guided-panel {
			border-left: none;
			border-top: 1px solid var(--structure);
		}
	}
</style>
