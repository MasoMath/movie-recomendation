# How Search Works

## The Big Idea

Each search box is a **voter**. When you submit, every non-empty category produces a ranked list of all 4,816 movies (a score vector). Those vectors are then blended together — each one weighted by its slider — to produce the final ranking.

```
Movies box     → score vector  ──┐ weight 0.8
Actors box     → score vector  ──┤ weight 0.5
Directors box  → score vector  ──┤ weight 0.0  (ignored, slider at 0)
Genres box     → score vector  ──┤ weight 1.0
Studios box    → score vector  ──┘ weight 0.3

Final score = weighted average of contributing vectors
```

---

## The Weight Slider

Each box has a slider from **0.0 to 1.0** (steps of 0.1). Default is 1.0.

- **0.0** — that box is completely ignored, even if it has items in it.
- **1.0** — full contribution.
- Values in between scale the contribution proportionally.

The weights are **normalized at runtime**: what matters is the ratio between sliders, not their absolute values. Setting everything to 1.0 is the same as setting everything to 0.5. What changes recommendations is making one slider *higher or lower relative to the others*.

---

## How Each Box Scores Movies

### Movies box

The most powerful input. Each movie you add looks up a **precomputed blended similarity row** from four offline matrices:

| Signal | Weight |
|---|---|
| Cast + Director (TF-IDF) | 45% |
| Production Companies (TF-IDF) | 20% |
| Keywords (SpaCy semantic) | 20% |
| Genres (SpaCy semantic) | 15% |

So "movies like Inception" doesn't just find movies with the same cast — it finds movies that share crew, studio, thematic keywords, and genre neighborhood in embedding space. If you add multiple seed movies, their rows are **averaged** before contributing to the final blend.

### Actors box

Finds all movies that contain any of the listed actors, then scores each movie by how many of those actors appear in it (averaged across the full list). It's a **presence signal** — movies with more of your selected actors score higher. No partial credit for "similar actors," just direct membership.

### Directors box

Same mechanism as Actors. Movies containing any of the listed directors score higher. Director is already baked into the Movies box signal (at 45% weight via the cast/director matrix), so this box is most useful when you want to **emphasize** a director specifically, or search by director alone without a seed movie.

### Genres box

Maps each genre to the set of movies tagged with it, then averages the presence vectors. Like Actors/Directors, this is a **direct tag match** at the movie level — not semantic. The semantic genre similarity (SpaCy embeddings) lives inside the Movies box signal, not here. Use this box when you want to hard-filter toward specific genres.

### Production Companies box

Same presence mechanism. Movies produced by any of the listed studios score higher. Useful for capturing "studio vibe" — e.g., A24, Pixar, Blumhouse — without specifying individual films.

---

## What Happens on Submit

1. Each box resolves typed names to integer indices (via preloaded JSON lookup files).
2. Frontend sends `{ items: [indices], weight: float }` per category to `POST /api/recommend`.
3. Backend computes a normalized score vector for each non-empty, non-zero-weight category.
4. Vectors are blended: `final = sum(vec × weight) / total_weight`.
5. Seed movies are excluded from results (score forced to -1).
6. Top 10 scores are returned, hydrated with title/poster/metadata, and rendered as the graph.
