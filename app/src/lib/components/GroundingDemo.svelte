<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';

	type RetrievedChunk = { start: number; text: string; score: number };
	type GroundingData = {
		question: string;
		package_id: string;
		chunks: RetrievedChunk[];
		no_context_answer: string;
		grounded_answer: string;
		citations: number[];
	};

	let data: GroundingData | null = $state(null);
	let loadError: string | null = $state(null);
	let included: Record<number, boolean> = $state({});

	onMount(async () => {
		try {
			data = (await fetch(`${base}/data/npm/grounding.json`).then((r) =>
				r.json()
			)) as GroundingData;
			included = Object.fromEntries(data.chunks.map((c) => [c.start, true]));
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'failed to load grounding demo';
		}
	});

	function toggle(start: number) {
		included[start] = !included[start];
	}

	let assembledChunks = $derived.by(() => {
		const loaded = data;
		if (!loaded) return [];
		return [...loaded.chunks].sort((a, b) => a.start - b.start).filter((c) => included[c.start]);
	});
	let anyCitationIncluded = $derived.by(() => {
		const loaded = data;
		if (!loaded) return false;
		return loaded.citations.some((start) => included[start]);
	});
</script>

<div class="lab">
	{#if loadError}
		<p class="overlay error">{loadError}</p>
	{:else if !data}
		<p class="overlay">loading grounding demo…</p>
	{:else}
		<div class="query-row">
			<span class="control-label">fixed question</span>
			<span class="lit-query">{data.question}</span>
		</div>

		<div class="grid">
			<div class="col">
				<span class="control-label">retrieved chunks</span>
				{#each data.chunks as chunk (chunk.start)}
					<button
						type="button"
						class="chunk-card"
						class:excluded={!included[chunk.start]}
						onclick={() => toggle(chunk.start)}
					>
						<div class="chunk-head">
							<span class="lit">chunk {chunk.start}</span>
							<span class="muted">score {chunk.score.toFixed(3)}</span>
						</div>
						<p class="chunk-text">{chunk.text}</p>
						<span class="toggle-hint muted"
							>{included[chunk.start]
								? 'in prompt — click to remove'
								: 'removed — click to add back'}</span
						>
					</button>
				{/each}
			</div>

			<div class="col">
				<span class="control-label">assembled prompt</span>
				<div class="prompt-block">
					{#if assembledChunks.length === 0}
						<p class="muted">no chunks in the prompt — the model gets no context.</p>
					{:else}
						{#each assembledChunks as chunk (chunk.start)}
							<p class="prompt-chunk">{chunk.text}</p>
						{/each}
					{/if}
				</div>
			</div>

			<div class="col">
				<span class="control-label">two answers</span>
				<div class="answer-card fail-card">
					<span class="answer-label fail">no context</span>
					<p class="answer-text">{data.no_context_answer}</p>
				</div>
				<div
					class="answer-card"
					class:pass-card={anyCitationIncluded}
					class:fail-card={!anyCitationIncluded}
				>
					<span
						class="answer-label"
						class:pass={anyCitationIncluded}
						class:fail={!anyCitationIncluded}
					>
						grounded
					</span>
					{#if anyCitationIncluded}
						<p class="answer-text">{data.grounded_answer}</p>
						<div class="citations">
							{#each data.citations as start (start)}
								<span class="citation-chip" class:dim={!included[start]}>chunk {start}</span>
							{/each}
						</div>
					{:else}
						<p class="answer-text muted">
							context removed — the cited chunk isn't in the prompt anymore, so there's nothing left
							to ground the answer in.
						</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.lab {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		height: 100%;
		overflow-y: auto;
	}

	.control-label {
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
	}

	.muted {
		color: var(--muted);
	}

	.overlay {
		font-family: var(--font-data);
		color: var(--muted);
	}

	.overlay.error {
		color: var(--fail);
	}

	.query-row {
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
		font-family: var(--font-data);
		font-size: 0.875rem;
	}

	.grid {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 1rem;
		flex: 1;
		min-height: 0;
	}

	.col {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		overflow-y: auto;
	}

	.chunk-card {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.625rem 0.75rem;
		text-align: left;
		cursor: pointer;
		font: inherit;
		color: inherit;
	}

	.chunk-card.excluded {
		opacity: 0.45;
	}

	.chunk-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		font-family: var(--font-data);
		font-size: 0.75rem;
	}

	.chunk-text {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		line-height: 1.45;
		white-space: pre-wrap;
	}

	.toggle-hint {
		font-family: var(--font-data);
		font-size: 0.6875rem;
	}

	.prompt-block {
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.prompt-chunk {
		font-family: var(--font-data);
		font-size: 0.75rem;
		line-height: 1.5;
		white-space: pre-wrap;
		padding: 0.5rem;
		border-left: 2px solid var(--signal);
		background: color-mix(in srgb, var(--signal) 12%, transparent);
	}

	.answer-card {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.75rem;
	}

	.answer-label {
		font-family: var(--font-data);
		font-size: 0.6875rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.answer-label.pass {
		color: var(--pass);
	}

	.answer-label.fail {
		color: var(--fail);
	}

	.answer-card.pass-card {
		border-color: var(--pass);
	}

	.answer-card.fail-card {
		border-color: var(--fail);
	}

	.answer-text {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		line-height: 1.5;
		white-space: pre-wrap;
	}

	.citations {
		display: flex;
		gap: 0.375rem;
		flex-wrap: wrap;
	}

	.citation-chip {
		font-family: var(--font-data);
		font-size: 0.6875rem;
		color: var(--pass);
		border: 1px solid var(--pass);
		border-radius: 999px;
		padding: 0.125rem 0.5rem;
	}

	.citation-chip.dim {
		color: var(--muted);
		border-color: var(--structure);
		text-decoration: line-through;
	}

	@media (max-width: 768px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
