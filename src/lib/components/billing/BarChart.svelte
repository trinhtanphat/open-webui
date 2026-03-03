<script lang="ts">
	/**
	 * Simple SVG bar chart for billing usage data.
	 * Props use traditional Svelte 4 export-let pattern for compatibility.
	 */

	import dayjs from 'dayjs';

	export let data: { label: string; value: number; secondary?: number }[] = [];
	export let height: number = 200;
	export let barColor: string = '#3b82f6';
	export let secondaryColor: string = '#10b981';
	export let valueLabel: string = 'Value';
	export let secondaryLabel: string = '';
	export let formatValue: (v: number) => string = (v) => v.toLocaleString();

	const pad = { t: 12, r: 8, b: 28, l: 50 };
	const W = 800;

	$: cw = W - pad.l - pad.r;
	$: ch = height - pad.t - pad.b;
	$: maxVal = Math.max(...data.map((d) => Math.max(d.value, d.secondary ?? 0)), 1);
	$: barW = data.length > 0 ? Math.max(4, (cw / data.length) * 0.6) : 0;
	$: gap = data.length > 0 ? cw / data.length : 0;
	$: labelStep = Math.max(1, Math.ceil(data.length / 10));

	$: yTicks = (() => {
		const count = 4;
		const step = maxVal / count;
		return Array.from({ length: count + 1 }, (_, i) => Math.round(i * step));
	})();

	let hoveredIdx: number | null = null;

	function getX(i: number): number {
		return pad.l + gap * i + gap / 2;
	}

	function getBarH(v: number): number {
		return (v / maxVal) * ch;
	}
</script>

{#if data.length === 0}
	<div class="text-sm text-gray-400 text-center py-8">No data</div>
{:else}
	<div class="relative w-full" style="height:{height}px">
		<svg
			viewBox="0 0 {W} {height}"
			class="w-full h-full"
			preserveAspectRatio="xMidYMid meet"
			role="img"
			on:mouseleave={() => (hoveredIdx = null)}
		>
			<!-- Y-axis gridlines and labels -->
			{#each yTicks as tick}
				{@const y = pad.t + ch - (tick / maxVal) * ch}
				<line x1={pad.l} x2={W - pad.r} y1={y} y2={y} stroke="#e5e7eb" stroke-width="0.5" />
				<text x={pad.l - 6} y={y + 3} text-anchor="end" fill="#9ca3af" font-size="10">
					{formatValue(tick)}
				</text>
			{/each}

			<!-- Bars -->
			{#each data as d, i}
				{@const x = getX(i)}
				{@const bh = getBarH(d.value)}
				{@const sh = d.secondary ? getBarH(d.secondary) : 0}

				<!-- Hover zone -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<rect
					x={x - gap / 2}
					y={pad.t}
					width={gap}
					height={ch}
					fill="transparent"
					on:mouseenter={() => (hoveredIdx = i)}
				/>

				<!-- Primary bar -->
				<rect
					x={d.secondary != null ? x - barW / 2 - 1 : x - barW / 2}
					y={pad.t + ch - bh}
					width={d.secondary != null ? barW / 2 : barW}
					height={bh}
					rx="2"
					fill={barColor}
					opacity={hoveredIdx === i ? 1 : 0.8}
				/>

				<!-- Secondary bar -->
				{#if d.secondary != null}
					<rect
						x={x + 1}
						y={pad.t + ch - sh}
						width={barW / 2}
						height={sh}
						rx="2"
						fill={secondaryColor}
						opacity={hoveredIdx === i ? 1 : 0.7}
					/>
				{/if}
			{/each}

			<!-- X-axis labels (show max 10) -->
			{#each data as d, i}
				{#if i % labelStep === 0 || i === data.length - 1}
					<text
						x={getX(i)}
						y={height - 6}
						text-anchor="middle"
						fill="#9ca3af"
						font-size="10"
					>
						{d.label.length > 8 ? d.label.slice(5) : d.label}
					</text>
				{/if}
			{/each}
		</svg>

		<!-- Tooltip -->
		{#if hoveredIdx !== null && data[hoveredIdx]}
			{@const d = data[hoveredIdx]}
			{@const xPct = (getX(hoveredIdx) / W) * 100}
			<div
				class="pointer-events-none absolute top-1"
				style="left:{Math.min(Math.max(xPct, 10), 90)}%"
			>
				<div
					class="min-w-[120px] -translate-x-1/2 rounded border border-gray-100 bg-white px-2.5 py-1.5 shadow-sm dark:border-gray-800 dark:bg-gray-900 text-[11px]"
				>
					<div class="text-[10px] text-gray-400 mb-1">{d.label}</div>
					<div class="flex items-center gap-1.5">
						<span class="w-2 h-2 rounded-full" style="background:{barColor}"></span>
						<span class="text-gray-600 dark:text-gray-300">{valueLabel}</span>
						<span class="font-medium ml-auto tabular-nums">{formatValue(d.value)}</span>
					</div>
					{#if d.secondary != null && secondaryLabel}
						<div class="flex items-center gap-1.5">
							<span class="w-2 h-2 rounded-full" style="background:{secondaryColor}"></span>
							<span class="text-gray-600 dark:text-gray-300">{secondaryLabel}</span>
							<span class="font-medium ml-auto tabular-nums">{formatValue(d.secondary)}</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/if}
