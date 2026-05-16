<script lang="ts">
	export let data: {
		label?: string;
		count?: number;
		isActive?: boolean;
	} = {};
	export let width = 0;
	export let height = 0;

	$: areaWidth = Math.max(160, Math.round(width ?? 0));
	$: areaHeight = Math.max(120, Math.round(height ?? 0));
</script>

<div
	class="mindmap-area-node {data?.isActive ? 'mindmap-area-node-active' : ''}"
	style={`width: ${areaWidth}px; height: ${areaHeight}px;`}
>
	<div class="mindmap-area-node-label">
		<span class="truncate">{data?.label ?? 'Branch'}</span>
		{#if data?.count}
			<span class="mindmap-area-node-count">{data.count}</span>
		{/if}
	</div>
</div>

<style>
	.mindmap-area-node {
		height: 100%;
		border: 1px solid var(--flow-area-border, rgba(148, 163, 184, 0.28));
		border-radius: 14px;
		background:
			linear-gradient(var(--flow-area-fill, rgba(148, 163, 184, 0.08)), var(--flow-area-fill, rgba(148, 163, 184, 0.08))),
			var(--flow-area-bg, transparent);
		box-shadow: inset 0 1px 0 var(--flow-area-highlight, rgba(255, 255, 255, 0.08));
		color: var(--text-muted, #64748b);
		overflow: hidden;
	}

	.mindmap-area-node-active {
		border-color: var(--primary, #3b82f6);
		background:
			linear-gradient(var(--primary-dim, rgba(59, 130, 246, 0.12)), var(--primary-dim, rgba(59, 130, 246, 0.12))),
			var(--flow-area-bg, transparent);
	}

	.mindmap-area-node-label {
		display: flex;
		align-items: center;
		gap: 6px;
		max-width: calc(100% - 24px);
		padding: 10px 12px;
		font-size: 11px;
		font-weight: 600;
		line-height: 1;
		letter-spacing: 0;
		text-transform: uppercase;
	}

	.mindmap-area-node-count {
		flex: none;
		border-radius: 999px;
		background: var(--bg-elev, rgba(255, 255, 255, 0.86));
		padding: 2px 6px;
		font-size: 10px;
		color: var(--text, #0f172a);
	}
</style>