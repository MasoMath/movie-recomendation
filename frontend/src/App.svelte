<script lang="ts">
    import { onMount } from 'svelte';
    import * as d3 from 'd3';
    import valid_movies from "./assets/valid_movies.json";
    import './app.css'

    interface GraphNode extends d3.SimulationNodeDatum {
        id: string | number;
        title: string;
        score?: number;
        isCenter: boolean;
        directors?: string[];
        cast?: string[];
        release_date?: string;
        genres?: string[];
        poster_url?: string;
    }

    interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
        source: string | GraphNode;
        target: number | string | GraphNode;
        score: number;
    }

    function normalize(s: string): string {
        return s.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, "").trim();
    }

    let searchQuery: string = '';
    let errorMessage: string = '';
    const validMoviesArray: string[] = valid_movies as string[];

    const validMovies = new Map<string,string>(validMoviesArray.map(m => [normalize(m), m]));
    
    let nodes: GraphNode[] = [];
    let links: GraphLink[] = [];
    let simulation: d3.Simulation<GraphNode, GraphLink>;
    
    let containerWidth: number;
    let containerHeight: number;

    let selectedMovie: GraphNode | null = null;

    type RequestData = {
        query: string;
    }

    async function handleSearch(): Promise<void> {
        const movie: string | undefined = validMovies.get(normalize(searchQuery));
        if (!movie) {
            errorMessage = "Movie not found in dataset.";
            return;
        }
        errorMessage = '';

        const data: RequestData = {query: movie};
        const server_response = await fetch("http://localhost:5000/api/recommend", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data)
        });

        if(!server_response.ok) {
            throw new Error(`Request failed: ${server_response.status}`);
        }

        const parsed = await server_response.json();
        const centerMovie = parsed[0];
        const recMovies = parsed.slice(1);

        nodes = [
            { 
                id: 'center', 
                title: centerMovie.title, 
                isCenter: true,
                fx: containerWidth / 2,
                fy: containerHeight / 2,
                score: centerMovie.score,
                directors: centerMovie.directors,
                cast: centerMovie.cast,
                release_date: centerMovie.release_date,
                genres: centerMovie.genres,
                poster_url: centerMovie.poster_url
            },
            ...recMovies.map((d: any) => ({
                id: d.id,
                title: d.title,
                score: d.score,
                isCenter: false,
                directors: d.directors,
                cast: d.cast,
                release_date: d.release_date,
                genres: d.genres,
                poster_url: d.poster_url
            }))
        ];

        links = recMovies.map((d: any) => ({
            source: 'center',
            target: d.id,
            score: d.score
        }));

        runSimulation();
    }

    function runSimulation(): void {
        if (simulation) simulation.stop();
        simulation = d3.forceSimulation<GraphNode, GraphLink>(nodes)
            .force('charge', d3.forceManyBody().strength(-800))
            .force('collide', d3.forceCollide().radius(100))
            .force('link', d3.forceLink<GraphNode, GraphLink>(links)
                .id(d => d.id as string)
                .distance(d => (1 - d.score) * 400 + 200)
            )
            .on('tick', () => {
                nodes.forEach(d => {
                    if (d.x !== undefined && d.y !== undefined) {
                        d.x = Math.max(60, Math.min(containerWidth - 60, d.x));
                        d.y = Math.max(90, Math.min(containerHeight - 90, d.y));
                    }
                });
                nodes = [...nodes];
                links = [...links];
            });
    }
    function openModal(node: GraphNode): void {
        if (!node.isCenter) {
            selectedMovie = node;
        }
    }

    function closeModal(): void {
        selectedMovie = null;
    }
</script>

<div class="screen-container">
    <div class="search-bar">
        <input type="text" bind:value={searchQuery} placeholder="Enter a movie..." list="movies-list" />
        <datalist id="movies-list">
            {#each validMoviesArray as movie}
                <option value={movie}></option>
            {/each}
        </datalist>
        <button on:click={handleSearch}>Search</button>
        {#if errorMessage}
            <span class="error-text">{errorMessage}</span>
        {/if}
    </div>

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
                <g 
                    transform="translate({node.x},{node.y})"
                    on:click={() => openModal(node)}
                    on:keydown={(e) => e.key === 'Enter' && openModal(node)}
                    role="button"
                    tabindex="0"
                    class:clickable={!node.isCenter}
                >
                    <clipPath id="clip-{node.id}">
                        <rect x="-60" y="-90" width="120" height="180" rx="8" />
                    </clipPath>
                    <rect 
                        x="-60" 
                        y="-90" 
                        width="120" 
                        height="180" 
                        fill={node.isCenter ? '#e2e8f0' : '#cbd5e1'} 
                        stroke="#334155"
                        stroke-width="2"
                        rx="8"
                    />
                    {#if node.poster_url}
                        <image href={node.poster_url} x="-60" y="-90" width="120" height="180" clip-path="url(#clip-{node.id})" preserveAspectRatio="xMidYMid slice" />
                    {:else}
                        <text x="0" y="-10" text-anchor="middle" font-weight="bold" font-family="sans-serif" font-size="14">
                            {node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title}
                        </text>
                    {/if}
                    {#if !node.isCenter}
                        <rect x="-25" y="70" width="50" height="20" rx="4" fill="rgba(255,255,255,0.9)" />
                        <text x="0" y="84" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#000" font-weight="bold">
                            {node.score !== undefined ? node.score.toFixed(2) : ''}
                        </text>
                    {/if}
                </g>
            {/each}
        </svg>
    </div>

    {#if selectedMovie}
        <div class="modal-backdrop" on:click|self={closeModal} on:keydown|self={(e) => e.key === 'Escape' && closeModal()} tabindex="0" role="button">
            <div class="modal-content" role="dialog" aria-modal="true">
                <button class="close-btn" on:click={closeModal} aria-label="Close modal">&times;</button>
                <h2>{selectedMovie.title}</h2>
                <div class="modal-body">
                    <p><strong>Score:</strong> {selectedMovie.score}</p>
                    {#if selectedMovie.directors && selectedMovie.directors.length > 0}
                        <p><strong>Director:</strong> {selectedMovie.directors.join(', ')}</p>
                    {/if}
                    {#if selectedMovie.release_date}
                        <p><strong>Release Date:</strong> {selectedMovie.release_date}</p>
                    {/if}
                    {#if selectedMovie.genres && selectedMovie.genres.length > 0}
                        <p><strong>Genres:</strong> {selectedMovie.genres.join(', ')}</p>
                    {/if}
                    {#if selectedMovie.cast && selectedMovie.cast.length > 0}
                        <p><strong>Cast:</strong> {selectedMovie.cast.join(', ')}</p>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>

