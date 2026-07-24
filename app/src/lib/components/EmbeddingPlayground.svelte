<script lang="ts">
	import { onMount } from 'svelte';
	import { extent, scaleLinear } from 'd3';
	import { base } from '$app/paths';
	import { queryState } from '$lib/stores/shell.svelte';
	import { loadNpy } from '$lib/npy';
	import { cosineSimilarity } from '$lib/cosine';
	import { indexCommunities, topCommunitiesBySize, type Community } from '$lib/communities';
	import { embed } from '$lib/embedder';

	const TOP_K = 8;
	const HOVER_RADIUS_PX = 16;
	const COMMUNITY_SLOTS = ['a', 'b'] as const;

	type Point = { id: string; name: string; x: number; y: number; communityId: string };
	type LegendEntry = { label: string; color: string };

	let canvasEl: HTMLCanvasElement;
	let width = $state(0);
	let height = $state(0);

	let datasetLoaded = $state(false);
	let modelLoading = $state(false);
	let loadError: string | null = $state(null);

	let points = $state<Point[]>([]);
	let litIds = $state<Set<string>>(new Set());
	let queryCentroid = $state<{ x: number; y: number } | null>(null);
	let hovered = $state<Point | null>(null);
	let hoveredScreen = $state<{ x: number; y: number } | null>(null);
	let legend = $state<LegendEntry[]>([]);

	// Set once after the initial fetch; read imperatively by draw()/hit-testing,
	// not part of the reactive dependency graph.
	let vectors: Float32Array | null = null;
	let dim = 0;
	let colorFor = new Map<string, string>();
	let communityLabels = new Map<string, string>();
	let otherColor = '#717b8b';
	let inkColor = '#0e1116';
	let signalColor = '#e8a13a';
	let queryColor = '#6e9bf2';
	let xScale = scaleLinear();
	let yScale = scaleLinear();
	let embedderReady = false;

	function cssVar(name: string): string {
		return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
	}

	onMount(async () => {
		try {
			const [projection, communities, embeddingsBuffer] = await Promise.all([
				fetch(`${base}/data/npm/projection.json`).then(
					(r) => r.json() as Promise<{ id: string; x: number; y: number }[]>
				),
				fetch(`${base}/data/npm/communities.json`).then((r) => r.json() as Promise<Community[]>),
				fetch(`${base}/data/npm/embeddings.npy`).then((r) => r.arrayBuffer())
			]);

			const loaded = loadNpy(embeddingsBuffer);
			vectors = loaded.data;
			dim = loaded.shape[1];

			inkColor = cssVar('--ink');
			signalColor = cssVar('--signal');
			queryColor = cssVar('--query');
			otherColor = cssVar('--community-other');

			const communityIndex = indexCommunities(communities);
			const topIds = topCommunitiesBySize(communities, COMMUNITY_SLOTS.length);
			communityLabels = new Map(communities.map((c) => [c.id, c.label]));

			colorFor = new Map(topIds.map((id, i) => [id, cssVar(`--community-${COMMUNITY_SLOTS[i]}`)]));
			legend = [
				...topIds.map((id) => ({
					label: communityLabels.get(id) ?? id,
					color: colorFor.get(id)!
				})),
				{ label: 'Other', color: otherColor }
			];

			points = projection.map((p) => ({
				id: p.id,
				name: p.id.replace(/^npm:/, ''),
				x: p.x,
				y: p.y,
				communityId: communityIndex.get(p.id) ?? ''
			}));

			datasetLoaded = true;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'failed to load dataset';
		}
	});

	function pointColor(p: Point): string {
		return litIds.has(p.id) ? signalColor : (colorFor.get(p.communityId) ?? otherColor);
	}

	function communityLabelFor(p: Point): string {
		return colorFor.has(p.communityId)
			? (communityLabels.get(p.communityId) ?? p.communityId)
			: 'Other';
	}

	function draw() {
		if (!canvasEl || points.length === 0 || width === 0 || height === 0) return;

		const dpr = window.devicePixelRatio || 1;
		canvasEl.width = width * dpr;
		canvasEl.height = height * dpr;
		canvasEl.style.width = `${width}px`;
		canvasEl.style.height = `${height}px`;
		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;
		ctx.scale(dpr, dpr);
		ctx.clearRect(0, 0, width, height);

		const pad = 24;
		const [xMin, xMax] = extent(points, (p) => p.x) as [number, number];
		const [yMin, yMax] = extent(points, (p) => p.y) as [number, number];
		xScale = scaleLinear()
			.domain([xMin, xMax])
			.range([pad, width - pad]);
		yScale = scaleLinear()
			.domain([yMin, yMax])
			.range([height - pad, pad]);

		for (const p of points) {
			const cx = xScale(p.x);
			const cy = yScale(p.y);
			const isLit = litIds.has(p.id);
			const r = isLit ? 6 : 4;

			// surface ring (marks-and-anatomy.md): keeps overlapping dots legible
			ctx.beginPath();
			ctx.arc(cx, cy, r + 2, 0, Math.PI * 2);
			ctx.fillStyle = inkColor;
			ctx.fill();

			ctx.beginPath();
			ctx.arc(cx, cy, r, 0, Math.PI * 2);
			ctx.fillStyle = pointColor(p);
			ctx.fill();
		}

		if (queryCentroid) {
			const cx = xScale(queryCentroid.x);
			const cy = yScale(queryCentroid.y);
			ctx.beginPath();
			ctx.arc(cx, cy, 9, 0, Math.PI * 2);
			ctx.strokeStyle = queryColor;
			ctx.lineWidth = 2;
			ctx.stroke();
		}
	}

	$effect(() => {
		// tracked deps: points, litIds, queryCentroid, width, height
		void points;
		void litIds;
		void queryCentroid;
		void width;
		void height;
		draw();
	});

	async function runQuery(text: string) {
		if (!text.trim() || !vectors || points.length === 0) return;
		modelLoading = !embedderReady;
		loadError = null;
		try {
			const qvec = await embed(text);
			embedderReady = true;
			modelLoading = false;

			const scored = points.map((p, i) => ({
				p,
				score: cosineSimilarity(qvec, vectors!.subarray(i * dim, i * dim + dim))
			}));
			scored.sort((a, b) => b.score - a.score);
			const top = scored.slice(0, TOP_K);

			litIds = new Set(top.map((t) => t.p.id));
			queryCentroid = {
				x: top.reduce((sum, t) => sum + t.p.x, 0) / top.length,
				y: top.reduce((sum, t) => sum + t.p.y, 0) / top.length
			};
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'search failed';
		} finally {
			modelLoading = false;
		}
	}

	$effect(() => {
		const text = queryState.text;
		if (datasetLoaded && text.trim()) runQuery(text);
	});

	function handlePointerMove(event: PointerEvent) {
		if (points.length === 0) return;
		const rect = canvasEl.getBoundingClientRect();
		const mx = event.clientX - rect.left;
		const my = event.clientY - rect.top;

		let nearest: Point | null = null;
		let nearestDist = Infinity;
		for (const p of points) {
			const dx = xScale(p.x) - mx;
			const dy = yScale(p.y) - my;
			const dist = Math.hypot(dx, dy);
			if (dist < nearestDist) {
				nearestDist = dist;
				nearest = p;
			}
		}

		if (nearest && nearestDist <= HOVER_RADIUS_PX) {
			hovered = nearest;
			hoveredScreen = { x: mx, y: my };
		} else {
			hovered = null;
			hoveredScreen = null;
		}
	}

	function handlePointerLeave() {
		hovered = null;
		hoveredScreen = null;
	}
