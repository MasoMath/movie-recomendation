<script lang="ts">
    import { onMount } from 'svelte';
    import * as d3 from 'd3';
    import valid_movies from "./assets/valid_movies.json";

    interface GraphNode extends d3.SimulationNodeDatum {
        id: string | number;
        title: string;
        score?: number;
        isCenter: boolean;
        director?: string;
        actors?: string[];
        release_date?: string;
    }

    interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
        source: string | GraphNode;
        target: number | string | GraphNode;
        score: number;
    }

    let searchQuery: string = '';
    let errorMessage: string = '';
    const validMoviesArray: string[] = valid_movies as string[];
    let validMovies = new Set(validMoviesArray);
    
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
        if (!validMovies.has(searchQuery)) {
            errorMessage = "Movie not found in dataset.";
            return;
        }
        errorMessage = '';

        const mockData = [
            { id: 1, title: 'Star Wars: Episode III', score: 0.95, director: 'George Lucas', actors: ['Ewan McGregor', 'Natalie Portman', 'Hayden Christensen'], release_date: '2005-05-19' },
            { id: 2, title: 'Mr. & Mrs. Smith', score: 0.88, director: 'Doug Liman', actors: ['Brad Pitt', 'Angelina Jolie', 'Vince Vaughn'], release_date: '2005-06-07' },
            { id: 3, title: 'The Dark Knight', score: 0.76, director: 'Christopher Nolan', actors: ['Christian Bale', 'Heath Ledger', 'Aaron Eckhart'], release_date: '2008-07-18' },
            { id: 4, title: 'Dune', score: 0.50, director: 'Denis Villeneuve', actors: ['Timothée Chalamet', 'Rebecca Ferguson', 'Oscar Isaac'], release_date: '2021-10-22' },
            { id: 5, title: 'Star Wars: Episode III', score: 0.94 },
            { id: 6, title: 'Star Wars: Episode III', score: 0.90 },
            { id: 7, title: 'Star Wars: Episode III', score: 0.99 },
            { id: 8, title: 'Star Wars: Episode III', score: 0.93 },
        ];

        nodes = [
            { 
                id: 'center', 
                title: searchQuery, 
                isCenter: true,
                fx: containerWidth / 2,
                fy: containerHeight / 2
            },
            ...mockData.map(d => ({ ...d, isCenter: false }))
        ];
        
        links = mockData.map(d => ({
            source: 'center',
            target: d.id,
            score: d.score
        }));

        const data: RequestData = {query: searchQuery}
        const server_response = await fetch("http://localhost:5000/api/recommend", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data)
        });

        if(!server_response.ok)
        {
            throw new Error(`Request failed :( : ${server_response.status}`);
        }
        if(server_response.ok)
        {
            console.log(server_response);
        }
        
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
                    <text x="0" y="-10" text-anchor="middle" font-weight="bold" font-family="sans-serif" font-size="14">
                        {node.title}
                    </text>
                    {#if !node.isCenter}
                        <text x="0" y="15" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#475569">
                            Score: {node.score}
                        </text>
                    {/if}
                </g>
            {/each}
        </svg>
    </div>

    {#if selectedMovie}
        <div class="modal-backdrop" on:click|self={closeModal} on:keydown|self={(e) => e.key === 'Escape' && closeModal()} tabindex="0" role="button">
            <div class="modal-content" role="document">
                <button class="close-btn" on:click={closeModal}>&times;</button>
                <h2>{selectedMovie.title}</h2>
                <div class="modal-body">
                    <p><strong>Score:</strong> {selectedMovie.score}</p>
                    {#if selectedMovie.director}
                        <p><strong>Director:</strong> {selectedMovie.director}</p>
                    {/if}
                    {#if selectedMovie.release_date}
                        <p><strong>Release Date:</strong> {selectedMovie.release_date}</p>
                    {/if}
                    {#if selectedMovie.actors}
                        <p><strong>Cast:</strong> {selectedMovie.actors.join(', ')}</p>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
    }
    .screen-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        width: 100vw;
        font-family: sans-serif;
        position: relative;
    }
    .search-bar {
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 10;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
    }
    input {
        padding: 8px;
        font-size: 16px;
        width: 300px;
    }
    button {
        padding: 8px 16px;
        font-size: 16px;
        cursor: pointer;
    }
    .error-text {
        color: #ef4444;
        font-weight: bold;
        margin-left: 10px;
    }
    .canvas-container {
        flex-grow: 1;
        width: 100%;
        height: 100%;
        background-color: #f8fafc;
    }
    svg {
        display: block;
    }
    .clickable {
        cursor: pointer;
        transition: transform 0.2s;
    }
    .clickable:hover rect {
        fill: #94a3b8;
    }
    .modal-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 50;
    }
    .modal-content {
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        width: 400px;
        max-width: 90%;
        position: relative;
    }
    .close-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
    }
    .modal-body {
        margin-top: 20px;
    }
    .modal-body p {
        margin: 8px 0;
    }
</style>

