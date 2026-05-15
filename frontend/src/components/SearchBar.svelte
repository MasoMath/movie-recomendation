<script lang="ts">
    import valid_movies from "../assets/valid_movies.json";
    import valid_actors from "../assets/valid_actors.json";
    import valid_directors from "../assets/valid_directors.json";
    import valid_genres from "../assets/valid_genres.json";
    import valid_production_companies from "../assets/valid_production_companies.json";
    import { slide } from 'svelte/transition';
    import { normalize } from "../lib/utils";
    import {
        SEARCH_CATEGORY_KEYS,
        CATEGORY_DISPLAY_LABELS,
        type SearchPayload,
        type ApiSearchPayload,
        type SearchCategoryKey,
    } from "../lib/types";

    export let errorMessage: string = '';
    export let onsearch: (display: SearchPayload, api: ApiSearchPayload) => void;

    const validMoviesArray: string[] = valid_movies as string[];
    const validActorsArray: string[] = valid_actors as string[];
    const validDirectorsArray: string[] = valid_directors as string[];
    const validGenresArray: string[] = valid_genres as string[];
    const validProductionCompaniesArray: string[] = valid_production_companies as string[];

    const validArrays: Record<SearchCategoryKey, string[]> = {
        movies: validMoviesArray,
        actors: validActorsArray,
        directors: validDirectorsArray,
        genres: validGenresArray,
        production_companies: validProductionCompaniesArray,
    };

    const indexMaps: Record<SearchCategoryKey, Map<string, number>> = {
        movies: new Map(validMoviesArray.map((m, i) => [normalize(m), i])),
        actors: new Map(validActorsArray.map((a, i) => [normalize(a), i])),
        directors: new Map(validDirectorsArray.map((d, i) => [normalize(d), i])),
        genres: new Map(validGenresArray.map((g, i) => [normalize(g), i])),
        production_companies: new Map(validProductionCompaniesArray.map((c, i) => [normalize(c), i])),
    };

    function categoryLabel(category: SearchCategoryKey): string {
        return CATEGORY_DISPLAY_LABELS[category];
    }

    let isCollapsed = false;
    let openCategories = new Set<SearchCategoryKey>(['movies']);

    function toggleCategory(cat: SearchCategoryKey) {
        if (openCategories.has(cat)) {
            openCategories.delete(cat);
        } else {
            openCategories.add(cat);
        }
        openCategories = openCategories;
    }

    let searchData: Record<
        SearchCategoryKey,
        { items: number[]; weight: number; currentInput: string }
    > = {
        movies: { items: [], weight: 1.0, currentInput: '' },
        actors: { items: [], weight: 1.0, currentInput: '' },
        directors: { items: [], weight: 1.0, currentInput: '' },
        genres: { items: [], weight: 1.0, currentInput: '' },
        production_companies: { items: [], weight: 1.0, currentInput: '' },
    };

    const categories = SEARCH_CATEGORY_KEYS;

    function addItem(category: SearchCategoryKey) {
        const rawInput = searchData[category].currentInput.trim();
        if (!rawInput) return;

        const idx = indexMaps[category].get(normalize(rawInput));

        if (idx !== undefined) {
            if (!searchData[category].items.includes(idx)) {
                searchData[category].items = [...searchData[category].items, idx];
            }
            searchData[category].currentInput = '';
            errorMessage = '';
        } else {
            errorMessage = `"${rawInput}" not found in ${categoryLabel(category)} list.`;
        }
    }

    function handleKeydown(event: KeyboardEvent, category: SearchCategoryKey) {
        if (event.key === 'Enter') {
            event.preventDefault();
            addItem(category);
        }
    }

    function removeItem(category: SearchCategoryKey, index: number) {
        searchData[category].items = searchData[category].items.filter((_, i) => i !== index);
    }

    function submitSearch() {
        categories.forEach(c => {
            if (searchData[c].currentInput.trim()) {
                addItem(c);
            }
        });

        if (!categories.some(c => searchData[c].items.length > 0)) {
            errorMessage = 'Please add at least one search item.';
            return;
        }

        isCollapsed = true;

        if (onsearch) {
            const displayPayload: SearchPayload = {
                movies: { items: searchData.movies.items.map(i => validArrays.movies[i]), weight: searchData.movies.weight },
                actors: { items: searchData.actors.items.map(i => validArrays.actors[i]), weight: searchData.actors.weight },
                directors: { items: searchData.directors.items.map(i => validArrays.directors[i]), weight: searchData.directors.weight },
                genres: { items: searchData.genres.items.map(i => validArrays.genres[i]), weight: searchData.genres.weight },
                production_companies: { items: searchData.production_companies.items.map(i => validArrays.production_companies[i]), weight: searchData.production_companies.weight },
            };
            const apiPayload: ApiSearchPayload = {
                movies: { items: searchData.movies.items, weight: searchData.movies.weight },
                actors: { items: searchData.actors.items, weight: searchData.actors.weight },
                directors: { items: searchData.directors.items, weight: searchData.directors.weight },
                genres: { items: searchData.genres.items, weight: searchData.genres.weight },
                production_companies: { items: searchData.production_companies.items, weight: searchData.production_companies.weight },
            };
            onsearch(displayPayload, apiPayload);
        }
    }
</script>