</script>

<div
	class="playground"
	bind:clientWidth={width}
	bind:clientHeight={height}
	role="img"
	aria-label="Scatter plot of npm packages positioned by embedding similarity"
>
	<canvas bind:this={canvasEl} onpointermove={handlePointerMove} onpointerleave={handlePointerLeave}
	></canvas>

	{#if !datasetLoaded && !loadError}
		<p class="overlay">loading dataset…</p>
	{:else if loadError}
		<p class="overlay error">{loadError}</p>
	{:else if modelLoading}
		<p class="overlay">loading the embedder…</p>
	{:else if !queryState.text.trim()}
		<p class="overlay">Ask about a package…</p>
	{/if}

	{#if hovered && hoveredScreen}
		<div class="tooltip" style:left="{hoveredScreen.x + 12}px" style:top="{hoveredScreen.y + 12}px">
			<span class="lit-query name">{hovered.name}</span>
			<span class="muted community">{communityLabelFor(hovered)}</span>
		</div>
	{/if}

	{#if legend.length > 0}
		<div class="legend">
			{#each legend as entry (entry.label)}
				<div class="legend-item">
					<span class="swatch" style:background={entry.color}></span>
					<span class="muted">{entry.label}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.playground {
		position: relative;
		width: 100%;
		height: 100%;
		min-height: 24rem;
	}

	canvas {
		display: block;
		width: 100%;
		height: 100%;
	}

	.overlay {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-family: var(--font-data);
		color: var(--muted);
		pointer-events: none;
	}

	.overlay.error {
		color: var(--fail);
	}

	.muted {
		color: var(--muted);
	}

	.tooltip {
		position: absolute;
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.375rem 0.5rem;
		font-family: var(--font-data);
		font-size: 0.75rem;
		pointer-events: none;
		white-space: nowrap;
	}

	.tooltip .name {
		font-weight: 600;
	}

	.legend {
		position: absolute;
		bottom: 0.75rem;
		left: 0.75rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.375rem 0.625rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-family: var(--font-data);
		font-size: 0.75rem;
	}

	.swatch {
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		flex-shrink: 0;
	}
</style>
