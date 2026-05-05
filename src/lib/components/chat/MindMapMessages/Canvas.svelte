<script lang="ts">
	import { browser } from '$app/environment';
	import { createEventDispatcher, getContext, onDestroy, onMount, tick } from 'svelte';
	import { writable } from 'svelte/store';
	import dagre from 'dagre';
	import {
		Background,
		BackgroundVariant,
		ControlButton,
		Controls,
		SvelteFlow,
		useNodesInitialized,
		useSvelteFlow
	} from '@xyflow/svelte';

	import { models, theme, user } from '$lib/stores';
	import AlignHorizontal from '$lib/components/icons/AlignHorizontal.svelte';
	import AlignVertical from '$lib/components/icons/AlignVertical.svelte';
	import ChatNode from './ChatNode.svelte';

	import '@xyflow/svelte/dist/style.css';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	export let history: any = { messages: {}, currentId: null };
	export let onNodeSelect: (messageId: string) => void | Promise<void> = (_messageId) => {};

	const nodeWidth = 300;
	const nodeHeight = 124;

	const nodes = writable<any[]>([]);
	const edges = writable<any[]>([]);
	const nodeTypes = { chat: ChatNode };

	const { fitView } = useSvelteFlow();
	const nodesInitialized = useNodesInitialized();

	let layoutDirection: 'TB' | 'LR' = 'TB';
	let pendingDraw: number | null = null;
	let lastFocusKey = '';
	let messageCount = 0;

	const getMessages = () => history?.messages ?? {};

	const sortRootIds = (ids: string[], messages: Record<string, any>) => {
		return [...ids].sort((left, right) => {
			const leftTime = messages[left]?.timestamp ?? 0;
			const rightTime = messages[right]?.timestamp ?? 0;

			if (leftTime === rightTime) {
				return left.localeCompare(right);
			}

			return leftTime - rightTime;
		});
	};

	const getOrderedMessageIds = (messages: Record<string, any>) => {
		const visited = new Set<string>();
		const orderedIds: string[] = [];

		const visit = (id: string) => {
			if (!id || visited.has(id) || !messages[id]) {
				return;
			}

			visited.add(id);
			orderedIds.push(id);

			for (const childId of messages[id]?.childrenIds ?? []) {
				visit(childId);
			}
		};

		const rootIds = Object.values(messages)
			.filter((message: any) => !message?.parentId || !messages[message.parentId])
			.map((message: any) => message.id);

		for (const id of sortRootIds(rootIds, messages)) {
			visit(id);
		}

		for (const id of Object.keys(messages)) {
			visit(id);
		}

		return orderedIds;
	};

	const getActiveMessageIds = (messages: Record<string, any>, currentId: string | null) => {
		const activeIds = new Set<string>();
		const visited = new Set<string>();
		let messageId = currentId;

		while (messageId && messages[messageId] && !visited.has(messageId)) {
			visited.add(messageId);
			activeIds.add(messageId);
			messageId = messages[messageId].parentId;
		}

		return activeIds;
	};

	const colorMode = () => {
		if ($theme?.includes('dark')) {
			return 'dark';
		}

		if (!browser) {
			return 'light';
		}

		if ($theme === 'system') {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}

		return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
	};

	const drawFlow = () => {
		const messages = getMessages();
		const orderedIds = getOrderedMessageIds(messages);
		const activeIds = getActiveMessageIds(messages, history?.currentId ?? null);
		const graph = new dagre.graphlib.Graph();

		graph.setGraph({
			rankdir: layoutDirection,
			nodesep: layoutDirection === 'TB' ? 48 : 64,
			ranksep: layoutDirection === 'TB' ? 90 : 128,
			marginx: 48,
			marginy: 48
		});
		graph.setDefaultEdgeLabel(() => ({}));

		for (const id of orderedIds) {
			graph.setNode(id, { width: nodeWidth, height: nodeHeight });
		}

		for (const id of orderedIds) {
			const parentId = messages[id]?.parentId;

			if (parentId && messages[parentId]) {
				graph.setEdge(parentId, id);
			}
		}

		dagre.layout(graph);

		nodes.set(
			orderedIds.map((id) => {
				const message = messages[id];
				const position = graph.node(id) ?? { x: 0, y: 0 };

				return {
					id,
					type: 'chat',
					position: {
						x: position.x - nodeWidth / 2,
						y: position.y - nodeHeight / 2
					},
					data: {
						message,
						model: $models.find((model) => model.id === message?.model),
						user: $user,
						direction: layoutDirection,
						isActive: history?.currentId === id,
						isOnActiveBranch: activeIds.has(id),
						childCount: message?.childrenIds?.length ?? 0
					},
					draggable: false,
					selectable: true
				};
			})
		);

		edges.set(
			orderedIds
				.map((id) => {
					const parentId = messages[id]?.parentId;

					if (!parentId || !messages[parentId]) {
						return null;
					}

					const isActiveEdge = activeIds.has(parentId) && activeIds.has(id);

					return {
						id: `${parentId}-${id}`,
						source: parentId,
						target: id,
						type: 'smoothstep',
						selectable: false,
						animated: isActiveEdge,
						class: isActiveEdge ? 'mindmap-edge-active' : 'mindmap-edge'
					};
				})
				.filter(Boolean)
		);
	};

	const scheduleDraw = () => {
		if (!browser) {
			drawFlow();
			return;
		}

		if (pendingDraw !== null) {
			return;
		}

		pendingDraw = requestAnimationFrame(() => {
			pendingDraw = null;
			drawFlow();
		});
	};

	const focusCurrentNode = async () => {
		if (!browser || !history?.currentId) {
			return;
		}

		await tick();

		try {
			await fitView({ nodes: [{ id: history.currentId }], padding: 0.24 });
		} catch (error) {
			console.debug('Unable to focus mind map node', error);
		}
	};

	const setLayoutDirection = (direction: 'TB' | 'LR') => {
		layoutDirection = direction;
		scheduleDraw();
		lastFocusKey = '';
	};

	const handleNodeClick = async (event: CustomEvent) => {
		const nodeId = event.detail?.node?.id;

		if (!nodeId) {
			return;
		}

		dispatch('select', nodeId);
		await onNodeSelect(nodeId);
		lastFocusKey = '';
	};

	$: messageCount = Object.keys(history?.messages ?? {}).length;
	$: if (history) {
		scheduleDraw();
	}
	$: if (browser && history?.currentId && $nodes.length > 0) {
		const focusKey = `${history.currentId}:${layoutDirection}:${$nodes.length}`;

		if (focusKey !== lastFocusKey) {
			lastFocusKey = focusKey;
			focusCurrentNode();
		}
	}

	onMount(() => {
		scheduleDraw();

		const unsubscribeNodesInitialized = nodesInitialized.subscribe((initialized) => {
			if (initialized) {
				focusCurrentNode();
			}
		});

		return () => {
			unsubscribeNodesInitialized();
		};
	});

	onDestroy(() => {
		if (pendingDraw !== null && browser) {
			cancelAnimationFrame(pendingDraw);
		}

		nodes.set([]);
		edges.set([]);
	});
