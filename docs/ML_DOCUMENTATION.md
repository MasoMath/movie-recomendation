# ML Evaluation & Similarity Functions — TMDB Movie Recommender

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Pipeline — `MovieData.py`](#2-data-pipeline--moviedatapy)
3. [Similarity Functions — `similarity.py`](#3-similarity-functions--similaritypy)
4. [Backend Inference Pipeline — `backend/helpers.py`](#4-backend-inference-pipeline--backendhelperspy)
5. [Recommendation Algorithms](#5-recommendation-algorithms)
6. [Precomputed Similarity Matrices](#6-precomputed-similarity-matrices)
7. [Matrix Generation (ml_dev.ipynb)](#7-matrix-generation-ml_devipynb)
8. [Data Contracts](#8-data-contracts)
9. [Evaluation Status](#9-evaluation-status)
10. [Scalability & Performance](#10-scalability--performance)

---

## 1. Architecture Overview

Content-based collaborative filtering across 4,816 TMDB movies. All similarity computation is **offline** — the server loads precomputed matrices at startup and blends four signals per request.

| Signal | Weight | Algorithm |
|---|---|---|
| Cast + Director | 45% | ECLAT TF-IDF cosine |
| Production Companies | 20% | ECLAT TF-IDF cosine |
| Keywords | 20% | SpaCy embedding cosine (lifted) |
| Genres | 15% | SpaCy embedding cosine (lifted) |

**Inference cost per request:** one row slice per seed movie, weighted average, argpartition for top-k. Runtime is O(k log n).

---

## 2. Data Pipeline — `MovieData.py`

### `MovieData.__init__`

```python
MovieData(
    path_to_movie: str = './kaggledata/tmdb_5000_movies.csv',
    path_to_credits: str = './kaggledata/tmdb_5000_credits.csv'
)
```

Loads, cleans, and merges both TMDB CSVs into a single 4,816-row DataFrame.

**Cleaning steps:**

| Step | Method | Columns affected |
|---|---|---|
| Parse JSON-like strings → int ID lists | `_clean_dataframe()` | `genres`, `keywords`, `production_companies` |
| Parse JSON with ISO codes | `_clean_dataframe_multi_id()` | `production_countries`, `spoken_languages` |
| Filter crew to Director only | `_clean_director()` | `crew` |
| Preserve numeric columns as-is | — | `id`, `budget`, `popularity`, `revenue`, `runtime`, `vote_average`, `vote_count` |

**Output schema (selected columns):**

| Column | Type | Notes |
|---|---|---|
| `id` | int | TMDB movie ID |
| `original_title` | str | |
| `genres` | list[int] | Genre IDs (14 unique) |
| `keywords` | list[int] | Keyword IDs (9,813 unique) |
| `cast` | list[int] | Actor IDs |
| `crew` | list[int] | Director IDs only |
| `production_companies` | list[int] | Studio IDs |
| `vote_average` | float | |

### Static Helpers

#### `_clean_dataframe(df, col_names, id='id') -> tuple[pd.DataFrame, dict]`

Parses JSON-encoded columns into flat lists of integer IDs. Returns the cleaned DataFrame and an `id → name` lookup dict.

#### `_clean_dataframe_multi_id(df, col_names, keys) -> tuple[pd.DataFrame, dict]`

Variant for columns with multiple identifier fields (e.g., ISO codes + numeric ID).

#### `_clean_director(df, col_names) -> tuple[pd.DataFrame, dict]`

Filters the `crew` column to only rows where `job == "Director"`, then flattens to ID lists.

### Public Getters

| Method | Returns | Notes |
|---|---|---|
| `get_data()` | `pd.DataFrame` | Full cleaned dataset |
| `get_genres()` | `np.ndarray[str]` | 14 genre names, int-indexed |
| `get_keywords()` | `np.ndarray[str]` | 9,813 keyword names |
| `get_actors()` | `np.ndarray[str]` | All actor names |
| `get_directors()` | `np.ndarray[str]` | All director names |
| `get_prod_companies()` | `np.ndarray[str]` | All studio names |
| `get_col(col: str)` | `pd.Series` | Arbitrary column by name |
| `find_movies(movies)` | `pd.DataFrame` | Subset by title string(s) or positional index(es) |
| `entry_as_list(col_name, row_num)` | `list \| Series` | Single cell as a list |
| `save_csv(file_path)` | `None` | Persist cleaned data |

---

## 3. Similarity Functions — `similarity.py`

### 3.1 Semantic Similarity (Genres & Keywords)

#### `id_semantic_similarity` — lines 12–48

```python
def id_semantic_similarity(
    attr1: list[int],
    attr_series: pd.Series,
    similarity_matrix: np.ndarray,
    row2: int | None = None
) -> float | list[float]
```

Low-level building block. Given the attribute IDs for one item and the precomputed attribute-level similarity matrix, computes the mean pairwise similarity between `attr1` and either one other item (`row2`) or all items.

**Algorithm:**
1. Index the similarity matrix rows by `attr1` and columns by `attr_series[row2]` (or all rows in `attr_series`).
2. Extract the resulting sub-matrix.
3. Return the mean of all values in that sub-matrix.

**Returns:** `np.nan` if either attribute list is empty.

---

#### `semantic_similarity` — lines 51–99

```python
def semantic_similarity(
    ids: int | list[int],
    row2: int | None = None,
    attribute: str = 'genres',
    similarity_matrix: np.ndarray | None = None,
    moviedata: MovieData | None = None
) -> float | list[float] | list[list[float]]
```

Movie-level wrapper around `id_semantic_similarity`. Accepts one or more movie positional indices and delegates to the attribute-level function.

**Parameters:**

| Param | Type | Description |
|---|---|---|
| `ids` | `int \| list[int]` | Positional index/indices of seed movie(s) |
| `row2` | `int \| None` | Target movie index, or `None` for all movies |
| `attribute` | `str` | `'genres'` or `'keywords'` |
| `similarity_matrix` | `np.ndarray \| None` | Auto-loaded from disk if `None` |
| `moviedata` | `MovieData \| None` | Auto-instantiated if `None` |

**Matrix paths auto-loaded:**

| attribute | File |
|---|---|
| `'genres'` | `similarity_matrices/genre.csv` (14 × 14) |
| `'keywords'` | `similarity_matrices/keywords.csv` (9,813 × 9,813) |

**Returns:** Single float when `row2` is int; list of floats when `row2` is None. Singleton dimensions are squeezed.

---

#### `semantic_similarity_plot` — lines 130–192

```python
def semantic_similarity_plot(
    row1: int,
    row2: int,
    attribute: str = 'genres',
    similarity_matrix: np.ndarray | None = None,
    moviedata: MovieData | None = None,
    savepath: str | None = None
) -> None
```

Visualization helper. Renders a heatmap of the attribute-level sub-matrix for two specific movies, annotated with genre/keyword names. Saves to `savepath` if provided.

---

### 3.2 Cast & Director Similarity

#### `cast_director_similarity` — lines 102–127

```python
def cast_director_similarity(
    row1: int,
    row2: int | None = None,
    similarity_matrix: np.ndarray | None = None,
    moviedata: MovieData | None = None
) -> float | pd.Series
```

Thin wrapper over the precomputed 4,816 × 4,816 cast/director matrix. Returns the similarity between `row1` and either one specific movie or all movies.

**Matrix auto-loaded from:** `similarity_matrices/cast_director.npy`

**Returns:**
- `float` if `row2` is int
- `pd.Series` (positionally indexed, length 4,816) if `row2` is None

---

### 3.3 Boolean Presence Functions

#### `individual_similarity` — lines 194–224

```python
def individual_similarity(
    ids: int | list[int],
    row: int | None = None,
    col_name: str = 'crew',
    moviedata: MovieData | None = None
) -> bool | np.ndarray[bool]
```

Checks whether specific person/attribute IDs appear in a column. Uses set intersection (non-disjoint test).

**Returns:**
- `bool` if `row` is provided
- `np.ndarray[bool]` of length 4,816 if `row` is None

---

#### `categorical_similarity` — lines 226–249

```python
def categorical_similarity(
    row1: int,
    row2: int | None = None,
    col_name: str = 'crew',
    moviedata: MovieData | None = None
) -> bool | np.ndarray[bool]
```

Convenience wrapper: extracts IDs from `row1` first, then calls `individual_similarity`. Compares one movie's cast/crew against all others.

---

### 3.4 Stub Functions (Not Implemented)

#### `continuous_similarity` — lines 252–258

```python
def continuous_similarity(
    row1: int,
    row2: int | None = None,
    attribute: str = 'cost',
    moviedata: MovieData | None = None
) -> np.ndarray
```

Intended for numeric features (budget, runtime, etc.). Currently a TODO stub.

---

#### `aggregate_similarity` — lines 260–272

```python
def aggregate_similarity(
    weights: np.ndarray | None = None,
    moviedata: MovieData | None = None,
    DEV_WEIGHTS_SIZE: int = 3,
    DEV_DUMMY_DATA: np.ndarray | None = None
) -> np.ndarray
```

Earlier prototype for weighted signal aggregation. Superseded by `send_input_to_model()` in `backend/helpers.py`.

---

## 4. Backend Inference Pipeline — `backend/helpers.py`

### 4.1 Startup Initialization — lines 198–239

On server start, the module-level initialization:

1. Instantiates `MovieData` and caches it.
2. Extracts lookup arrays: `genres_arr`, `actors_arr`, `directors_arr`, `production_companies_arr`.
3. Loads all four precomputed `.npy` matrices into memory.
4. **Mean-centers** the two dense (SpaCy-derived) matrices:

```python
genre_movie_matrix    -= genre_movie_matrix.mean(axis=1, keepdims=True)
keywords_movie_matrix -= keywords_movie_matrix.mean(axis=1, keepdims=True)
```

5. Builds inverted indices for fast attribute → movie lookup: `_actor_index`, `_director_index`, `_genre_index`, `_company_index`.
6. Optionally loads attribute-level `genre.csv` and `keywords.csv` if available.

**Why mean-centering?** SpaCy cosine similarities have a ~0.4 baseline floor — any two unrelated movies score ~0.4 on genres/keywords. Mean-centering converts absolute similarity to a signed deviation (above/below this movie's average), improving discriminative power without changing within-row ranking.

---

### 4.2 Blending Weights — lines 99–104

```python
SIMILARITY_WEIGHTS = {
    'cast_director':        0.45,
    'production_companies': 0.20,
    'keyword':              0.20,
    'genre':                0.15,
}
```

These weights apply inside `_movie_sim_vector()`. The user-facing weights in `send_input_to_model()` are separate and normalized at runtime.

---

### 4.3 Internal Helper Functions

#### `_build_index(col: str) -> dict[int, list[int]]` — lines 106–113

Inverts a DataFrame column: maps each attribute ID to the list of movie positional indices that contain it.

```
genre_id → [movie_pos_0, movie_pos_17, movie_pos_42, ...]
```

---

#### `_minmax_normalize(v: np.ndarray) -> np.ndarray` — lines 127–129

Min-max scales a vector to [0, 1]. Returns a zero vector if all values are equal (zero range).

---

#### `_movie_sim_vector(pos: int) -> np.ndarray | None` — lines 131–139

Core blending function for a single seed movie. Returns a length-4,816 vector.

**Steps:**
1. Slice row `pos` from each of the four precomputed matrices.
2. Min-max normalize each row vector independently.
3. Compute the weighted sum using `SIMILARITY_WEIGHTS`.
4. Returns `None` if `pos` is out of bounds.

---

#### `_presence_vector(item_indices: list[int], lookup: dict[int, list[int]]) -> np.ndarray | None` — lines 141–149

For actor/director/genre/studio inputs (not movie inputs). Builds a presence signal:
1. For each item index in `item_indices`, look up which movies contain it via the inverted index.
2. One-hot encode each result as a length-4,816 vector.
3. Return the mean across all items.

Returns `None` if the item list is empty or none map to known movies.

---

#### `_category_vector(category: Category, lookup: dict | None) -> np.ndarray | None` — lines 151–159

Routes dispatch:
- If `lookup` is `None` → category is movies; averages `_movie_sim_vector()` results for each seed.
- If `lookup` is provided → category is actors/directors/genres/studios; calls `_presence_vector()`.

Min-max normalizes the result before returning.

---

#### `_exclude_movies(scores: np.ndarray, positions: list[int]) -> None` — lines 122–125

Sets the scores at the given positional indices to `-1.0` in-place. Prevents seed movies from appearing in their own recommendations.

---

#### `_top_k(scores: np.ndarray, k: int) -> list[MovieIdAndScore]` — lines 115–120

Uses `np.argpartition` (O(n)) to find the top-k indices, then sorts only those k elements. Converts positional indices to TMDB movie IDs via the `MovieData` lookup and returns `list[MovieIdAndScore]`.

---

### 4.4 Hydration Helpers

#### `hydrate_recommended_movies(recs: list[MovieIdAndScore]) -> list[HydratedMovie]`

Fetches title, genres, cast, directors, production companies, and poster URL for each recommended movie.

#### `hydrate_input_movies(input_movie_indices: list[int]) -> list[HydratedMovie]`

Same hydration but for the seed movies sent by the frontend.

#### `get_movie_poster_url(movie_id: int, tmdb_api_key: str) -> str | None`

Calls the TMDB API to resolve a poster image path. Returns `None` on failure.

---

## 5. Recommendation Algorithms

### 5.1 Single-Movie Recommendation — `blended_recommend`

**File:** `backend/helpers.py` lines 164–169

```python
def blended_recommend(
    movie_pos: int,
    k: int = NUM_RECOMMENDATIONS
) -> list[MovieIdAndScore]
```

Simplified entry point for a single seed movie.

**Steps:**
1. Call `_movie_sim_vector(movie_pos)` → weighted blend of all four signals.
2. `_exclude_movies(sims, [movie_pos])` → set self-score to -1.
3. `_top_k(sims, k)` → return top-k results.

---

### 5.2 Multi-Category Recommendation — `send_input_to_model`

**File:** `backend/helpers.py` lines 171–189

```python
def send_input_to_model(
    movie_input: InputFormatted,
    k: int = NUM_RECOMMENDATIONS
) -> list[MovieIdAndScore]
```

Full multi-signal recommendation supporting arbitrary combinations of movies, actors, directors, genres, and studios with user-specified per-category weights.

**Algorithm:**

```
for each category in [movies, actors, directors, genres, production_companies]:
    vec = _category_vector(category, lookup)      # length-4816 signal vector
    if vec is not None:
        contributions.append((vec, category.weight))

total_weight = sum(w for _, w in contributions)
blended = sum(v * w for v, w in contributions) / total_weight

_exclude_movies(blended, movie_input.movies.items)
return _top_k(blended, k)
```

**Key properties:**
- Weights are normalized at runtime (sum to 1), so the frontend doesn't need to pre-normalize.
- Categories with no valid items are silently dropped from the blend.
- Movie-based and attribute-based signals are unified into the same vector space before blending.

---

## 6. Precomputed Similarity Matrices

All matrices are distributed in `similarity_matrices.zip` (~843 MB total).

| File | Shape | dtype | Algorithm | Notes |
|---|---|---|---|---|
| `genre.csv` | 14 × 14 | float64 | SpaCy `en_core_web_md` cosine | All 14 genres in-vocab |
| `keywords.csv` | 9,813 × 9,813 | float64 | SpaCy `en_core_web_md` cosine | 1.85% OOV (typos, acronyms, non-English) |
| `cast_director.npy` | 4,816 × 4,816 | float32 | ECLAT TF-IDF; blended 70% cast + 30% director | Movie-to-movie |
| `production_companies.npy` | 4,816 × 4,816 | float32 | ECLAT TF-IDF | Movie-to-movie |
| `genre_movie.npy` | 4,816 × 4,816 | float32 | Incidence lift of `genre.csv` | Mean-centered at load time |
| `keywords_movie.npy` | 4,816 × 4,816 | float32 | Incidence lift of `keywords.csv` | Mean-centered at load time |

All matrices are symmetric. Diagonal = 1.0 (or 0 for movies with no attributes in that signal).

---

## 7. Matrix Generation (`ml_dev.ipynb`)

### 7.1 SpaCy Embedding Matrices (genre.csv, keywords.csv)

**Model:** `en_core_web_md`

**Method:** `nlp(token_name).similarity(nlp(other_token_name))` — cosine similarity between averaged token word vectors.

**Process:**
1. Load all genre/keyword names.
2. Check vocabulary coverage; log OOV tokens.
3. Compute all pairwise similarities.
4. Write symmetric matrix to CSV.
5. (Keywords only) Checkpoint every 20 keywords due to ~36-hour compute time.

---

### 7.2 ECLAT TF-IDF Matrices (cast_director.npy, production_companies.npy)

**Rationale:** A film starring an obscure actor + Kubrick should score higher against other Kubrick films than against films sharing only the obscure actor. Rare collaborators carry higher weight.

**Algorithm:**

```
N = total number of movies

For each person p:
    df(p) = number of movies containing p
    idf(p) = log(N / df(p))

For each pair (i, j) of movies sharing person p:
    S[i, j] += idf(p)²

L2-normalize rows and columns → cosine similarity
```

**For cast_director.npy specifically:**
1. Compute `S_cast` (actors only) and `S_dir` (directors only) separately.
2. Blend: `S = 0.7 * S_cast + 0.3 * S_dir`.

**Properties:**
- Symmetric, entries in [0, 1]
- Tom Hanks appearing in 50 films contributes much less than a cinematographer appearing in 3 specific films.

---

### 7.3 Lifted Movie-Level Matrices (genre_movie.npy, keywords_movie.npy)

Converts attribute-level similarity (14×14 or 9,813×9,813) to movie-level similarity (4,816×4,816).

**Algorithm:**

```
G[movie, attr] = 1 / |attrs(movie)|   # normalized incidence matrix

S_movie = G @ S_attr @ G.T            # lift via matrix multiplication

clip S_movie to [0, 1]
force diagonal to 1.0 (0 for movies with no attributes)
```

**Mean-centering (applied at load time in helpers.py):**

```python
S -= S.mean(axis=1, keepdims=True)
```

Converts the ~0.4 SpaCy baseline floor into zero-mean signed deviations. Above-average matches become positive; below-average become negative.

---

## 8. Data Contracts

### Input to Model

```python
@dataclass
class Category:
    items: list[int]   # positional indices into the respective lookup array
    weight: float      # user-specified importance, normalized at runtime

@dataclass
class InputFormatted:
    movies:               Category
    actors:               Category
    directors:            Category
    genres:               Category
    production_companies: Category
```

### Output from Model

```python
@dataclass
class MovieIdAndScore:
    id:    int    # TMDB movie ID
    score: float  # blended similarity score

@dataclass
class HydratedMovie:
    id:                   int
    score:                float
    title:                str
    genres:               list[str]
    cast:                 list[str]
    release_date:         str
    directors:            list[str]
    production_companies: list[str]
    poster_url:           str | None
```

---

## 9. Evaluation Status

**No formal evaluation metrics are implemented in the codebase.**

The system uses informal "vibe checks" — spot-testing known movies against expected outputs (e.g., confirming that a Nolan film recommends other Nolan films highly).

Stub functions exist but are not implemented:
- `continuous_similarity()` — numeric feature similarity (budget, runtime)
- `aggregate_similarity()` — superseded by `send_input_to_model()`

Metrics that could be added in future work:

| Metric | What it measures |
|---|---|
| Precision@k | Fraction of top-k results rated relevant |
| Recall@k | Fraction of relevant items captured in top-k |
| NDCG@k | Ranked quality of top-k; rewards highly-relevant items appearing earlier |
| MAP | Mean average precision across multiple queries |
| Hit rate | Whether at least one relevant item appears in top-k |
| Coverage | Fraction of catalog ever recommended |
| Intra-list diversity | Average pairwise dissimilarity within a returned list |

---

## 10. Scalability & Performance

| Dimension | Value |
|---|---|
| Dataset size | 4,816 movies |
| Keyword vocabulary | 9,813 terms |
| Matrix storage (disk) | ~843 MB compressed |
| Matrix memory (runtime) | ~200 MB |
| Inference latency | ~10–50 ms per request |
| Matrix generation (keyword SpaCy) | ~36 hours (one-time, offline) |
| Matrix generation (ECLAT) | Minutes (one-time, offline) |

Inference is fully vectorized via NumPy — no Python-level loops over movies at request time. `np.argpartition` finds top-k in O(n) rather than a full sort.
