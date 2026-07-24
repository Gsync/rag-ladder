<script lang="ts">
	import { onMount } from 'svelte';
	import EmbeddingPlayground from '$lib/components/EmbeddingPlayground.svelte';
	import { rungState, setGuidedPanel, resetGuidedPanel } from '$lib/stores/shell.svelte';

	const M1_GUIDED = {
		whatThisShows: 'Every package is placed by meaning, not name. Nearby = similar.',
		tryThis: 'Type "http client".',
		aha: "You searched with zero keywords — that's an embedding."
	};

	onMount(() => {
		if (!rungState.active) rungState.active = 'vanilla';
	});

	$effect(() => {
		if (rungState.active === 'vanilla') {
			setGuidedPanel(M1_GUIDED);
		} else {
			resetGuidedPanel();
		}
	});
</script>

{#if rungState.active === 'vanilla'}
	<EmbeddingPlayground />
{/if}
