<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { chunkText, type Chunk } from '$lib/chunker';
	import { cosineSimilarity } from '$lib/cosine';
	import { embed, embedBatch } from '$lib/embedder';

	const FEATURE_PACKAGE = 'npm:debug';
	const FIXED_QUERY = "how do I add a custom formatter to debug's output?";

	const SIZE_MIN = 150;
	const SIZE_MAX = 2500;
	const SIZE_DEFAULT = 600;
	const SMALL_THRESHOLD = 250;
	const LARGE_THRESHOLD = 1800;

	const OVERLAP_MAX = 400;
	const OVERLAP_DEFAULT = 80;
	const RECOMPUTE_DEBOUNCE_MS = 350;

	let readme: string | null = $state(null);
	let loadError: string | null = $state(null);
	let modelLoading = $state(false);
	let computing = $state(false);

	let chunkSize = $state(SIZE_DEFAULT);
	let overlapInput = $state(OVERLAP_DEFAULT);
	let effectiveOverlap = $derived(Math.min(overlapInput, chunkSize - 20));

	let chunks: Chunk[] = $state([]);
	let scores: number[] = $state([]);
	let winnerIndex = $state(-1);

	let queryVector: Float32Array | null = null;
	let debounceHandle: ReturnType<typeof setTimeout> | null = null;

	onMount(async () => {
		try {
			const data = (await fetch(`${base}/data/npm/readmes.json`).then((r) => r.json())) as Record<
				string,
				string
			>;
			readme = data[FEATURE_PACKAGE] ?? null;
			if (!readme) loadError = `no README cached for ${FEATURE_PACKAGE}`;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'failed to load README';
		}
	});

	async function recompute(text: string, size: number, overlap: number) {
		const newChunks = chunkText(text, size, overlap);
		chunks = newChunks;
		computing = true;
		loadError = null;
		try {
			if (!queryVector) {
				modelLoading = true;
				queryVector = await embed(FIXED_QUERY);
				modelLoading = false;
			}
			const { data, dim } = await embedBatch(newChunks.map((c) => c.text));
			const newScores = newChunks.map((_, i) =>
				cosineSimilarity(queryVector!, data.subarray(i * dim, i * dim + dim))
			);
			scores = newScores;
			winnerIndex = newScores.reduce((best, s, i) => (s > newScores[best] ? i : best), 0);
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'retrieval failed';
		} finally {
			computing = false;
			modelLoading = false;
		}
	}

	$effect(() => {
		const text = readme;
		const size = chunkSize;
		const overlap = effectiveOverlap;
		if (!text) return;
		if (debounceHandle) clearTimeout(debounceHandle);
		debounceHandle = setTimeout(() => recompute(text, size, overlap), RECOMPUTE_DEBOUNCE_MS);
	});
</script>

<div class="lab">
	<div class="controls">
		<label>
			<span class="control-label">chunk size <span class="muted">({chunkSize} chars)</span></span>
			<input type="range" min={SIZE_MIN} max={SIZE_MAX} step="10" bind:value={chunkSize} />
		</label>
		<label>
			<span class="control-label"
				>overlap <span class="muted">({effectiveOverlap} chars)</span></span
			>
			<input type="range" min="0" max={OVERLAP_MAX} step="10" bind:value={overlapInput} />
		</label>
	</div>

	{#if chunkSize <= SMALL_THRESHOLD}
		<p class="warning">
			chunks too small to hold context — the winning chunk may cut off mid-idea.
		</p>
	{:else if chunkSize >= LARGE_THRESHOLD}
		<p class="warning">
			chunks this large blur distinct sections together — retrieval gets less precise.
		</p>
	{/if}

	{#if loadError}
		<p class="overlay error">{loadError}</p>
	{:else if !readme}
		<p class="overlay">loading readme…</p>
	{:else}
		<div class="ribbon" aria-label="README chunked into {chunks.length} pieces">
			{#each chunks as chunk, i (chunk.start)}
				<span
					class="band"
					class:winner={i === winnerIndex}
					style:flex-grow={chunk.text.length}
					title={chunk.text.slice(0, 120)}
				>
					<span class="band-index">{i}</span>
				</span>
			{/each}
		</div>

		<div class="result">
			<div class="query-row">
				<span class="control-label">fixed query</span>
				<span class="lit-query">{FIXED_QUERY}</span>
			</div>
			{#if modelLoading}
				<p class="overlay">loading the embedder…</p>
			{:else if computing}
				<p class="overlay">recomputing…</p>
			{:else if winnerIndex >= 0}
				<div class="winner-panel">
					<div class="winner-header">
						<span class="lit">chunk {winnerIndex}</span>
						<span class="muted">score {scores[winnerIndex].toFixed(3)}</span>
					</div>
					<p class="winner-text">{chunks[winnerIndex].text}</p>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.lab {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		height: 100%;
	}

	.controls {
		display: flex;
		gap: 2rem;
		flex-wrap: wrap;
	}

	.controls label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
		min-width: 12rem;
	}

	.control-label {
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
	}

	.muted {
		color: var(--muted);
	}

	.warning {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		color: var(--muted);
		border: 1px dashed var(--structure);
		border-radius: 0.25rem;
		padding: 0.5rem 0.75rem;
	}

	.overlay {
		font-family: var(--font-data);
		color: var(--muted);
	}

	.overlay.error {
		color: var(--fail);
	}

	.ribbon {
		display: flex;
		width: 100%;
		height: 2.5rem;
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		overflow: hidden;
	}

	.band {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 3px;
		background: var(--surface);
		border-right: 1px solid var(--ink);
		cursor: default;
	}

	.band.winner {
		background: color-mix(in srgb, var(--signal) 35%, var(--surface));
	}

	.band-index {
		font-family: var(--font-data);
		font-size: 0.625rem;
		color: var(--muted);
	}

	.band.winner .band-index {
		color: var(--signal);
	}

	.result {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.query-row {
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
		font-family: var(--font-data);
		font-size: 0.875rem;
	}

	.winner-panel {
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.75rem 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.winner-header {
		display: flex;
		gap: 0.75rem;
		align-items: baseline;
		font-family: var(--font-data);
		font-size: 0.75rem;
	}

	.winner-text {
		font-family: var(--font-body);
		font-size: 0.875rem;
		line-height: 1.5;
		white-space: pre-wrap;
		color: var(--text);
	}
</style>
