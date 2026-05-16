<script lang="ts">
	import { getContext } from 'svelte';
	import { Handle, NodeResizer, Position } from '@xyflow/svelte';

	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ProfileImage from '../Messages/ProfileImage.svelte';

	const i18n = getContext('i18n');

	type ChatNodeData = {
		message?: any;
		model?: any;
		user?: any;
		direction?: 'TB' | 'LR';
		isActive?: boolean;
		isOnActiveBranch?: boolean;
		isEditMode?: boolean;
		isResizeMode?: boolean;
		branchLabel?: string;
		childCount?: number;
		width?: number;
		height?: number;
		onNodeResize?: (id: string, size: { width?: number; height?: number; x?: number; y?: number }) => void;
	};

	export let id = '';
	export let data: ChatNodeData = {};
	export let selected = false;
	export let width: number | undefined = undefined;
	export let height: number | undefined = undefined;

	const minNodeWidth = 240;
	const minNodeHeight = 112;
	const maxNodeWidth = 520;
	const maxNodeHeight = 320;

	const stringifyContent = (content: any) => {
		if (typeof content === 'string') {
			return content;
		}

		if (Array.isArray(content)) {
			return content
				.map((part) => {
					if (typeof part === 'string') {
						return part;
					}

					return part?.text ?? part?.content ?? '';
				})
				.join(' ');
		}

		if (content && typeof content === 'object') {
			return content.text ?? content.content ?? '';
		}

		return '';
	};

	const stripMarkdown = (text: string) => {
		return text
			.replace(/```[\s\S]*?```/g, ' ')
			.replace(/`([^`]+)`/g, '$1')
			.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
			.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
			.replace(/[#>*_~|\-]+/g, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	};

	const truncate = (text: string, maxLength = 180) => {
		return text.length > maxLength ? `${text.slice(0, maxLength).trim()}...` : text;
	};

	$: message = data?.message ?? {};
	$: isUser = message?.role === 'user';
	$: rawContent = stringifyContent(message?.error?.content ?? message?.content ?? '');
	$: preview = truncate(stripMarkdown(rawContent));
	$: displayName = isUser
		? (data?.user?.name ?? $i18n.t('You'))
		: (data?.model?.name ?? message?.model ?? $i18n.t('Assistant'));
	$: avatarSrc = isUser
		? data?.user?.id
			? `${WEBUI_API_BASE_URL}/users/${data.user.id}/profile/image`
			: ''
		: `${WEBUI_API_BASE_URL}/models/model/profile/image?id=${encodeURIComponent(
				data?.model?.id ?? message?.model ?? ''
			)}&lang=${$i18n.language}`;
	$: targetPosition = data?.direction === 'LR' ? Position.Left : Position.Top;
	$: sourcePosition = data?.direction === 'LR' ? Position.Right : Position.Bottom;
	$: nodeWidth = Math.max(minNodeWidth, Math.round(width ?? data?.width ?? 300));
	$: nodeHeight = Math.max(minNodeHeight, Math.round(height ?? data?.height ?? 124));
	$: showResizer = !!data?.isResizeMode && (selected || data?.isActive);
</script>

<Tooltip content={rawContent || displayName} allowHTML={false} className="block">
	<div
		class="mindmap-chat-node group relative rounded-xl border bg-white/95 px-3.5 py-3 shadow-sm transition-colors dark:bg-gray-900/95 {data?.isActive
			? 'border-blue-500 ring-2 ring-blue-500/20 dark:border-blue-400'
			: data?.isOnActiveBranch
				? 'border-blue-300 dark:border-blue-600'
				: 'border-gray-200 dark:border-gray-800'} {data?.isEditMode ? 'mindmap-chat-node-editable' : ''}"
		style={`width: ${nodeWidth}px; height: ${nodeHeight}px;`}
		aria-label={`${displayName}: ${preview}`}
	>
		<NodeResizer
			nodeId={id}
			isVisible={showResizer}
			minWidth={minNodeWidth}
			minHeight={minNodeHeight}
			maxWidth={maxNodeWidth}
			maxHeight={maxNodeHeight}
			color="var(--primary, #3b82f6)"
			handleClass="mindmap-resize-handle"
			lineClass="mindmap-resize-line"
			onResizeEnd={(_event, params) => data?.onNodeResize?.(id, params)}
		/>

		<Handle
			type="target"
			position={targetPosition}
			class="!size-2 !border-0 !bg-gray-300 dark:!bg-gray-700"
		/>

		<div class="flex min-h-0 min-w-0 items-start gap-2.5">
			<ProfileImage src={avatarSrc} className="size-7 flex-none" />

			<div class="flex min-h-0 min-w-0 flex-1 flex-col">
				<div class="flex min-w-0 items-center gap-2">
					<div
						class="min-w-0 flex-1 truncate text-xs font-semibold text-gray-900 dark:text-gray-100"
					>
						{displayName}
					</div>

					{#if data?.isActive}
						<div
							class="flex-none rounded-md bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-500/15 dark:text-blue-200"
						>
							{$i18n.t('Active')}
						</div>
					{:else if (data?.childCount ?? 0) > 0}
						<div
							class="flex-none rounded-md bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400"
						>
							{data.childCount}
						</div>
					{/if}
				</div>

				{#if data?.branchLabel}
					<div class="mt-1 truncate text-[10px] font-medium text-gray-400 dark:text-gray-500">
						{data.branchLabel}
					</div>
				{/if}

				{#if message?.error}
					<div class="mt-1.5 line-clamp-3 min-h-0 text-xs leading-5 text-red-500">
						{message.error.content}
					</div>
				{:else}
					<div class="mt-1.5 line-clamp-3 min-h-0 text-xs leading-5 text-gray-600 dark:text-gray-400">
						{preview || $i18n.t('Empty message')}
					</div>
				{/if}
			</div>
		</div>

		<Handle
			type="source"
			position={sourcePosition}
			class="!size-2 !border-0 !bg-gray-300 dark:!bg-gray-700"
		/>
	</div>
</Tooltip>

<style>
	:global(.svelte-flow__node-chat) {
		border-radius: 0.75rem;
	}

	:global(.svelte-flow__node-chat.selected .mindmap-chat-node) {
		box-shadow: 0 0 0 2px var(--primary-glow, rgba(59, 130, 246, 0.32));
	}

	:global(.svelte-flow__node-chat.draggable .mindmap-chat-node-editable) {
		cursor: grab;
	}

	:global(.svelte-flow__node-chat.dragging .mindmap-chat-node-editable) {
		cursor: grabbing;
	}

	:global(.mindmap-resize-handle) {
		border: 2px solid var(--bg-elev, #fff);
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.22);
	}

	:global(.mindmap-resize-line) {
		border-color: var(--primary-glow, rgba(59, 130, 246, 0.34));
	}
</style>
