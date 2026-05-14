<script lang="ts">
    import './app.css';
    import { ServerPayload, type HydratedMovie } from './lib/utils';
    import type { GraphNode, GraphLink, SearchPayload } from './lib/types';

    import SearchBar from './components/SearchBar.svelte';
    import ForceGraph from './components/ForceGraph.svelte';
    import MovieModal from './components/MovieModal.svelte';
    import InputsSummaryModal from './components/InputsSummaryModal.svelte';

    let errorMessage: string = '';
    let nodes: GraphNode[] = [];
    let links: GraphLink[] = [];
    let selectedMovie: GraphNode | null = null;

    let lastSearchPayload: SearchPayload | null = null;
    let lastInputMoviesHydrated: HydratedMovie[] = [];
    let inputsSummaryOpen = false;

    async function handleSearch(payload: SearchPayload): Promise<void> {
        errorMessage = '';

        try {
            const server_response = await fetch("http://localhost:5000/api/recommend", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload)
            });

            if(!server_response.ok) {
                throw new Error(`Request failed: ${server_response.status}`);
            }

            const parsed_json = await server_response.json();
            const zod_parsed = ServerPayload.safeParse(parsed_json);

            if(!zod_parsed.success){
                throw new Error("Zod failed to validate response structure");
            }
            
            const input_movies_hydrated = zod_parsed.data.input_movies;
            const recommended_movies_hydrated = zod_parsed.data.recommended_movies;

            lastSearchPayload = payload;
            lastInputMoviesHydrated = input_movies_hydrated;

            const centerTitle = input_movies_hydrated[0]?.title ?? 'Query';

            nodes = [
                {
                    id: 'center',
                    title: centerTitle,
                    isCenter: true,
                    score: input_movies_hydrated[0]?.score ?? 1,
                    directors: input_movies_hydrated[0]?.directors,
                    cast: input_movies_hydrated[0]?.cast,
                    release_date: input_movies_hydrated[0]?.release_date,
                    genres: input_movies_hydrated[0]?.genres,
                    production_companies: input_movies_hydrated[0]?.production_companies,
                },
                ...recommended_movies_hydrated.map((d: any) => ({
                    id: d.id,
                    title: d.title,
                    score: d.score,
                    isCenter: false,
                    directors: d.directors,
                    cast: d.cast,
                    release_date: d.release_date,
                    genres: d.genres,
                    production_companies: d.production_companies,
                    poster_url: d.poster_url
                }))
            ];

            links = recommended_movies_hydrated.map((d: any) => ({
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
    <ForceGraph
        {nodes}
        {links}
        onNodeClick={(node) => selectedMovie = node}
        onCenterClick={() => {
            if (lastSearchPayload) inputsSummaryOpen = true;
        }}
    />
    {#if selectedMovie}
        <MovieModal {selectedMovie} on:close={() => selectedMovie = null} />
    {/if}
    {#if inputsSummaryOpen && lastSearchPayload}
        <InputsSummaryModal
            payload={lastSearchPayload}
            movieInputsHydrated={lastInputMoviesHydrated}
            on:close={() => inputsSummaryOpen = false}
        />
    {/if}
</div>