</script>

<div class="h-full w-full min-h-[360px] overflow-hidden px-2 pt-12">
	{#if messageCount === 0}
		<div class="flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400">
			{$i18n.t('No conversation yet')}
		</div>
	{:else}
		<SvelteFlow
			{nodes}
			{edges}
			{nodeTypes}
			fitView
			minZoom={0.08}
			maxZoom={1.6}
			colorMode={colorMode()}
			nodesConnectable={false}
			nodesDraggable={false}
			on:nodeclick={handleNodeClick}
		>
			<Controls showLock={false}>
				<ControlButton on:click={() => setLayoutDirection('TB')} title={$i18n.t('Vertical Layout')}>
					<AlignVertical className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={() => setLayoutDirection('LR')}
					title={$i18n.t('Horizontal Layout')}
				>
					<AlignHorizontal className="size-4" />
				</ControlButton>
			</Controls>

			<Background variant={BackgroundVariant.Dots} gap={18} size={1} />
		</SvelteFlow>
	{/if}
</div>

<style>
	:global(.mindmap-edge path) {
		stroke: rgba(148, 163, 184, 0.6);
		stroke-width: 1.5;
	}

	:global(.mindmap-edge-active path) {
		stroke: var(--primary, #3b82f6) !important;
		stroke-width: 2.25;
	}

	:global(.svelte-flow__controls) {
		border: 1px solid var(--border, rgba(148, 163, 184, 0.2));
		box-shadow: var(--shadow-card, 0 12px 28px rgba(0, 0, 0, 0.12));
	}
</style>
