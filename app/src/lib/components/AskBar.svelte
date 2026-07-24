<script lang="ts">
	import { DEMO_QUESTIONS, queryState } from '$lib/stores/shell.svelte';

	function submit(question: string) {
		queryState.text = question;
	}
</script>

<div class="ask-bar">
	<form
		onsubmit={(e) => {
			e.preventDefault();
			submit(queryState.text);
		}}
	>
		<span class="prompt">question:</span>
		<input type="text" bind:value={queryState.text} placeholder="ask about a package…" />
	</form>
	<div class="chips">
		{#each DEMO_QUESTIONS as question (question)}
			<button type="button" class="chip" onclick={() => submit(question)}>{question}</button>
		{/each}
	</div>
</div>

<style>
	.ask-bar {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		min-width: 0;
	}

	form {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.375rem;
		padding: 0.375rem 0.625rem;
	}

	.prompt {
		font-family: var(--font-data);
		color: var(--structure);
		white-space: nowrap;
	}

	input {
		flex: 1;
		min-width: 0;
		background: transparent;
		border: none;
		color: var(--text);
		font-family: var(--font-data);
		outline: none;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
	}

	.chip {
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--structure);
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 999px;
		padding: 0.25rem 0.625rem;
		cursor: pointer;
	}

	.chip:hover {
		color: var(--query);
		border-color: var(--query);
	}
</style>
