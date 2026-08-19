<script lang="ts">
	import { onMount } from 'svelte';
	import Graph from 'graphology';
	import type Sigma from 'sigma';
	import { base } from '$app/paths';
	import { queryState, DEMO_QUESTIONS } from '$lib/stores/shell.svelte';
	import { indexCommunities, topCommunitiesBySize, type Community } from '$lib/communities';
	import Stepper from './Stepper.svelte';

	const DEBUG_ID = 'npm:debug';
	const BREAKS_QUESTION = DEMO_QUESTIONS[1];
	const THEMATIC_QUESTION = DEMO_QUESTIONS[2];
	const COMMUNITY_SLOTS = ['a', 'b'] as const;

	type RawNode = { id: string; label: string; x: number; y: number };
	type RawEdge = { src: string; dst: string };
	type ChunkMeta = { id: string; metadata: { license?: string; version?: string } };

	let containerEl: HTMLDivElement;
	let sigmaInstance: Sigma | null = null;

	let loaded = $state(false);
	let loadError: string | null = $state(null);

	let communityMode = $state(false);
	let hopIndex = $state(0);
	let selectedId: string | null = $state(null);
	let hoveredId: string | null = $state(null);
	let hoverPos = $state<{ x: number; y: number } | null>(null);
	let hopGroupsLen = $state(1);

	let hopGroups: string[][] = [[DEBUG_ID]];
	let nodeById = new Map<string, RawNode>();
	let adjOut = new Map<string, string[]>(); // package -> its dependencies
	let adjIn = new Map<string, string[]>(); // package -> its dependents
	let chunkById = new Map<string, ChunkMeta>();
	let communityIndex = new Map<string, string>();
	let communityById = new Map<string, Community>();
	let colorFor = new Map<string, string>();

	let structureColor = '#3a4351';
	let signalColor = '#e8a13a';
	let queryColor = '#6e9bf2';
	let otherColor = '#717b8b';
	let textColor = '#e6eaf0';

	function cssVar(name: string): string {
		return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
	}

	function bareName(id: string): string {
		return id.replace(/^npm:/, '');
	}

	function computeHops(rootId: string, reverseAdj: Map<string, string[]>): string[][] {
		const groups: string[][] = [[rootId]];
		const seen: Record<string, true> = { [rootId]: true };
		let frontier = [rootId];
		while (frontier.length > 0) {
			const next: string[] = [];
			for (const id of frontier) {
				for (const dependent of reverseAdj.get(id) ?? []) {
					if (!seen[dependent]) {
						seen[dependent] = true;
						next.push(dependent);
					}
				}
			}
			if (next.length === 0) break;
			groups.push(next);
			frontier = next;
		}
		return groups;
	}

	const isTraversing = $derived(queryState.text === BREAKS_QUESTION);
	const litIds = $derived.by(() => {
		if (!isTraversing) return new Set<string>();
		const ids: string[] = [];
		for (let i = 0; i <= hopIndex && i < hopGroups.length; i++) ids.push(...hopGroups[i]);
		return new Set(ids);
	});
	const notFoundQuery = $derived.by(() => {
		if (!loaded) return null;
		const text = queryState.text.trim();
		if (!text || text === BREAKS_QUESTION || text === THEMATIC_QUESTION) return null;
		const bare = text.toLowerCase();
		const match = [...nodeById.keys()].find((id) => bareName(id).toLowerCase() === bare);
		return match ? null : text;
	});
	const selectedNode = $derived(selectedId ? (nodeById.get(selectedId) ?? null) : null);
	const selectedDeps = $derived(selectedId ? (adjOut.get(selectedId) ?? []) : []);
	const selectedDependents = $derived(selectedId ? (adjIn.get(selectedId) ?? []) : []);
	const selectedMeta = $derived(selectedId ? (chunkById.get(selectedId) ?? null) : null);
	const hoveredCommunity = $derived.by(() => {
		if (!communityMode || !hoveredId) return null;
		const id = communityIndex.get(hoveredId);
		return id ? (communityById.get(id) ?? null) : null;
	});

	function nodeColorAndSize(node: string): { color: string; size: number } {
		if (communityMode) {
			return { color: colorFor.get(communityIndex.get(node) ?? '') ?? otherColor, size: 3 };
		}
		if (isTraversing) {
			if (node === DEBUG_ID) return { color: queryColor, size: 8 };
			if (litIds.has(node)) return { color: signalColor, size: 5 };
			return { color: structureColor, size: 2 };
		}
		if (selectedId === node) return { color: queryColor, size: 7 };
		return { color: structureColor, size: 3 };
	}

	onMount(async () => {
		try {
			const [{ default: SigmaCtor }, graphData, communities, chunks] = await Promise.all([
				import('sigma'),
				fetch(`${base}/data/npm/graph.json`).then(
					(r) => r.json() as Promise<{ nodes: RawNode[]; edges: RawEdge[] }>
				),
				fetch(`${base}/data/npm/communities.json`).then((r) => r.json() as Promise<Community[]>),
				fetch(`${base}/data/npm/chunks.json`).then((r) => r.json() as Promise<ChunkMeta[]>)
			]);

			structureColor = cssVar('--structure');
			signalColor = cssVar('--signal');
			queryColor = cssVar('--query');
			otherColor = cssVar('--community-other');
			textColor = cssVar('--text');

			nodeById = new Map(graphData.nodes.map((n) => [n.id, n]));

			const outEdges: Record<string, string[]> = {};
			const inEdges: Record<string, string[]> = {};
			for (const e of graphData.edges) {
				(outEdges[e.src] ??= []).push(e.dst);
				(inEdges[e.dst] ??= []).push(e.src);
			}
			adjOut = new Map(Object.entries(outEdges));
			adjIn = new Map(Object.entries(inEdges));

			chunkById = new Map(chunks.map((c) => [c.id, c]));

			communityIndex = indexCommunities(communities);
			communityById = new Map(communities.map((c) => [c.id, c]));
			const topIds = topCommunitiesBySize(communities, COMMUNITY_SLOTS.length);
			colorFor = new Map(topIds.map((id, i) => [id, cssVar(`--community-${COMMUNITY_SLOTS[i]}`)]));

			hopGroups = computeHops(DEBUG_ID, adjIn);
			hopGroupsLen = hopGroups.length;

			const g = new Graph({ type: 'directed' });
			for (const n of graphData.nodes) {
				g.addNode(n.id, { x: n.x, y: n.y, label: bareName(n.id), size: 3, color: structureColor });
			}
			for (const e of graphData.edges) {
				if (!g.hasEdge(e.src, e.dst)) g.addEdge(e.src, e.dst, { size: 1, color: structureColor });
			}

			sigmaInstance = new SigmaCtor(g, containerEl, {
				renderLabels: true,
				labelRenderedSizeThreshold: Infinity,
				defaultNodeColor: structureColor,
				defaultEdgeColor: structureColor,
				labelColor: { color: textColor },
				nodeReducer: (node, data) => {
					const { color, size } = nodeColorAndSize(node);
					const showLabel = node === hoveredId || node === selectedId || node === DEBUG_ID;
					return {
						...data,
						color,
						size,
						label: showLabel ? data.label : null,
						forceLabel: showLabel
					};
				},
				edgeReducer: (edge, data) => {
					if (isTraversing && g) {
						const src = g.source(edge);
						const dst = g.target(edge);
						if (litIds.has(src) && (dst === DEBUG_ID || litIds.has(dst))) {
							return { ...data, hidden: false, color: signalColor, size: 2 };
						}
					}
					return { ...data, hidden: true };
				}
			});

			sigmaInstance.on('clickNode', ({ node }) => {
				selectedId = node;
			});
			sigmaInstance.on('clickStage', () => {
				selectedId = null;
			});
			sigmaInstance.on('enterNode', ({ node, event }) => {
				hoveredId = node;
				hoverPos = { x: event.x, y: event.y };
			});
			sigmaInstance.on('leaveNode', () => {
				hoveredId = null;
				hoverPos = null;
			});

			loaded = true;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'failed to load graph';
		}
	});

	$effect(() => {
		if (isTraversing) hopIndex = 0;
	});

	$effect(() => {
		if (queryState.text === THEMATIC_QUESTION) communityMode = true;
	});

	$effect(() => {
		if (!loaded) return;
		const text = queryState.text.trim();
		if (!text || text === BREAKS_QUESTION || text === THEMATIC_QUESTION) return;
		const bare = text.toLowerCase();
		const match = [...nodeById.keys()].find((id) => bareName(id).toLowerCase() === bare);
		if (match) selectedId = match;
	});

	$effect(() => {
		void communityMode;
		void isTraversing;
		void hopIndex;
		void selectedId;
		void hoveredId;
		sigmaInstance?.refresh();
	});
