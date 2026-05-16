<script lang="ts">
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { Handle, Position, type NodeProps } from '@xyflow/svelte';
	import { getContext } from 'svelte';

	import ProfileImage from '../Messages/ProfileImage.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';

	const i18n = getContext('i18n');

	type $$Props = NodeProps;
	export let data: $$Props['data'];
</script>

<div
	class="overview-chat-node group h-20 w-60 rounded-xl border px-4 py-3 shadow-md transition-colors {data?.isActive
		? 'border-blue-500 ring-2 ring-blue-500/20 dark:border-blue-400'
		: data?.isOnActiveBranch
			? 'border-blue-300 dark:border-blue-700'
			: 'border-gray-100 dark:border-gray-800'} bg-white dark:bg-gray-900"
>
	<Tooltip
		content={data?.message?.error ? data.message.error.content : data.message.content}
		class="w-full"
		allowHTML={false}
	>
		{#if data.message.role === 'user'}
			<div class="flex w-full">
				<ProfileImage
					src={`${WEBUI_API_BASE_URL}/users/${data.user.id}/profile/image`}
					className={'size-5 -translate-y-[1px] flex-shrink-0'}
				/>
				<div class="ml-2">
					<div class=" flex justify-between items-center">
						<div class="text-xs text-black dark:text-white font-medium line-clamp-1">
							{data?.user?.name ?? 'User'}
						</div>
					</div>

					{#if data?.message?.error}
						<div class="text-red-500 line-clamp-2 text-xs mt-0.5">{data.message.error.content}</div>
					{:else}
						<div class="text-gray-500 line-clamp-2 text-xs mt-0.5">{data.message.content}</div>
					{/if}
				</div>
			</div>
		{:else}
			<div class="flex w-full">
				<ProfileImage
					src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${data.model?.id ?? data.message.model}&lang=${$i18n.language}`}
					className={'size-5 -translate-y-[1px] flex-shrink-0'}
				/>

				<div class="ml-2">
					<div class=" flex justify-between items-center">
						<div class="text-xs text-black dark:text-white font-medium line-clamp-1">
							{data?.model?.name ?? data?.message?.model ?? 'Assistant'}
						</div>

						<button
							class={data?.message?.favorite ? '' : 'invisible group-hover:visible'}
							aria-label={data?.message?.favorite
								? $i18n.t('Remove from favorites')
								: $i18n.t('Add to favorites')}
							on:click={() => {
								data.message.favorite = !(data?.message?.favorite ?? false);
							}}
						>
							<Heart
								className="size-3 {data?.message?.favorite
									? 'fill-red-500 stroke-red-500'
									: 'hover:fill-red-500 hover:stroke-red-500'} "
								strokeWidth="2.5"
							/>
						</button>
					</div>

					{#if data?.message?.error}
						<div class="text-red-500 line-clamp-2 text-xs mt-0.5">
							{data.message.error.content}
						</div>
					{:else}
						<div class="text-gray-500 line-clamp-2 text-xs mt-0.5">{data.message.content}</div>
					{/if}
				</div>
			</div>
		{/if}
	</Tooltip>
	<Handle type="target" position={Position.Top} class="!size-2 !border-0 !bg-gray-300 dark:!bg-gray-700" />
	<Handle type="source" position={Position.Bottom} class="!size-2 !border-0 !bg-gray-300 dark:!bg-gray-700" />
</div>

<style>
	:global(.overview-chat-node) {
		background: var(--flow-node-bg, var(--card-bg, #ffffff));
		border-color: var(--flow-node-border, var(--border, rgba(148, 163, 184, 0.24)));
		color: var(--text, #0f172a);
	}

	:global(.svelte-flow__node-custom.selected .overview-chat-node) {
		box-shadow: 0 0 0 2px var(--primary-glow, rgba(59, 130, 246, 0.32));
	}
</style>
