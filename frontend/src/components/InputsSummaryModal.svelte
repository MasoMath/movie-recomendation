<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { SearchPayload } from '../lib/types';
    import { SEARCH_CATEGORY_KEYS, CATEGORY_DISPLAY_LABELS } from '../lib/types';
    import type { HydratedMovie } from '../lib/utils';

    export let payload: SearchPayload;
    export let movieInputsHydrated: HydratedMovie[];

    const dispatch = createEventDispatcher();

    function closeModal() {
        dispatch('close');
    }
</script>

<div
    class="modal-backdrop"
    on:click|self={closeModal}
    on:keydown|self={(e) => e.key === 'Escape' && closeModal()}
    tabindex="0"
    role="button"
>
    <div class="modal-content" role="dialog" aria-modal="true">
        <button class="close-btn" on:click={closeModal} aria-label="Close modal">&times;</button>
        <h2>Your query</h2>
        <p class="subtitle">Weights and selections from your last search</p>
        <div class="modal-body">
            {#each SEARCH_CATEGORY_KEYS as key}
                {@const cat = payload[key]}
                <section class="category-section">
                    <h3>
                        {CATEGORY_DISPLAY_LABELS[key]}
                        <span class="weight">weight: {cat.weight}</span>
                    </h3>
                    {#if key === 'movies'}
                        {#if cat.items.length === 0}
                            <p class="empty">No movies selected</p>
                        {:else}
                            <ul class="movie-list">
                                {#each cat.items as title, i}
                                    <li class="movie-row">
                                        <div class="poster-wrap">
                                            {#if movieInputsHydrated[i]?.poster_url}
                                                <img
                                                    src={movieInputsHydrated[i].poster_url}
                                                    alt=""
                                                    class="poster"
                                                />
                                            {:else}
                                                <div class="poster poster-placeholder"></div>
                                            {/if}
                                        </div>
                                        <span class="item-title">{title}</span>
                                    </li>
                                {/each}
                            </ul>
                        {/if}
                    {:else if cat.items.length === 0}
                        <p class="empty">No items</p>
                    {:else}
                        <ul class="plain-list">
                            {#each cat.items as item}
                                <li>{item}</li>
                            {/each}
                        </ul>
                    {/if}
                </section>
            {/each}
        </div>
    </div>
</div>

<style>
    .modal-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.85);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 60;
    }

    .modal-content {
        background-color: #1a1a1a;
        color: #e5e5e5;
        padding: 28px 30px 32px;
        border-radius: 8px;
        border: 1px solid #8b0000;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.9);
        width: min(520px, 92vw);
        max-height: 88vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    h2 {
        margin: 0;
        color: #fff;
        font-size: 1.5rem;
    }

    .subtitle {
        margin: 6px 0 0;
        font-size: 1rem;
        color: #94a3b8;
    }

    .close-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 24px;
        color: #8b0000;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }

    .close-btn:hover {
        color: #ff4d4d;
    }

    .modal-body {
        margin-top: 18px;
        overflow-y: auto;
        padding-right: 6px;
        display: flex;
        flex-direction: column;
        gap: 18px;
    }

    .category-section h3 {
        margin: 0 0 8px;
        font-size: 1.1rem;
        color: #c9a96e;
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 8px;
    }

    .weight {
        font-size: 0.95rem;
        font-weight: normal;
        color: #cbd5e1;
    }

    .empty {
        margin: 0;
        font-size: 1rem;
        color: #64748b;
    }

    .plain-list {
        margin: 0;
        padding-left: 1.2rem;
        color: #e5e5e5;
    }

    .plain-list li {
        margin: 4px 0;
    }

    .movie-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .movie-row {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #222;
        border-radius: 8px;
        padding: 8px 10px;
        border: 1px solid #333;
    }

    .poster-wrap {
        flex-shrink: 0;
    }

    .poster {
        width: 48px;
        height: 72px;
        object-fit: cover;
        border-radius: 4px;
        display: block;
    }

    .poster-placeholder {
        background: #0f172a;
        border: 1px dashed #475569;
    }

    .item-title {
        font-size: 0.95rem;
    }
</style>