<div class="search-panel {isCollapsed ? 'collapsed' : ''}">
    <h2>Query Parameters</h2>
    <div class="categories">
        {#each categories as category}
            <div class="category-block">
                <button class="category-header" on:click={() => toggleCategory(category)}>
                    <span>{categoryLabel(category)}</span>
                    <div class="header-right">
                        {#if searchData[category].items.length > 0}
                            <span class="item-count">{searchData[category].items.length}</span>
                        {/if}
                        <span class="chevron" class:open={openCategories.has(category)}>▾</span>
                    </div>
                </button>
                {#if openCategories.has(category)}
                    <div class="category-content" transition:slide={{ duration: 150 }}>
                        <div class="weight-row">
                            <label for="{category}-weight" class="weight-label">Weight</label>
                            <input id="{category}-weight" type="range" min="0.1" max="1" step="0.1" bind:value={searchData[category].weight} />
                            <span class="weight-val">{searchData[category].weight}</span>
                        </div>
                        <div class="input-row">
                            <label for="{category}-input" class="sr-only">Add {categoryLabel(category)}</label>
                            <input
                                id="{category}-input"
                                type="text"
                                bind:value={searchData[category].currentInput}
                                on:keydown={(e) => handleKeydown(e, category)}
                                placeholder={`Add ${categoryLabel(category).toLowerCase()}...`}
                                list="{category}-list"
                            />
                            <button class="add-btn" on:click={() => addItem(category)}>+</button>
                        </div>
                        <div class="tags">
                            {#each searchData[category].items as itemIdx, i}
                                <span class="tag">
                                    {validArrays[category][itemIdx]}
                                    <button class="remove-btn" on:click={() => removeItem(category, i)}>×</button>
                                </span>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
    <button class="search-btn" on:click={submitSearch}>Generate Recommendations</button>
    {#if errorMessage}
        <span class="error-text">{errorMessage}</span>
    {/if}
</div>

<datalist id="movies-list">
    {#each validMoviesArray as item}
        <option value={item}></option>
    {/each}
</datalist>

<datalist id="actors-list">
    {#each validActorsArray as item}
        <option value={item}></option>
    {/each}
</datalist>

<datalist id="directors-list">
    {#each validDirectorsArray as item}
        <option value={item}></option>
    {/each}
</datalist>

<datalist id="genres-list">
    {#each validGenresArray as item}
        <option value={item}></option>
    {/each}
</datalist>

<datalist id="production_companies-list">
    {#each validProductionCompaniesArray as item}
        <option value={item}></option>
    {/each}
</datalist>

<style>
.search-panel {
    box-sizing: border-box;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    background-color: #141414;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.9);
    border: 2px solid #8b0000;
    border-radius: 12px;
    padding: 30px;
    z-index: 100;
    transition: all 0.5s ease;
    display: flex;
    flex-direction: column;
    gap: 20px;
    max-height: 90vh;
    overflow-y: auto;
}

.search-panel.collapsed {
    top: 0;
    left: 0;
    transform: none;
    width: 350px;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
    border: none;
    border-right: 2px solid #8b0000;
    padding: 16px;
    gap: 10px;
    overflow-y: hidden;
}

.search-panel.collapsed .categories {
    flex: 1;
    min-height: 0;
    gap: 6px;
    overflow: visible;
}

.search-panel.collapsed .search-btn {
    flex-shrink: 0;
    padding: 12px;
    font-size: 16px;
    margin-top: 0;
}

h2 {
    color: #fff;
    margin: 0;
    text-align: center;
    font-family: sans-serif;
}

.categories {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.category-block {
    background-color: #222;
    border-radius: 8px;
    border: 1px solid #444;
    overflow: hidden;
}

.category-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: none;
    border: none;
    color: #fff;
    font-weight: bold;
    font-size: 15px;
    cursor: pointer;
    text-align: left;
}

.category-header:hover {
    background-color: #2a2a2a;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

.item-count {
    background-color: #8b0000;
    color: #fff;
    font-size: 11px;
    font-weight: bold;
    padding: 1px 6px;
    border-radius: 10px;
    min-width: 18px;
    text-align: center;
}

.chevron {
    font-size: 16px;
    transition: transform 0.15s;
    display: inline-block;
    transform: rotate(-90deg);
}

.chevron.open {
    transform: rotate(0deg);
}

.category-content {
    padding: 0 14px 12px;
    border-top: 1px solid #333;
}

.weight-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    padding-top: 10px;
}

.weight-label {
    color: #aaa;
    font-size: 13px;
    flex-shrink: 0;
}

.weight-val {
    color: #fff;
    font-size: 13px;
    min-width: 24px;
}

.input-row {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}

input[type="text"] {
    flex-grow: 1;
    padding: 8px;
    background-color: #111;
    color: #fff;
    border: 1px solid #555;
    border-radius: 4px;
    font-size: 1rem;
}

input[type="text"]:focus {
    outline: none;
    border-color: #8b0000;
}

.add-btn {
    background-color: #444;
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 0 15px;
    cursor: pointer;
    font-weight: bold;
}

.add-btn:hover {
    background-color: #666;
}

.tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.tag {
    background-color: #8b0000;
    color: #fff;
    padding: 5px 10px;
    border-radius: 12px;
    font-size: 15px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.remove-btn {
    background: none;
    border: none;
    color: #fff;
    cursor: pointer;
    padding: 0;
    font-weight: bold;
    font-size: 16px;
    line-height: 1;
}

.remove-btn:hover {
    color: #fff;
}

.search-btn {
    background-color: #8b0000;
    color: #fff;
    border: none;
    padding: 16px;
    font-size: 20px;
    font-weight: bold;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
    margin-top: 10px;
}

.search-btn:hover {
    background-color: #a50000;
}


.error-text {
    color: #ff4d4d;
    text-align: center;
    font-weight: bold;
}

input[type="range"] {
    accent-color: #8b0000;
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
</style>


