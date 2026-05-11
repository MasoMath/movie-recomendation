<script lang="ts">
    import valid_movies from "./assets/valid_movies.json";
    import './app.css';
    import { normalize } from './lib/utils';
    import type { GraphNode, GraphLink } from './lib/types';
    
    import SearchBar from './components/SearchBar.svelte';
    import ForceGraph from './components/ForceGraph.svelte';
    import MovieModal from './components/MovieModal.svelte';

    let errorMessage: string = '';
    let nodes: GraphNode[] = [];
    let links: GraphLink[] = [];
    let selectedMovie: GraphNode | null = null;

    const validMoviesArray: string[] = valid_movies as string[];
    const validMovies = new Map<string,string>(validMoviesArray.map(m => [normalize(m), m]));

    async function handleSearch(payload: {query: string}): Promise<void> {
        const searchQuery = payload.query;
        const movie: string | undefined = validMovies.get(normalize(searchQuery));
        
        if (!movie) {
            errorMessage = "Movie not found in dataset.";
            return;
        }
        errorMessage = '';

        try {
            const server_response = await fetch("http://localhost:5000/api/recommend", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query: movie })
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

        } catch (error) {
            errorMessage = "Failed to fetch recommendations.";
            console.error(error);
        }
    }
</script>

<div class="screen-container">
    <SearchBar {errorMessage} onsearch={handleSearch} />
    <ForceGraph {nodes} {links} onNodeClick={(node) => selectedMovie = node} />
    {#if selectedMovie}
        <MovieModal {selectedMovie} on:close={() => selectedMovie = null} />
    {/if}
</div>

