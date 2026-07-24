<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';

	onMount(async () => {
		const [chunks, projection, graph] = await Promise.all([
			fetch(`${base}/data/npm/chunks.json`).then((r) => r.json()),
			fetch(`${base}/data/npm/projection.json`).then((r) => r.json()),
			fetch(`${base}/data/npm/graph.json`).then((r) => r.json())
		]);

		console.log(
			`${chunks.length.toLocaleString()} chunks, ${projection.length.toLocaleString()} points, ${graph.edges.length.toLocaleString()} edges`
		);
	});
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
