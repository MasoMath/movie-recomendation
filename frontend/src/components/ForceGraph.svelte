<script lang="ts">
    import * as d3 from 'd3';
    import type { GraphNode, GraphLink } from '../lib/types';

    export let nodes: GraphNode[] = [];
    export let links: GraphLink[] = [];
    export let graphKey: number = 0;
    export let onNodeClick: ((node: GraphNode) => void) | undefined = undefined;
    export let onCenterClick: (() => void) | undefined = undefined;

    let containerWidth: number;
    let containerHeight: number;
    let simulation: d3.Simulation<GraphNode, GraphLink>;
    let rafId: number | null = null;
    let lastSimKey = '';

    // Card dimensions
    const OUT_W = 120;
    const OUT_H = 180;
    const CTR_W = 144;
    const CTR_H = 216;


    // Score label below card
    const SCORE_LABEL_GAP = 5;
    const SCORE_LABEL_HEIGHT = 22;
    const SCORE_LABEL_RX = 4;
    const SCORE_LABEL_TEXT_OFFSET = 15; // pixels from label rect top to text baseline

    // Layout
    const MENU_WIDTH = 350;
    const HORIZONTAL_EDGE_PAD = 18;  // extra buffer beyond half-card-width at screen edges
    const TOP_EDGE_PAD = OUT_H / 2 + 20;
    const BOTTOM_EDGE_PAD = OUT_H / 2 + SCORE_LABEL_GAP + SCORE_LABEL_HEIGHT + 20;
    const INITIAL_ANGLE_JITTER = 0.25; // radians of random offset added to each evenly-spaced angle

    // Simulation tuning
    const CHARGE_STRENGTH = -4200;
    const CTR_COLLISION_RADIUS = 158;
    const OUT_COLLISION_RADIUS = 148;
    const COLLISION_ITERATIONS = 5;
    const LINK_DISTANCE_SCALE = 360;
    const LINK_DISTANCE_MIN = 230;
    const Y_FORCE_STRENGTH = 0.1;
    const X_FORCE_STRENGTH = 0.01;
    const ALPHA_DECAY = 0.02;

    function cardLayout(node: GraphNode): { w: number; h: number; x: number; y: number } {
        if (node.isCenter) {
            return { w: CTR_W, h: CTR_H, x: -CTR_W / 2, y: -CTR_H / 2 };
        }
        return { w: OUT_W, h: OUT_H, x: -OUT_W / 2, y: -OUT_H / 2 };
    }

    // Only restart the simulation when the actual node set or container dimensions change,
    // not on every tick-driven nodes reassignment.
    $: {
        const key = nodes.map(n => String(n.id)).join(',') + `|${containerWidth ?? 0}|${containerHeight ?? 0}|${graphKey}`;
        if (key !== lastSimKey && nodes.length > 0 && containerWidth && containerHeight) {
            lastSimKey = key;
            runSimulation();
        }
    }

    function runSimulation(): void {
        if (simulation) simulation.stop();
        if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }

        const centerX = MENU_WIDTH + (containerWidth - MENU_WIDTH) / 2;
        const centerY = containerHeight / 2;
        const padX = CTR_W / 2 + HORIZONTAL_EDGE_PAD;

        // Scale forces so the layout fills the available canvas on any screen size.
        // Reference: a ~800px tall small laptop. Linear scale keeps proportions natural.
        const scale = Math.min(containerWidth - MENU_WIDTH, containerHeight) / 800;

        const centerNode = nodes.find(n => n.isCenter);
        if (centerNode) {
            centerNode.x = centerX;
            centerNode.y = centerY;
            centerNode.fx = centerX;
            centerNode.fy = centerY;
        }

        const outerNodes = nodes.filter(n => !n.isCenter);
        const initR = LINK_DISTANCE_MIN * scale * 0.9;
        outerNodes.forEach((n, i) => {
            if (n.x === undefined) {
                const angle = (2 * Math.PI * i) / outerNodes.length + (Math.random() - 0.5) * INITIAL_ANGLE_JITTER;
                n.x = centerX + initR * Math.cos(angle);
                n.y = centerY + initR * Math.sin(angle);
            }
        });

        const scores = links.map(l => l.score);
        const minScore = Math.min(...scores);
        const maxScore = Math.max(...scores);
        const scoreRange = maxScore - minScore;

        simulation = d3.forceSimulation<GraphNode, GraphLink>(nodes)
            .force('charge', d3.forceManyBody().strength(CHARGE_STRENGTH * scale))
            .force('collide', d3.forceCollide<GraphNode>().radius(d => d.isCenter ? CTR_COLLISION_RADIUS : OUT_COLLISION_RADIUS).iterations(COLLISION_ITERATIONS))
            .force('link', d3.forceLink<GraphNode, GraphLink>(links)
                .id(d => d.id as string)
                .distance(d => {
                    const norm = scoreRange > 0 ? (d.score - minScore) / scoreRange : 0.5;
                    return ((1 - norm) * LINK_DISTANCE_SCALE + LINK_DISTANCE_MIN) * scale;
                })
            )
            .force('y', d3.forceY(centerY).strength(Y_FORCE_STRENGTH))
            .force('x', d3.forceX(centerX).strength(X_FORCE_STRENGTH))
            .alphaDecay(ALPHA_DECAY)
            .on('tick', () => {
                nodes.forEach(d => {
                    if (d.x !== undefined && d.y !== undefined) {
                        if (d.x < MENU_WIDTH + padX) { d.x = MENU_WIDTH + padX; if ((d.vx ?? 0) < 0) d.vx = 0; }
                        else if (d.x > containerWidth - padX) { d.x = containerWidth - padX; if ((d.vx ?? 0) > 0) d.vx = 0; }
                        if (d.y < TOP_EDGE_PAD) { d.y = TOP_EDGE_PAD; if ((d.vy ?? 0) < 0) d.vy = 0; }
                        else if (d.y > containerHeight - BOTTOM_EDGE_PAD) { d.y = containerHeight - BOTTOM_EDGE_PAD; if ((d.vy ?? 0) > 0) d.vy = 0; }
                    }
                });
                // Throttle Svelte re-renders to one per animation frame.
                if (rafId === null) {
                    rafId = requestAnimationFrame(() => {
                        nodes = [...nodes];
                        links = [...links];
                        rafId = null;
                    });
                }
            })
            .on('end', () => {
                if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
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
                        fill="#141414"
                        stroke="#8b0000"
                        stroke-width="2"
                        rx="8"
                    />
                    <text
                        x="0"
                        y="5"
                        text-anchor="middle"
                        font-family="sans-serif"
                        font-size="13"
                        font-weight="bold"
                        fill="#c9a96e"
                    >Your Inputs</text>
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
                            font-size="15"
                        >
                            {node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title}
                        </text>
                    {/if}
                    <rect
                        x={c.x}
                        y={c.y + c.h + SCORE_LABEL_GAP}
                        width={c.w}
                        height={SCORE_LABEL_HEIGHT}
                        rx={SCORE_LABEL_RX}
                        fill="#1a1a1a"
                    />
                    <text
                        x="0"
                        y={c.y + c.h + SCORE_LABEL_GAP + SCORE_LABEL_TEXT_OFFSET}
                        text-anchor="middle"
                        font-family="sans-serif"
                        font-size="13"
                        fill="#c9a96e"
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
        transition: filter 0.2s;
    }

    .clickable:hover {
        filter: drop-shadow(0 0 10px rgba(180, 30, 30, 0.85));
    }

    .center-card {
        cursor: pointer;
        transition: filter 0.2s;
    }

    .center-card:hover {
        filter: drop-shadow(0 0 10px rgba(180, 30, 30, 0.7));
    }
</style>
