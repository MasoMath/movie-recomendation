<script lang="ts">
    import valid_movies from "../assets/valid_movies.json";
    export let errorMessage: string = '';
    export let onsearch: (payload: { query: string }) => void;

    const validMoviesArray: string[] = valid_movies as string[];

    let isCollapsed = false;

    let searchData = {
        movies: { items: [] as string[], weight: 1.0, currentInput: '' },
        actors: { items: [] as string[], weight: 1.0, currentInput: '' },
        directors: { items: [] as string[], weight: 1.0, currentInput: '' },
        genres: { items: [] as string[], weight: 1.0, currentInput: '' },
    };

    type SearchCategoryKey = keyof typeof searchData;
    const categories: SearchCategoryKey[] = ['movies', 'actors', 'directors', 'genres'];

    function addItem(category: SearchCategoryKey) {
        const input = searchData[category].currentInput.trim();
        if (input && !searchData[category].items.includes(input)) {
            searchData[category].items = [...searchData[category].items, input];
            searchData[category].currentInput = '';
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
        isCollapsed = true;
        const query = searchData.movies.items[0] || searchData.movies.currentInput || '';
        if (onsearch) {
            onsearch({ query });
        }
    }
</script>

<div class="search-panel {isCollapsed ? 'collapsed' : ''}">
    <h2>Query Parameters</h2>
    <div class="categories">
        {#each categories as category}
            <div class="category-block">
                <div class="header-row">
                    <label for="{category}-weight">{category.charAt(0).toUpperCase() + category.slice(1)}</label>
                    <input id="{category}-weight" type="range" min="0" max="1" step="0.1" bind:value={searchData[category].weight} title="Weight" />
                    <span class="weight-val">{searchData[category].weight}</span>
                </div>
                <div class="input-row">
                    <label for="{category}-input" class="sr-only">Add {category}</label>
                    <input
                        id="{category}-input"
                        type="text"
                        bind:value={searchData[category].currentInput}
                        on:keydown={(e) => handleKeydown(e, category)}
                        placeholder={`Add ${category}...`}
                        list={category === 'movies' ? "movies-list" : null}
                    />
                    <button class="add-btn" on:click={() => addItem(category)}>+</button>
                </div>
                <div class="tags">
                    {#each searchData[category].items as item, i}
                        <span class="tag">
                            {item}
                            <button class="remove-btn" on:click={() => removeItem(category, i)}>×</button>
                        </span>
                    {/each}
                </div>
            </div>
        {/each}
    </div>
    <button class="search-btn" on:click={submitSearch}>Generate Recommendations</button>
    {#if errorMessage}
        <span class="error-text">{errorMessage}</span>
    {/if}
</div>
<datalist id="movies-list">
    {#each validMoviesArray as movie}
        <option value={movie}></option>
    {/each}
</datalist>

<style>
.search-panel {
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
    padding: 20px;
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
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #444;
}

.header-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.header-row label {
    color: #fff;
    font-weight: bold;
    flex-grow: 1;
    text-transform: capitalize;
}

.weight-val {
    color: #ffd700;
    font-size: 14px;
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
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 14px;
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
    color: #ffd700;
}

.search-btn {
    background-color: #8b0000;
    color: #ffd700;
    border: none;
    padding: 15px;
    font-size: 18px;
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
