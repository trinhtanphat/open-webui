<script lang="ts">
	import { getContext } from 'svelte';
	import { Handle, Position } from '@xyflow/svelte';

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
		childCount?: number;
	};

	export let data: ChatNodeData = {};

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
</script>

<Tooltip content={rawContent || displayName} allowHTML={false} className="block">
	<div
		class="mindmap-chat-node group relative w-[300px] min-h-[112px] rounded-xl border bg-white/95 px-3.5 py-3 shadow-sm transition-colors dark:bg-gray-900/95 {data?.isActive
			? 'border-blue-500 ring-2 ring-blue-500/20 dark:border-blue-400'
			: data?.isOnActiveBranch
				? 'border-blue-300 dark:border-blue-600'
				: 'border-gray-200 dark:border-gray-800'}"
		aria-label={`${displayName}: ${preview}`}
	>
		<Handle
			type="target"
			position={targetPosition}
			class="!size-2 !border-0 !bg-gray-300 dark:!bg-gray-700"
		/>

		<div class="flex min-w-0 items-start gap-2.5">
			<ProfileImage src={avatarSrc} className="size-7 flex-none" />

			<div class="min-w-0 flex-1">
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

				{#if message?.error}
					<div class="mt-1.5 line-clamp-3 text-xs leading-5 text-red-500">
						{message.error.content}
					</div>
				{:else}
					<div class="mt-1.5 line-clamp-3 text-xs leading-5 text-gray-600 dark:text-gray-400">
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
</style>
