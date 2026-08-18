<script lang="ts">
	import { onMount } from 'svelte';
	import EmbeddingPlayground from '$lib/components/EmbeddingPlayground.svelte';
	import ChunkingLab from '$lib/components/ChunkingLab.svelte';
	import GroundingDemo from '$lib/components/GroundingDemo.svelte';
	import VanillaBreaks from '$lib/components/VanillaBreaks.svelte';
	import {
		rungState,
		vanillaModuleState,
		queryState,
		DEMO_QUESTIONS,
		setGuidedPanel,
		resetGuidedPanel
	} from '$lib/stores/shell.svelte';

	const M1_GUIDED = {
		whatThisShows: 'Every package is placed by meaning, not name. Nearby = similar.',
		tryThis: 'Type "http client".',
		aha: "You searched with zero keywords — that's an embedding."
	};

	const M2_GUIDED = {
		whatThisShows: "RAG doesn't read whole docs — it reads chunks.",
		tryThis: 'Shrink the chunk size and watch the answer degrade.',
		aha: 'Same data, worse retrieval — chunking is a decision, not a default.'
	};

	const M3_GUIDED = {
		whatThisShows:
			"Retrieved chunks don't just get read — they get typed straight into the prompt.",
		tryThis:
			'Remove the cited chunk from the prompt and watch the grounded answer lose its source.',
		aha: 'The model didn\'t "know" this — it was handed the passage. Remove it and watch it guess.'
	};

	const M4_GUIDED = {
		whatThisShows:
			'Vanilla search finds packages that sound related — not packages that depend on debug.',
		tryThis: 'Read the answer vanilla gave, then climb to the graph to see the real dependents.',
		aha: "The answer isn't about similar packages — it's about connected ones. Similarity can't see connections. That's the wall."
	};

	const BREAKS_QUESTION = DEMO_QUESTIONS[1];

	onMount(() => {
		if (!rungState.active) rungState.active = 'vanilla';
	});

	$effect(() => {
		if (rungState.active === 'vanilla') {
			if (queryState.text === BREAKS_QUESTION) setGuidedPanel(M4_GUIDED);
			else if (vanillaModuleState.active === 'chunk') setGuidedPanel(M2_GUIDED);
			else if (vanillaModuleState.active === 'ground') setGuidedPanel(M3_GUIDED);
			else setGuidedPanel(M1_GUIDED);
		} else {
			resetGuidedPanel();
		}
	});
</script>

{#if rungState.active === 'vanilla'}
	{#if queryState.text === BREAKS_QUESTION}
		<VanillaBreaks />
	{:else if vanillaModuleState.active === 'chunk'}
		<ChunkingLab />
	{:else if vanillaModuleState.active === 'ground'}
		<GroundingDemo />
	{:else}
		<EmbeddingPlayground />
	{/if}
{/if}
