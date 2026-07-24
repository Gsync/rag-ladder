<script lang="ts">
	let {
		index,
		total,
		onPrev,
		onNext
	}: {
		index: number;
		total: number;
		onPrev: () => void;
		onNext: () => void;
	} = $props();
</script>

<div class="stepper" role="group" aria-label="Step control">
	<button type="button" onclick={onPrev} disabled={index <= 0} aria-label="Previous step">◀</button>
	<span class="position">{index + 1} / {total}</span>
	<button type="button" onclick={onNext} disabled={index >= total - 1} aria-label="Next step"
		>▶</button
	>
</div>

<style>
	.stepper {
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		font-family: var(--font-data);
	}

	button {
		background: var(--surface);
		border: 1px solid var(--structure);
		color: var(--text);
		border-radius: 0.25rem;
		padding: 0.25rem 0.625rem;
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		border-color: var(--signal);
		color: var(--signal);
	}

	button:disabled {
		color: var(--structure);
		cursor: not-allowed;
	}

	.position {
		color: var(--structure);
	}
</style>
