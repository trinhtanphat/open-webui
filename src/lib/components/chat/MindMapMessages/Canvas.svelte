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
		MiniMap,
		SelectionMode,
		SvelteFlow,
		useNodesInitialized,
		useSvelteFlow
	} from '@xyflow/svelte';

	import { models, theme, user } from '$lib/stores';
	import AlignHorizontal from '$lib/components/icons/AlignHorizontal.svelte';
	import AlignVertical from '$lib/components/icons/AlignVertical.svelte';
	import ArrowsPointingOut from '$lib/components/icons/ArrowsPointingOut.svelte';
	import CursorArrowRays from '$lib/components/icons/CursorArrowRays.svelte';
	import Grid from '$lib/components/icons/Grid.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Merge from '$lib/components/icons/Merge.svelte';
	import Reset from '$lib/components/icons/Reset.svelte';
	import ChatNode from './ChatNode.svelte';
	import AreaNode from './AreaNode.svelte';

	import '@xyflow/svelte/dist/style.css';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	export let history: any = { messages: {}, currentId: null };
	export let onNodeSelect: (messageId: string) => void | Promise<void> = (_messageId) => {};

	const defaultNodeWidth = 300;
	const defaultNodeHeight = 124;
	const areaPadding = 46;
	const areaHeaderHeight = 34;

	const nodes = writable<any[]>([]);
	const edges = writable<any[]>([]);
	const nodeTypes = { chat: ChatNode, area: AreaNode };

	const { fitView } = useSvelteFlow();
	const nodesInitialized = useNodesInitialized();

	let layoutDirection: 'TB' | 'LR' = 'TB';
	let editMode = false;
	let resizeMode = false;
	let groupMode = true;
	let relationMode = true;
	let miniMapMode = true;
	let pendingDraw: number | null = null;
	let lastFocusKey = '';
	let messageCount = 0;
	let nodeLayouts: Record<
		string,
		{ position?: { x: number; y: number }; width?: number; height?: number }
	> = {};

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

	const getBranchRootId = (messages: Record<string, any>, messageId: string) => {
		const visited = new Set<string>();
		let currentId = messageId;

		while (
			messages[currentId]?.parentId &&
			messages[messages[currentId].parentId] &&
			!visited.has(currentId)
		) {
			visited.add(currentId);
			currentId = messages[currentId].parentId;
		}

		return currentId;
	};

	const stringifyContent = (content: any) => {
		if (typeof content === 'string') return content;
		if (Array.isArray(content)) {
			return content.map((part) => part?.text ?? part?.content ?? '').join(' ');
		}
		return content?.text ?? content?.content ?? '';
	};

	const getBranchLabel = (messages: Record<string, any>, rootId: string, fallbackIndex: number) => {
		const rootMessage = messages[rootId];
		const rawLabel = stringifyContent(rootMessage?.content ?? rootMessage?.error?.content ?? '')
			.replace(/\s+/g, ' ')
			.trim();

		return rawLabel ? rawLabel.slice(0, 44) : `${$i18n.t('Branch')} ${fallbackIndex + 1}`;
	};

	const getNodeDimensions = (id: string) => ({
		width: nodeLayouts[id]?.width ?? defaultNodeWidth,
		height: nodeLayouts[id]?.height ?? defaultNodeHeight
	});

	const buildAreaNodes = (
		chatNodes: any[],
		messages: Record<string, any>,
		activeIds: Set<string>
	) => {
		if (!groupMode) return [];

		const groups = new Map<string, any[]>();

		for (const node of chatNodes) {
			const rootId = getBranchRootId(messages, node.id);
			groups.set(rootId, [...(groups.get(rootId) ?? []), node]);
		}

		return Array.from(groups.entries()).map(([rootId, groupNodes], index) => {
			const minX = Math.min(...groupNodes.map((node) => node.position.x));
			const minY = Math.min(...groupNodes.map((node) => node.position.y));
			const maxX = Math.max(
				...groupNodes.map((node) => node.position.x + (node.width ?? defaultNodeWidth))
			);
			const maxY = Math.max(
				...groupNodes.map((node) => node.position.y + (node.height ?? defaultNodeHeight))
			);

			return {
				id: `area-${rootId}`,
				type: 'area',
				position: {
					x: minX - areaPadding,
					y: minY - areaPadding - areaHeaderHeight
				},
				width: maxX - minX + areaPadding * 2,
				height: maxY - minY + areaPadding * 2 + areaHeaderHeight,
				data: {
					label: getBranchLabel(messages, rootId, index),
					count: groupNodes.length,
					isActive: groupNodes.some((node) => activeIds.has(node.id))
				},
				selectable: false,
				draggable: false,
				deletable: false,
				class: 'mindmap-area-wrapper',
				zIndex: -10
			};
		});
	};

	const buildRelationEdges = (messages: Record<string, any>) => {
		if (!relationMode) return [];

		return Object.values(messages).flatMap((message: any) => {
			const childrenIds = (message?.childrenIds ?? []).filter((id: string) => messages[id]);

			if (childrenIds.length < 2) return [];

			return childrenIds.slice(1).map((childId: string, index: number) => ({
				id: `branch-link-${message.id}-${childrenIds[index]}-${childId}`,
				source: childrenIds[index],
				target: childId,
				type: 'smoothstep',
				selectable: false,
				animated: false,
				class: 'mindmap-edge-related',
				zIndex: -2
			}));
		});
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
			graph.setNode(id, getNodeDimensions(id));
		}

		for (const id of orderedIds) {
			const parentId = messages[id]?.parentId;

			if (parentId && messages[parentId]) {
				graph.setEdge(parentId, id);
			}
		}

		dagre.layout(graph);

		const chatNodes = orderedIds.map((id) => {
				const message = messages[id];
				const position = graph.node(id) ?? { x: 0, y: 0 };
				const dimensions = getNodeDimensions(id);
				const savedPosition = nodeLayouts[id]?.position;
				const branchRootId = getBranchRootId(messages, id);

				return {
					id,
					type: 'chat',
					position: {
						x: savedPosition?.x ?? position.x - dimensions.width / 2,
						y: savedPosition?.y ?? position.y - dimensions.height / 2
					},
					width: dimensions.width,
					height: dimensions.height,
					data: {
						message,
						model: $models.find((model) => model.id === message?.model),
						user: $user,
						direction: layoutDirection,
						isActive: history?.currentId === id,
						isOnActiveBranch: activeIds.has(id),
						isEditMode: editMode,
						isResizeMode: resizeMode,
						branchLabel: groupMode ? getBranchLabel(messages, branchRootId, 0) : '',
						childCount: message?.childrenIds?.length ?? 0,
						width: dimensions.width,
						height: dimensions.height,
						onNodeResize: handleNodeResize
					},
					draggable: editMode,
					selectable: true,
					zIndex: activeIds.has(id) ? 2 : 1
				};
			});
		const areaNodes = buildAreaNodes(chatNodes, messages, activeIds);

		nodes.set([...areaNodes, ...chatNodes]);

		edges.set(
			[
				...orderedIds
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
				.filter(Boolean),
				...buildRelationEdges(messages)
			]
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

	const setEditMode = (enabled: boolean) => {
		editMode = enabled;
		if (!editMode) resizeMode = false;
		scheduleDraw();
	};

	const toggleResizeMode = () => {
		resizeMode = !resizeMode;
		if (resizeMode) editMode = true;
		scheduleDraw();
	};

	const toggleGroupMode = () => {
		groupMode = !groupMode;
		scheduleDraw();
	};

	const toggleRelationMode = () => {
		relationMode = !relationMode;
		scheduleDraw();
	};

	const resetLayout = async () => {
		nodeLayouts = {};
		lastFocusKey = '';
		scheduleDraw();
		await focusCurrentNode();
	};

	const handleNodeResize = (
		id: string,
		params: { width?: number; height?: number; x?: number; y?: number }
	) => {
		nodeLayouts = {
			...nodeLayouts,
			[id]: {
				...(nodeLayouts[id] ?? {}),
				width: params.width ?? nodeLayouts[id]?.width,
				height: params.height ?? nodeLayouts[id]?.height,
				position:
					params.x !== undefined && params.y !== undefined
						? { x: params.x, y: params.y }
						: nodeLayouts[id]?.position
			}
		};
		scheduleDraw();
	};

	const handleNodeDragStop = (event: CustomEvent) => {
		const draggedNodes = event.detail?.nodes ?? [];
		const updates = draggedNodes
			.filter((node) => node?.type === 'chat' && node?.id)
			.reduce((nextLayouts, node) => {
				nextLayouts[node.id] = {
					...(nextLayouts[node.id] ?? {}),
					position: node.position,
					width: node.width ?? nextLayouts[node.id]?.width,
					height: node.height ?? nextLayouts[node.id]?.height
				};
				return nextLayouts;
			}, { ...nodeLayouts });

		nodeLayouts = updates;
	};

	const handleNodeClick = async (event: CustomEvent) => {
		const nodeId = event.detail?.node?.id;

		if (!nodeId || nodeId.startsWith('area-')) {
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
			maxZoom={2.4}
			colorMode={colorMode()}
			nodesConnectable={false}
			nodesDraggable={editMode}
			elementsSelectable={true}
			selectionOnDrag={editMode}
			selectionMode={SelectionMode.Partial}
			selectionKey={editMode ? null : 'Shift'}
			panOnDrag={!editMode}
			panOnScroll={true}
			snapGrid={[12, 12]}
			on:nodeclick={handleNodeClick}
			on:nodedragstop={handleNodeDragStop}
		>
			<Controls showZoom={true} showFitView={true} showLock={false} fitViewOptions={{ padding: 0.18 }}>
				<ControlButton on:click={() => setLayoutDirection('TB')} title={$i18n.t('Vertical Layout')}>
					<AlignVertical className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={() => setLayoutDirection('LR')}
					title={$i18n.t('Horizontal Layout')}
				>
					<AlignHorizontal className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={() => setEditMode(!editMode)}
					title={editMode ? $i18n.t('Lock layout') : $i18n.t('Edit layout')}
					aria-pressed={editMode}
				>
					{#if editMode}
						<CursorArrowRays className="size-4" />
					{:else}
						<LockClosed className="size-4" />
					{/if}
				</ControlButton>

				<ControlButton
					on:click={toggleResizeMode}
					title={$i18n.t('Resize nodes')}
					aria-pressed={resizeMode}
				>
					<ArrowsPointingOut className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={toggleGroupMode}
					title={$i18n.t('Group branches')}
					aria-pressed={groupMode}
				>
					<Grid className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={toggleRelationMode}
					title={$i18n.t('Show branch links')}
					aria-pressed={relationMode}
				>
					<Merge className="size-4" />
				</ControlButton>

				<ControlButton
					on:click={() => (miniMapMode = !miniMapMode)}
					title={$i18n.t('Mini map')}
					aria-pressed={miniMapMode}
				>
					<ArrowsPointingOut className="size-4" />
				</ControlButton>

				<ControlButton on:click={resetLayout} title={$i18n.t('Reset layout')}>
					<Reset className="size-4" />
				</ControlButton>
			</Controls>

			{#if miniMapMode}
				<MiniMap
					position="bottom-right"
					pannable
					zoomable
					nodeBorderRadius={8}
					nodeColor={(node) => (node.type === 'area' ? 'transparent' : 'var(--primary, #3b82f6)')}
					nodeStrokeColor={(node) => (node.type === 'area' ? 'transparent' : 'var(--border, rgba(148, 163, 184, 0.35))')}
				/>
			{/if}

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

	:global(.mindmap-edge-related path) {
		stroke: var(--accent, #14b8a6) !important;
		stroke-dasharray: 5 6;
		stroke-opacity: 0.55;
		stroke-width: 1.4;
	}

	:global(.svelte-flow__node-area) {
		pointer-events: none;
	}

	:global(.mindmap-area-wrapper) {
		pointer-events: none;
	}

	:global(.svelte-flow__controls) {
		border: 1px solid var(--border, rgba(148, 163, 184, 0.2));
		box-shadow: var(--shadow-card, 0 12px 28px rgba(0, 0, 0, 0.12));
	}

	:global(.svelte-flow__controls-button[aria-pressed='true']) {
		background: var(--primary-dim, rgba(59, 130, 246, 0.14)) !important;
		color: var(--primary, #3b82f6) !important;
	}

	:global(.svelte-flow__minimap) {
		border: 1px solid var(--border, rgba(148, 163, 184, 0.2));
		border-radius: 10px;
		overflow: hidden;
		box-shadow: var(--shadow-card, 0 12px 28px rgba(0, 0, 0, 0.12));
	}
</style>
