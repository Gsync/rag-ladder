<script lang="ts">
	import { onMount } from 'svelte';
	import EmbeddingPlayground from '$lib/components/EmbeddingPlayground.svelte';
	import ChunkingLab from '$lib/components/ChunkingLab.svelte';
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

	onMount(() => {
		if (!rungState.active) rungState.active = 'vanilla';
	});

	$effect(() => {
		if (rungState.active === 'vanilla') {
			setGuidedPanel(vanillaModuleState.active === 'chunk' ? M2_GUIDED : M1_GUIDED);
		} else {
			resetGuidedPanel();
		}
	});
</script>

{#if rungState.active === 'vanilla'}
	{#if vanillaModuleState.active === 'chunk'}
		<ChunkingLab />
	{:else}
		<EmbeddingPlayground />
	{/if}
{/if}
