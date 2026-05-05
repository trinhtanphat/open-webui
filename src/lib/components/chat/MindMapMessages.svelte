<script lang="ts">
	import { SvelteFlowProvider } from '@xyflow/svelte';

	import Canvas from './MindMapMessages/Canvas.svelte';

	export let history: any = { messages: {}, currentId: null };
	export let onNodeSelect: (messageId: string) => void | Promise<void> = (_messageId) => {};
</script>

<SvelteFlowProvider>
	<Canvas bind:history {onNodeSelect} />
</SvelteFlowProvider>
