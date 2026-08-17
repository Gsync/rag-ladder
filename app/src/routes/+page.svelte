<script lang="ts">
	import { onMount } from 'svelte';
	import EmbeddingPlayground from '$lib/components/EmbeddingPlayground.svelte';
	import ChunkingLab from '$lib/components/ChunkingLab.svelte';
	import GroundingDemo from '$lib/components/GroundingDemo.svelte';
	import {
		rungState,
		vanillaModuleState,
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

	onMount(() => {
		if (!rungState.active) rungState.active = 'vanilla';
	});

	$effect(() => {
		if (rungState.active === 'vanilla') {
			if (vanillaModuleState.active === 'chunk') setGuidedPanel(M2_GUIDED);
			else if (vanillaModuleState.active === 'ground') setGuidedPanel(M3_GUIDED);
			else setGuidedPanel(M1_GUIDED);
		} else {
			resetGuidedPanel();
		}
	});
</script>

{#if rungState.active === 'vanilla'}
	{#if vanillaModuleState.active === 'chunk'}
		<ChunkingLab />
	{:else if vanillaModuleState.active === 'ground'}
		<GroundingDemo />
	{:else}
		<EmbeddingPlayground />
	{/if}
{/if}
