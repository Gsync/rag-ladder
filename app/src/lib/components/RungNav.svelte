<script lang="ts">
	import { RUNGS, rungState, VANILLA_MODULES, vanillaModuleState } from '$lib/stores/shell.svelte';
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
		{#if rung.id === 'vanilla' && rungState.active === 'vanilla'}
			<div class="sub-nav">
				{#each VANILLA_MODULES as mod (mod.id)}
					<button
						type="button"
						class="sub-rung"
						class:active={vanillaModuleState.active === mod.id}
						aria-current={vanillaModuleState.active === mod.id ? 'true' : undefined}
						onclick={() => (vanillaModuleState.active = mod.id)}
					>
						{mod.label}
					</button>
				{/each}
			</div>
		{/if}
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

	.sub-nav {
		display: flex;
		flex-direction: column;
		margin-left: 1.5rem;
		border-left: 2px solid var(--structure);
	}

	.sub-rung {
		background: transparent;
		border: none;
		color: var(--muted);
		font-family: var(--font-data);
		font-size: 0.8125rem;
		text-align: left;
		padding: 0.25rem 0.75rem;
		cursor: pointer;
	}

	.sub-rung:hover {
		color: var(--text);
	}

	.sub-rung.active {
		color: var(--signal);
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

		.sub-nav {
			flex-direction: row;
			margin-left: 0;
			border-left: none;
		}
	}
</style>
