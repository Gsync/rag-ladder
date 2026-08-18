<script lang="ts">
	import { onMount } from 'svelte';
	import { extent, scaleLinear } from 'd3';
	import { base } from '$app/paths';
	import { rungState } from '$lib/stores/shell.svelte';

	type Point = { id: string; name: string; x: number; y: number };
	type Step = { kind: string; tool: string | null; touched_ids: string[] };
	type Trace = { question: string; mode: string; steps: Step[]; answer: string };

	let canvasEl: HTMLCanvasElement;
	let width = $state(0);
	let height = $state(0);

	let loaded = $state(false);
	let loadError: string | null = $state(null);

	let points: Point[] = [];
	let debugId = 'npm:debug';
	let touchedIds = $state<Set<string>>(new Set());
	let answer = $state('');

	let structureColor = '#3a4351';
	let signalColor = '#e8a13a';
	let queryColor = '#6e9bf2';
	let xScale = scaleLinear();
	let yScale = scaleLinear();

	function cssVar(name: string): string {
		return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
	}

	onMount(async () => {
		try {
			const [projection, demos] = await Promise.all([
				fetch(`${base}/data/npm/projection.json`).then(
					(r) => r.json() as Promise<{ id: string; x: number; y: number }[]>
				),
				fetch(`${base}/data/npm/demos.json`).then((r) => r.json() as Promise<Trace[]>)
			]);

			structureColor = cssVar('--structure');
			signalColor = cssVar('--signal');
			queryColor = cssVar('--query');

			points = projection.map((p) => ({
				id: p.id,
				name: p.id.replace(/^npm:/, ''),
				x: p.x,
				y: p.y
			}));

			const trace = demos.find(
				(t) => t.mode === 'vanilla' && t.question === 'what breaks if debug disappears?'
			);
			if (!trace) throw new Error('vanilla debug trace not found in demos.json');

			const searchStep = trace.steps.find((s) => s.tool === 'vector_search');
			touchedIds = new Set(searchStep?.touched_ids ?? []);
			answer = trace.answer;

			loaded = true;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'failed to load demo';
		}
	});

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
			const isTouched = touchedIds.has(p.id);
			const isDebug = p.id === debugId;
			const cx = xScale(p.x);
			const cy = yScale(p.y);
			const r = isTouched || isDebug ? 5 : 3;

			ctx.beginPath();
			ctx.arc(cx, cy, r, 0, Math.PI * 2);
			ctx.fillStyle = isTouched ? signalColor : structureColor;
			ctx.globalAlpha = isTouched || isDebug ? 1 : 0.5;
			ctx.fill();
			ctx.globalAlpha = 1;

			if (isDebug) {
				ctx.beginPath();
				ctx.arc(cx, cy, r + 4, 0, Math.PI * 2);
				ctx.strokeStyle = queryColor;
				ctx.lineWidth = 2;
				ctx.stroke();
			}
		}
	}

	$effect(() => {
		void loaded;
		void width;
		void height;
		draw();
	});
</script>

<div
	class="breaks"
	bind:clientWidth={width}
	bind:clientHeight={height}
	role="img"
	aria-label="Scatter plot showing vanilla search retrieving semantically-similar but unrelated packages for the debug question"
>
	<canvas bind:this={canvasEl}></canvas>

	{#if loadError}
		<p class="overlay error">{loadError}</p>
	{:else if !loaded}
		<p class="overlay">loading…</p>
	{:else}
		<div class="insufficient">
			<span class="fail-label">✕ insufficient</span>
			<p class="insufficient-text">
				These packages sound related — they don't <em>depend on</em>
				<span class="lit-query">debug</span>.
			</p>
		</div>

		<div class="answer-panel">
			<span class="control-label">what vanilla answered</span>
			<p class="answer-text">{answer}</p>
			<button type="button" class="cta" onclick={() => (rungState.active = 'graph')}>
				Climb to the graph ▸
			</button>
		</div>
	{/if}
</div>

<style>
	.breaks {
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
	}

	.overlay.error {
		color: var(--fail);
	}

	.control-label {
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
	}

	.insufficient {
		position: absolute;
		top: 0.75rem;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		background: var(--surface);
		border: 1px solid var(--fail);
		border-radius: 0.25rem;
		padding: 0.5rem 0.875rem;
		text-align: center;
		max-width: 26rem;
	}

	.fail-label {
		font-family: var(--font-data);
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--fail);
	}

	.insufficient-text {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		color: var(--text);
	}

	.answer-panel {
		position: absolute;
		left: 0.75rem;
		right: 0.75rem;
		bottom: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		background: var(--surface);
		border: 1px solid var(--fail);
		border-radius: 0.25rem;
		padding: 0.75rem;
	}

	.answer-text {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		line-height: 1.5;
		white-space: pre-wrap;
		max-height: 6rem;
		overflow-y: auto;
	}

	.cta {
		align-self: flex-end;
		font-family: var(--font-data);
		font-size: 0.8125rem;
		color: var(--signal);
		background: transparent;
		border: 1px solid var(--signal);
		border-radius: 0.25rem;
		padding: 0.375rem 0.75rem;
		cursor: pointer;
	}

	.cta:hover {
		background: color-mix(in srgb, var(--signal) 12%, transparent);
	}
</style>
