# Project Overview — TMDB Movie Recommendation System

A full-stack content-based movie recommendation system built on the TMDB 5000 dataset. Users search by movies, actors, directors, genres, or studios with custom weights; the system returns the 10 most similar films visualized as an interactive force-directed graph.

---

## Table of Contents

1. [Architecture at a Glance](#1-architecture-at-a-glance)
2. [Directory Structure](#2-directory-structure)
3. [Frontend](#3-frontend)
4. [Backend API](#4-backend-api)
5. [ML Pipeline](#5-ml-pipeline)
6. [Data](#6-data)
7. [Setup & Running](#7-setup--running)
8. [Key Files Reference](#8-key-files-reference)

---

## 1. Architecture at a Glance

```
┌─────────────────────────────────────────┐
│             Browser (Svelte SPA)         │
│                                         │
│  SearchBar → POST /api/recommend        │
│  ForceGraph ← HydratedMovie[]           │
└───────────────────┬─────────────────────┘
                    │ HTTP (localhost:5173 → :5000)
┌───────────────────▼─────────────────────┐
│              Flask API (:5000)           │
│                                         │
│  /api/recommend                         │
│    → format_raw_input (Pydantic)        │
│    → send_input_to_model                │
│    → hydrate_recommended_movies         │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│           ML Inference Layer             │
│                                         │
│  Precomputed matrices (loaded at start) │
│  Weighted blend of 4 signals → top-10  │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│     similarity_matrices/ + kaggledata/   │
│  4816 movies × 4 similarity matrices    │
└─────────────────────────────────────────┘
```

**Request lifecycle:** frontend sends category indices + weights → Flask validates → ML layer blends precomputed similarity vectors → top-10 results hydrated with TMDB poster/metadata → returned as JSON → D3 renders graph.

---

## 2. Directory Structure

```
Code/
├── frontend/               Svelte + Vite SPA (TypeScript)
│   ├── src/
│   │   ├── App.svelte
│   │   ├── components/
│   │   │   ├── SearchBar.svelte
│   │   │   ├── ForceGraph.svelte
│   │   │   ├── MovieModal.svelte
│   │   │   └── InputsSummaryModal.svelte
│   │   ├── lib/            Utilities & Zod types
│   │   └── assets/         Generated JSON lookups (movies, actors, etc.)
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                Flask REST API (Python)
│   ├── server.py           App entry point, single route
│   ├── helpers.py          ML inference + TMDB hydration
│   └── startserver.sh
│
├── similarity_matrices/    Precomputed .npy / .csv matrices
│   ├── cast_director.npy       4816 × 4816
│   ├── production_companies.npy 4816 × 4816
│   ├── genre_movie.npy         4816 × 4816
│   ├── keywords_movie.npy      4816 × 4816
│   ├── genre.csv               14 × 14
│   └── keywords.csv            9813 × 9813
│
├── kaggledata/             Raw TMDB CSVs
│   ├── tmdb_5000_movies.csv
│   └── tmdb_5000_credits.csv
│
├── MovieData.py            Data loading & cleaning class
├── similarity.py           Standalone similarity functions
├── json_dump.py            Generate frontend JSON asset files
├── grab_data.py            Download TMDB data via kagglehub
├── requirements.txt
├── ml_dev.ipynb            Matrix generation notebook
├── ExploreSemanticSimilarity.ipynb
├── run-backend.ps1
├── run-frontend.ps1
├── start-app.sh
└── similarity_matrices.zip (~843 MB, distributed separately)
```

---

## 3. Frontend

**Stack:** Svelte 5, TypeScript, Vite 8, D3 v7, Zod

Dev server: `http://localhost:5173`

### Components

#### `SearchBar.svelte`
Multi-category search with five independent input channels: **Movies**, **Actors**, **Directors**, **Genres**, **Production Companies**. Each channel has a weight slider. Autocomplete pulls from JSON lookup files in `src/assets/`. On submit, resolves names to integer indices and POSTs to the backend.

#### `ForceGraph.svelte`
D3 force-directed graph. The primary search result is the center node; the 10 recommendations radiate outward. Edge thickness represents similarity score. Clicking a node opens `MovieModal`. Clicking the center opens `InputsSummaryModal`.

#### `MovieModal.svelte`
Detailed card for a single movie: poster, title, release year, genres, cast, directors, studios, similarity score.

#### `InputsSummaryModal.svelte`
Shows the user's input selections and weights that produced the current graph.

### Frontend ↔ Backend Contract

**Request** `POST http://localhost:5000/api/recommend`:
```json
{
  "movies":               { "items": [42, 178], "weight": 1.0 },
  "actors":               { "items": [5],       "weight": 0.5 },
  "directors":            { "items": [],         "weight": 0.0 },
  "genres":               { "items": [3],        "weight": 0.3 },
  "production_companies": { "items": [],         "weight": 0.0 }
}
```

`items` are **positional indices** into the corresponding lookup array (not TMDB IDs).

**Response:**
```json
{
  "input_movies": [ HydratedMovie, ... ],
  "recommended_movies": [ HydratedMovie, ... ]
}
```

Response schema is validated client-side with Zod (`ServerPayload`).

### Asset Files (generated by `json_dump.py`)

| File | Content |
|---|---|
| `valid_movies.json` | All 5000 movie titles, int-indexed |
| `valid_actors.json` | All actor names, int-indexed |
| `valid_directors.json` | All director names, int-indexed |
| `valid_genres.json` | 20 genre strings |
| `valid_production_companies.json` | All studio names, int-indexed |

These are regenerated by running `python json_dump.py` from the project root whenever the cleaned dataset changes.

---

## 4. Backend API

**Stack:** Flask, Flask-CORS, Pydantic, Python 3.x

Port: `http://localhost:5000`

### Endpoint

#### `POST /api/recommend`

1. **Validate** — Pydantic parses the JSON body into `InputFormatted` (5 categories, each with `items: list[int]` and `weight: float`).
2. **Infer** — `send_input_to_model(formatted_input)` returns `list[MovieIdAndScore]`.
3. **Hydrate** — `hydrate_recommended_movies()` and `hydrate_input_movies()` fetch title, genres, cast, directors, studios, poster URL. Poster fetches run in a `ThreadPoolExecutor` for parallelism and are cached in-memory.
4. **Respond** — Returns `{ input_movies, recommended_movies }` as JSON.

### CORS

Allowed origins: `localhost:5173`, `127.0.0.1:5173`, `localhost:4173`, `127.0.0.1:4173`. Override with env var `FLASK_CORS_ORIGINS`.

### Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `TMDB_API_KEY` | Yes | Fetch movie poster images from TMDB |

---

## 5. ML Pipeline

Full details are in [`ML_DOCUMENTATION.md`](ML_DOCUMENTATION.md). Summary below.

### Signals & Weights

| Signal | Weight | Algorithm | Matrix |
|---|---|---|---|
| Cast + Director | 45% | ECLAT TF-IDF cosine | `cast_director.npy` |
| Production Companies | 20% | ECLAT TF-IDF cosine | `production_companies.npy` |
| Keywords | 20% | SpaCy embedding cosine (lifted + mean-centered) | `keywords_movie.npy` |
| Genres | 15% | SpaCy embedding cosine (lifted + mean-centered) | `genre_movie.npy` |

### How Inference Works

```
Input: { movies: [42], actors: [5], genres: [3], weight per category }

For each category:
  - Movies    → slice rows from the 4 blended precomputed matrices → normalize
  - Others    → invert-index lookup → presence vector → normalize

Weighted average of all category vectors
Exclude seed movies (score = -1)
argpartition → top-10
```

### How the Matrices Were Built

**ECLAT TF-IDF (cast/director, studios):**
- Person IDF = `log(N / document_frequency)`.
- For each pair of movies sharing a person, add `idf²` to the similarity matrix.
- L2-normalize → cosine similarity in [0, 1].
- Cast/director matrix blends 70% cast + 30% director.

**SpaCy Embeddings (genres, keywords):**
- `en_core_web_md` — cosine similarity between averaged word vectors per token.
- Genre matrix: 14 × 14, computed in minutes.
- Keyword matrix: 9,813 × 9,813, ~36 hours to compute.

**Lifting (attribute → movie level):**
- Build normalized incidence matrix `G` where `G[movie, attr] = 1 / |attrs(movie)|`.
- Lift: `S_movie = G @ S_attr @ G.T`, clip to [0, 1].

**Mean-centering (applied at server startup):**
- SpaCy matrices have a ~0.4 baseline floor (any two movies score ~0.4 regardless of content).
- Row-wise mean-centering converts absolute similarity to signed deviation, improving discrimination.

### Startup Initialization

On server start, `backend/helpers.py` module-level code:
1. Instantiates `MovieData` and builds lookup arrays.
2. Loads all four `.npy` matrices into memory.
3. Mean-centers the two SpaCy-derived matrices.
4. Builds inverted indices (`attr_id → [movie_positions]`) for actors, directors, genres, studios.

After startup, inference is purely NumPy operations — no disk I/O per request.

---

## 6. Data

### Raw Data — `kaggledata/`

| File | Size | Content |
|---|---|---|
| `tmdb_5000_movies.csv` | ~5.6 MB | Metadata: genres, keywords, budget, revenue, rating, language, overview |
| `tmdb_5000_credits.csv` | ~40 MB | Full cast and crew JSON per movie |

Downloaded by running `python grab_data.py` (uses `kagglehub`).

### Precomputed Matrices — `similarity_matrices/`

| File | Shape | Size | Notes |
|---|---|---|---|
| `cast_director.npy` | 4816 × 4816 | ~92 MB | ECLAT TF-IDF |
| `production_companies.npy` | 4816 × 4816 | ~92 MB | ECLAT TF-IDF |
| `genre_movie.npy` | 4816 × 4816 | ~92 MB | SpaCy lifted |
| `keywords_movie.npy` | 4816 × 4816 | ~385 MB | SpaCy lifted |
| `genre.csv` | 14 × 14 | ~10 KB | Attribute-level |
| `keywords.csv` | 9813 × 9813 | ~2.4 GB | Attribute-level |

Distributed as `similarity_matrices.zip` (~843 MB). Generated by running `ml_dev.ipynb`.

### Notebooks

| Notebook | Purpose |
|---|---|
| `ml_dev.ipynb` | Primary matrix generation (run offline, once) |
| `ExploreSemanticSimilarity.ipynb` | Research and QA for genre/keyword semantics |
| `numpy_clustering_example.ipynb` | Clustering experiments (legacy/research) |

---

## 7. Setup & Running

### First-Time Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download raw TMDB data
python grab_data.py

# 4. Extract precomputed similarity matrices
unzip similarity_matrices.zip -d similarity_matrices/

# 5. Generate frontend JSON lookup files
python json_dump.py

# 6. Install frontend dependencies
cd frontend && npm install
```

> **Note (Windows/SSL):** If `kagglehub` or `npm` fail on certificate errors, set the system CA bundle path explicitly before running. See `env_ssl_certs` in project memory.

### Running the App

**All-in-one (Bash):**
```bash
./start-app.sh
```

**Separate terminals (PowerShell):**
```powershell
# Terminal 1 — Backend
./run-backend.ps1
# or: cd backend; python -m flask --app server.py --debug run

# Terminal 2 — Frontend
./run-frontend.ps1
# or: cd frontend; npm run dev
```

**URLs:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`

### Environment Variables

Create a `.env` file in the project root (or `backend/`):
```
TMDB_API_KEY=your_key_here
```

---

## 8. Key Files Reference

| File | Purpose |
|---|---|
| `backend/server.py` | Flask app, single `/api/recommend` route |
| `backend/helpers.py` | ML inference, matrix loading, TMDB hydration |
| `MovieData.py` | Data loading and cleaning class |
| `similarity.py` | Standalone similarity functions (used in notebooks) |
| `json_dump.py` | Regenerate frontend JSON lookup assets |
| `grab_data.py` | Download TMDB CSVs via kagglehub |
| `ml_dev.ipynb` | Generate all precomputed similarity matrices |
| `frontend/src/components/SearchBar.svelte` | Multi-category search input |
| `frontend/src/components/ForceGraph.svelte` | D3 recommendation graph |
| `data-contract-front-back.md` | API schema reference |
| `ML_DOCUMENTATION.md` | Deep-dive ML architecture and function reference |
