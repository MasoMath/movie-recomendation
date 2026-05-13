<script lang="ts">
    import * as d3 from 'd3';
    import type { GraphNode, GraphLink } from '../lib/types';

    export let nodes: GraphNode[] = [];
    export let links: GraphLink[] = [];
    export let onNodeClick: ((node: GraphNode) => void) | undefined = undefined;
    export let onCenterClick: (() => void) | undefined = undefined;

    let containerWidth: number;
    let containerHeight: number;
    let simulation: d3.Simulation<GraphNode, GraphLink>;

    /** Outer (recommended) poster card; center uses larger blank card */
    const OUT_W = 120;
    const OUT_H = 180;
    const CTR_W = 144;
    const CTR_H = 216;

    function cardLayout(node: GraphNode): { w: number; h: number; x: number; y: number } {
        if (node.isCenter) {
            return { w: CTR_W, h: CTR_H, x: -CTR_W / 2, y: -CTR_H / 2 };
        }
        return { w: OUT_W, h: OUT_H, x: -OUT_W / 2, y: -OUT_H / 2 };
    }

    $: if (nodes.length > 0 && containerWidth && containerHeight) {
        runSimulation();
    }

    function runSimulation(): void {
        if (simulation) simulation.stop();

        const menuWidth = 350;
        const centerX = menuWidth + (containerWidth - menuWidth) / 2;
        const centerY = containerHeight / 2;
        const padX = Math.max(90, CTR_W / 2 + 18);

        nodes.forEach((n) => {
            if (n.x === undefined) n.x = centerX + (Math.random() - 0.5) * 50;
            if (n.y === undefined) n.y = centerY + (Math.random() - 0.5) * 50;
        });

        const centerNode = nodes.find((n) => n.isCenter);
        if (centerNode) {
            centerNode.fx = centerX;
            centerNode.fy = centerY;
        }

        simulation = d3
            .forceSimulation<GraphNode, GraphLink>(nodes)
            .force('charge', d3.forceManyBody().strength(-2500))
            .force(
                'collide',
                d3
                    .forceCollide<GraphNode>()
                    .radius((d) => (d.isCenter ? 158 : 130))
                    .iterations(3)
            )
            .force(
                'link',
                d3
                    .forceLink<GraphNode, GraphLink>(links)
                    .id((d) => d.id as string)
                    .distance((d) => (1 - d.score) * 500 + 250)
            )
            .force('y', d3.forceY(centerY).strength(0.1))
            .force('x', d3.forceX(centerX).strength(0.01))
            .alphaDecay(0.02)
            .on('tick', () => {
                nodes.forEach((d) => {
                    if (d.x !== undefined && d.y !== undefined) {
                        d.x = Math.max(menuWidth + padX, Math.min(containerWidth - padX, d.x));
                        d.y = Math.max(100, Math.min(containerHeight - 100, d.y));
                    }
                });
                nodes = [...nodes];
                links = [...links];
            });
    }

    function handleNodeActivate(node: GraphNode): void {
        if (node.isCenter) {
            onCenterClick?.();
        } else {
            onNodeClick?.(node);
        }
    }
</script>

<div class="canvas-container" bind:clientWidth={containerWidth} bind:clientHeight={containerHeight}>
    <svg width="100%" height="100%">
        {#each links as link}
            <line
                x1={link.source.x}
                y1={link.source.y}
                x2={link.target.x}
                y2={link.target.y}
                stroke="#999"
                stroke-width="2"
            />
        {/each}

        {#each nodes as node}
            {@const c = cardLayout(node)}
            <g
                transform="translate({node.x},{node.y})"
                on:click={() => handleNodeActivate(node)}
                on:keydown={(e) => e.key === 'Enter' && handleNodeActivate(node)}
                role="button"
                tabindex="0"
                class:clickable={!node.isCenter}
                class:center-card={node.isCenter}
            >
                <clipPath id="clip-{node.id}">
                    <rect x={c.x} y={c.y} width={c.w} height={c.h} rx="8" />
                </clipPath>
                {#if node.isCenter}
                    <rect
                        x={c.x}
                        y={c.y}
                        width={c.w}
                        height={c.h}
                        fill="#0f172a"
                        stroke="#475569"
                        stroke-width="2"
                        rx="8"
                    />
                {:else}
                    <rect
                        x={c.x}
                        y={c.y}
                        width={c.w}
                        height={c.h}
                        fill="#cbd5e1"
                        stroke="#334155"
                        stroke-width="2"
                        rx="8"
                    />
                    {#if node.poster_url}
                        <image
                            href={node.poster_url}
                            x={c.x}
                            y={c.y}
                            width={c.w}
                            height={c.h}
                            clip-path="url(#clip-{node.id})"
                            preserveAspectRatio="xMidYMid slice"
                        />
                    {:else}
                        <text
                            x="0"
                            y="-10"
                            text-anchor="middle"
                            font-weight="bold"
                            font-family="sans-serif"
                            font-size="14"
                        >
                            {node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title}
                        </text>
                    {/if}
                    <rect x="-25" y="70" width="50" height="20" rx="4" fill="rgba(255,255,255,0.9)" />
                    <text
                        x="0"
                        y="84"
                        text-anchor="middle"
                        font-family="sans-serif"
                        font-size="12"
                        fill="#000"
                        font-weight="bold"
                    >
                        {node.score !== undefined ? node.score.toFixed(2) : ''}
                    </text>
                {/if}
            </g>
        {/each}
    </svg>
</div>

<style>
    .canvas-container {
        flex-grow: 1;
        width: 100%;
        height: 100%;
        background-color: #0a0a0a;
    }

    svg {
        display: block;
    }

    .clickable {
        cursor: pointer;
        transition: transform 0.2s;
    }

    .clickable:hover rect {
        fill: #222 !important;
        stroke: #ffd700 !important;
    }

    .center-card {
        cursor: pointer;
        transition: transform 0.2s;
    }

    .center-card:hover rect {
        stroke: #ffd700 !important;
        fill: #1e293b !important;
    }
</style>
