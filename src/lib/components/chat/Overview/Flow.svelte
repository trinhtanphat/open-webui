<script>
	import { browser } from '$app/environment';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	import { theme } from '$lib/stores';
	import {
		Background,
		Controls,
		SvelteFlow,
		BackgroundVariant,
		ControlButton,
		MiniMap,
		SelectionMode
	} from '@xyflow/svelte';
	import AlignVertical from '$lib/components/icons/AlignVertical.svelte';
	import AlignHorizontal from '$lib/components/icons/AlignHorizontal.svelte';
	import CursorArrowRays from '$lib/components/icons/CursorArrowRays.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Reset from '$lib/components/icons/Reset.svelte';

	export let nodes;
	export let nodeTypes;
	export let edges;
	export let setLayoutDirection;
	export let resetLayout = () => {};

	let editMode = false;
	let miniMapMode = false;

	const colorMode = () => {
		if ($theme?.includes('dark')) return 'dark';
		if (!browser) return 'light';
		if ($theme === 'system') {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
	};
</script>

<SvelteFlow
	{nodes}
	{nodeTypes}
	{edges}
	fitView
	minZoom={0.001}
	maxZoom={2.2}
	colorMode={colorMode()}
	nodesConnectable={false}
	nodesDraggable={editMode}
	elementsSelectable={true}
	selectionOnDrag={editMode}
	selectionMode={SelectionMode.Partial}
	panOnDrag={!editMode}
	on:nodeclick={(e) => dispatch('nodeclick', e.detail)}
	oninit={() => {
		console.log('Flow initialized');
	}}
>
	<Controls showZoom={true} showFitView={true} showLock={false} fitViewOptions={{ padding: 0.2 }}>
		<ControlButton on:click={() => setLayoutDirection('vertical')} title="Vertical Layout">
			<AlignVertical className="size-4" />
		</ControlButton>
		<ControlButton on:click={() => setLayoutDirection('horizontal')} title="Horizontal Layout">
			<AlignHorizontal className="size-4" />
		</ControlButton>
		<ControlButton
			on:click={() => (editMode = !editMode)}
			title={editMode ? 'Lock Layout' : 'Edit Layout'}
			aria-pressed={editMode}
		>
			{#if editMode}
				<CursorArrowRays className="size-4" />
			{:else}
				<LockClosed className="size-4" />
			{/if}
		</ControlButton>
		<ControlButton
			on:click={() => (miniMapMode = !miniMapMode)}
			title="Mini Map"
			aria-pressed={miniMapMode}
		>
			<AlignHorizontal className="size-4" />
		</ControlButton>
		<ControlButton on:click={resetLayout} title="Reset Layout">
			<Reset className="size-4" />
		</ControlButton>
	</Controls>
	{#if miniMapMode}
		<MiniMap
			position="bottom-right"
			pannable
			zoomable
			nodeBorderRadius={8}
			nodeColor="var(--primary, #3b82f6)"
			nodeStrokeColor="var(--border, rgba(148, 163, 184, 0.35))"
		/>
	{/if}
	<Background variant={BackgroundVariant.Dots} />
</SvelteFlow>

<style>
	:global(.svelte-flow__controls-button[aria-pressed='true']) {
		background: var(--primary-dim, rgba(59, 130, 246, 0.14)) !important;
		color: var(--primary, #3b82f6) !important;
	}
</style>