</script>

<div class="explorer">
	<div class="canvas-wrap" bind:this={containerEl}></div>

	{#if loadError}
		<p class="overlay error">{loadError}</p>
	{:else if !loaded}
		<p class="overlay">loading…</p>
	{/if}

	{#if loaded}
		<button
			type="button"
			class="community-toggle"
			class:active={communityMode}
			onclick={() => (communityMode = !communityMode)}
		>
			{communityMode ? '● color by community' : '○ color by community'}
		</button>

		{#if notFoundQuery}
			<p class="empty-search">no package named "{notFoundQuery}" in this slice</p>
		{/if}

		{#if hoveredId && !communityMode}
			<div class="tooltip" style:left="{hoverPos?.x ?? 0}px" style:top="{hoverPos?.y ?? 0}px">
				{bareName(hoveredId)}
			</div>
		{/if}

		{#if hoveredCommunity}
			<div
				class="tooltip community"
				style:left="{hoverPos?.x ?? 0}px"
				style:top="{hoverPos?.y ?? 0}px"
			>
				<strong>{hoveredCommunity.label}</strong>
				{#if hoveredCommunity.summary}
					<p>{hoveredCommunity.summary}</p>
				{/if}
			</div>
		{/if}

		{#if isTraversing}
			<div class="traversal-panel">
				<span class="control-label">reverse-dependency walk from debug</span>
				<Stepper
					index={hopIndex}
					total={hopGroupsLen}
					onPrev={() => (hopIndex = Math.max(0, hopIndex - 1))}
					onNext={() => (hopIndex = Math.min(hopGroupsLen - 1, hopIndex + 1))}
				/>
				<ul class="hit-list">
					{#each [...litIds].filter((id) => id !== DEBUG_ID) as id (id)}
						<li>{bareName(id)}</li>
					{/each}
				</ul>
			</div>
		{/if}

		{#if selectedId && selectedNode && !isTraversing}
			<div class="inspect-panel">
				<button type="button" class="close" onclick={() => (selectedId = null)}>✕</button>
				<span class="control-label">inspect</span>
				<h3>{bareName(selectedId)}</h3>
				{#if selectedMeta?.metadata.license}
					<p class="meta-line">license: {selectedMeta.metadata.license}</p>
				{/if}
				{#if selectedMeta?.metadata.version}
					<p class="meta-line">version: {selectedMeta.metadata.version}</p>
				{/if}
				<div class="rel-lists">
					<div>
						<span class="rel-label">depends on ({selectedDeps.length})</span>
						<ul>
							{#each selectedDeps as id (id)}
								<li>{bareName(id)}</li>
							{/each}
						</ul>
					</div>
					<div>
						<span class="rel-label">depended on by ({selectedDependents.length})</span>
						<ul>
							{#each selectedDependents as id (id)}
								<li>{bareName(id)}</li>
							{/each}
						</ul>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.explorer {
		position: relative;
		width: 100%;
		height: 100%;
		min-height: 24rem;
	}

	.canvas-wrap {
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

	.community-toggle {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 999px;
		padding: 0.375rem 0.75rem;
		cursor: pointer;
	}

	.community-toggle.active {
		color: var(--community-a);
		border-color: var(--community-a);
	}

	.empty-search {
		position: absolute;
		top: 0.75rem;
		left: 50%;
		transform: translateX(-50%);
		font-family: var(--font-data);
		font-size: 0.8125rem;
		color: var(--muted);
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.375rem 0.75rem;
	}

	.tooltip {
		position: absolute;
		transform: translate(0.75rem, -0.75rem);
		pointer-events: none;
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--text);
		background: var(--surface);
		border: 1px solid var(--structure);
		border-radius: 0.25rem;
		padding: 0.25rem 0.5rem;
		max-width: 16rem;
	}

	.tooltip.community strong {
		color: var(--community-a);
	}

	.tooltip.community p {
		margin: 0.25rem 0 0;
		font-family: var(--font-body);
		color: var(--muted);
	}

	.traversal-panel {
		position: absolute;
		left: 0.75rem;
		bottom: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		background: var(--surface);
		border: 1px solid var(--signal);
		border-radius: 0.25rem;
		padding: 0.75rem;
		max-width: 20rem;
	}

	.hit-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 0.5rem;
		list-style: none;
		margin: 0;
		padding: 0;
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--signal);
		max-height: 6rem;
		overflow-y: auto;
	}

	.inspect-panel {
		position: absolute;
		right: 0.75rem;
		bottom: 0.75rem;
		width: 16rem;
		max-height: 20rem;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		background: var(--surface);
		border: 1px solid var(--query);
		border-radius: 0.25rem;
		padding: 0.75rem;
	}

	.close {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		background: transparent;
		border: none;
		color: var(--muted);
		cursor: pointer;
	}

	.inspect-panel h3 {
		margin: 0;
		font-family: var(--font-header);
		font-size: 1rem;
		color: var(--text);
	}

	.meta-line {
		margin: 0;
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--muted);
	}

	.rel-lists {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.rel-label {
		font-family: var(--font-data);
		font-size: 0.6875rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--muted);
	}

	.rel-lists ul {
		list-style: none;
		margin: 0.25rem 0 0;
		padding: 0;
		font-family: var(--font-data);
		font-size: 0.75rem;
		color: var(--text);
	}
</style>
