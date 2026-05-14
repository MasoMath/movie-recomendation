<script lang="ts">
    import type { GraphNode } from '../lib/types';
    import { createEventDispatcher } from 'svelte';

    export let selectedMovie: GraphNode;
    
    const dispatch = createEventDispatcher();

    function closeModal() {
        dispatch('close');
    }

    $: companies = selectedMovie.production_companies ?? [];
    $: companiesLabel = companies.length === 1 ? 'Production company' : 'Production companies';
    $: companiesText = companies.length > 0 ? companies.join(', ') : 'Not listed in dataset';
</script>

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
            <p><strong>{companiesLabel}:</strong> {companiesText}</p>
            {#if selectedMovie.genres && selectedMovie.genres.length > 0}
                <p><strong>Genres:</strong> {selectedMovie.genres.join(', ')}</p>
            {/if}
            {#if selectedMovie.cast && selectedMovie.cast.length > 0}
                <div class="cast-section">
                    <strong>Cast</strong>
                    <ul class="cast-list">
                        {#each selectedMovie.cast as actor}
                            <li>{actor}</li>
                        {/each}
                    </ul>
                </div>
            {/if}
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
  z-index: 50;
}

.modal-content {
  background-color: #1a1a1a;
  color: #e5e5e5;
  padding: 30px;
  border-radius: 8px;
  border: 1px solid #8b0000;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.9);
  width: 400px;
  max-width: 90%;
  max-height: 85vh;
  position: relative;
  display: flex;
  flex-direction: column;
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
}

.close-btn:hover {
  color: #ff4d4d;
}

.modal-body {
  margin-top: 20px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.modal-body p {
  margin: 8px 0;
}

.modal-body strong {
  color: #c9a96e;
}

.cast-section {
  margin: 8px 0;
}

.cast-section strong {
  color: #c9a96e;
}

.cast-list {
  margin: 6px 0 0 0;
  padding-left: 1.2rem;
  max-height: 140px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cast-list li {
  font-size: 1rem;
  color: #e5e5e5;
}
</style>
