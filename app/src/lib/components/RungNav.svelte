<script lang="ts">
	import { RUNGS, rungState } from '$lib/stores/shell.svelte';
</script>

<nav class="rung-nav" aria-label="RAG ladder rungs">
	{#each RUNGS as rung (rung.id)}
		<button
			type="button"
			class="rung"
			class:active={rungState.active === rung.id}
			aria-current={rungState.active === rung.id ? 'true' : undefined}
			onclick={() => (rungState.active = rung.id)}
		>
			<span class="number">{rung.number}</span>
			<span class="label">{rung.label}</span>
		</button>
	{/each}
</nav>

<style>
	.rung-nav {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.rung {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: transparent;
		border: none;
		border-left: 2px solid var(--structure);
		color: var(--muted);
		font-family: var(--font-data);
		text-align: left;
		padding: 0.5rem 0.75rem;
		cursor: pointer;
	}

	.rung:hover {
		color: var(--text);
	}

	.rung.active {
		border-left-color: var(--signal);
		color: var(--signal);
	}

	.number {
		font-weight: 600;
	}

	@media (max-width: 768px) {
		.rung-nav {
			flex-direction: row;
			justify-content: space-around;
		}

		.rung {
			flex-direction: column;
			border-left: none;
			border-top: 2px solid var(--structure);
			text-align: center;
		}

		.rung.active {
			border-left: none;
			border-top-color: var(--signal);
		}
	}
</style>
