import os, sys, random, requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#^this is just so that I don't have to move around the files to access MovieData

from MovieData import MovieData
from dataclasses import dataclass
import numpy as np
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
tmdb_api_key = os.getenv("TMDB_API_KEY")

@dataclass
class MovieIdAndScore:
    id: int
    score: float

@dataclass
class HydratedMovie:
    id: int
    score: float
    title: str
    genres: list[str]
    cast: list[str]
    release_date: str
    directors: list[str]
    production_companies: list[str]
    poster_url: str

class Category(BaseModel):
    items: list[str]
    weight: float

class InputFormatted(BaseModel):
    movies: Category
    actors: Category
    directors: Category
    genres: Category
    production_companies: Category

def format_raw_input(payload: dict) -> InputFormatted:
    return InputFormatted(**payload)


# --- Hydration ---

def get_movie_poster_url(movie_id: int, tmdb_api_key: str) -> str:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}"
    try:
        response = requests.get(url, timeout=3)
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    poster_path = response.json().get('poster_path')
    return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

def _hydrate_movie_from_row(row, score: float) -> HydratedMovie:
    genre_names   = genres_arr[row['genres']].tolist() if isinstance(row['genres'], list) else []
    cast_names    = actors_arr[row['cast']].tolist()   if isinstance(row['cast'], list)   else []
    director_names = directors_arr[row['crew']].tolist() if isinstance(row['crew'], list) else []
    raw_pc = row['production_companies'] if 'production_companies' in row.index else []
    company_names = production_companies_arr[raw_pc].tolist() if isinstance(raw_pc, list) and raw_pc else []

    release_date = str(row['release_date']) if pd.notna(row['release_date']) else "Unknown"
    movie_id = int(row['id'])

    poster_url = all_movie_posters.get(movie_id)
    if not poster_url:
        poster_url = get_movie_poster_url(movie_id, tmdb_api_key)
        all_movie_posters[movie_id] = poster_url

    return HydratedMovie(
        id=movie_id, score=score, title=row['original_title'],
        genres=genre_names, cast=cast_names, release_date=release_date,
        directors=director_names, production_companies=company_names, poster_url=poster_url
    )

def hydrate_recommended_movies(recs: list[MovieIdAndScore]) -> list[HydratedMovie]:
    return [_hydrate_movie_from_row(df.loc[r.id], r.score) for r in recs if r.id in df.index]

#TODO: Don't append None
def hydrate_input_movies(input_movies: list[str]) -> list[HydratedMovie]:
    results = []
    for title in input_movies:
        rows = movie_data_instance.find_movies(title)
        results.append(_hydrate_movie_from_row(rows.iloc[0], 1.0) if not rows.empty else None)
    return results


# --- ML helpers ---

SIMILARITY_WEIGHTS = {
    'cast_director':        0.45,
    'production_companies': 0.20,
    'keyword':              0.20,
    'genre':                0.15,
}

def _build_index(col: str, arr: np.ndarray) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos, (_, row) in enumerate(df.iterrows()):
        if isinstance(row[col], list):
            for i in row[col]:
                index.setdefault(arr[i].lower(), []).append(pos)
    return index

def _top_k(scores: np.ndarray, k: int = 10) -> list[MovieIdAndScore]:
    k = min(k, len(scores))
    top = np.argpartition(-scores, k)[:k]
    top = top[np.argsort(-scores[top])]
    return [MovieIdAndScore(id=int(pos_to_tmdb_id[p]), score=round(float(scores[p]), 4))
            for p in top if scores[p] >= 0.0]

def _exclude_movies(scores: np.ndarray, titles: list[str]) -> None:
    for title in titles:
        rows = movie_data_instance.find_movies(title)
        if not rows.empty:
            pos = tmdb_id_to_pos.get(int(rows.iloc[0]['id']))
            if pos is not None:
                scores[pos] = -1.0

def _minmax_normalize(v: np.ndarray) -> np.ndarray:
    lo, hi = v.min(), v.max()
    return (v - lo) / (hi - lo) if hi - lo > 1e-9 else np.zeros_like(v)

def _movie_sim_vector(title: str) -> np.ndarray | None:
    matches = movie_data_instance.find_movies(title)
    if matches.empty:
        return None
    pos = tmdb_id_to_pos.get(int(matches.iloc[0]['id']))
    if pos is None:
        return None
    return (
        SIMILARITY_WEIGHTS['cast_director']        * cast_director_matrix[pos]
        + SIMILARITY_WEIGHTS['production_companies'] * production_companies_matrix[pos]
        + SIMILARITY_WEIGHTS['keyword']              * keywords_movie_matrix[pos]
        + SIMILARITY_WEIGHTS['genre']                * genre_movie_matrix[pos]
    ).copy()

def _presence_vector(items: list[str], lookup: dict) -> np.ndarray | None:
    vecs = []
    for name in items:
        positions = lookup.get(name.lower())
        if positions:
            v = np.zeros(len(pos_to_tmdb_id), dtype=np.float32)
            v[positions] = 1.0
            vecs.append(v)
    return np.mean(vecs, axis=0) if vecs else None

def _category_vector(category: Category, lookup: dict | None) -> np.ndarray | None:
    if not category.items or category.weight <= 0:
        return None
    if lookup is None:
        vecs = [v for t in category.items if (v := _movie_sim_vector(t)) is not None]
        raw = np.mean(vecs, axis=0) if vecs else None
    else:
        raw = _presence_vector(category.items, lookup)
    return _minmax_normalize(raw) if raw is not None else None


# --- Recommendation API ---

def blended_recommend(movie_title: str, k: int = 10) -> list[MovieIdAndScore]:
    sims = _movie_sim_vector(movie_title)
    if sims is None:
        return []
    _exclude_movies(sims, [movie_title])
    return _top_k(sims, k)

def send_input_to_model(movie_input: InputFormatted, k: int = 10) -> list[MovieIdAndScore]:
    specs = [
        (movie_input.movies,               None),
        (movie_input.actors,               _actor_index),
        (movie_input.directors,            _director_index),
        (movie_input.genres,               _genre_index),
        (movie_input.production_companies, _company_index),
    ]
    contributions = [
        (vec, cat.weight)
        for cat, lkp in specs
        if (vec := _category_vector(cat, lkp)) is not None
    ]
    if not contributions:
        return []
    total_weight = sum(w for _, w in contributions)
    blended = sum(v * w for v, w in contributions) / total_weight
    _exclude_movies(blended, movie_input.movies.items)
    return _top_k(blended, k)

def fake_ml_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    ids = random.sample(all_movie_ids, 10)
    return [MovieIdAndScore(id=m, score=round(random.random(), 3)) for m in ids]


# --- Startup: load data, matrices, build indices ---

movie_data_instance = MovieData(
    path_to_movie='../kaggledata/tmdb_5000_movies.csv',
    path_to_credits='../kaggledata/tmdb_5000_credits.csv'
)

df = movie_data_instance.get_data()
all_movie_ids = df['id'].tolist()

_tmdb_ids_in_order = df['id'].values
tmdb_id_to_pos = {int(tid): i for i, tid in enumerate(_tmdb_ids_in_order)}
pos_to_tmdb_id = np.asarray(_tmdb_ids_in_order, dtype=np.int64)

df.set_index('id', drop=False, inplace=True)
genres_arr               = movie_data_instance.get_genres()
actors_arr               = movie_data_instance.get_actors()
directors_arr            = movie_data_instance.get_directors()
production_companies_arr = movie_data_instance.get_prod_companies()

_matrices_dir = os.path.join(os.path.dirname(__file__), '..', 'similarity_matrices')
cast_director_matrix        = np.load(os.path.join(_matrices_dir, 'cast_director.npy'))
production_companies_matrix = np.load(os.path.join(_matrices_dir, 'production_companies.npy'))
genre_movie_matrix          = np.load(os.path.join(_matrices_dir, 'genre_movie.npy'))
keywords_movie_matrix       = np.load(os.path.join(_matrices_dir, 'keywords_movie.npy'))

# Mean-center dense (SpaCy) matrices so they contribute signed adjustments instead of a flat ~0.4 baseline
genre_movie_matrix    -= genre_movie_matrix.mean(axis=1, keepdims=True)
keywords_movie_matrix -= keywords_movie_matrix.mean(axis=1, keepdims=True)

_actor_index    = _build_index('cast',                 actors_arr)
_director_index = _build_index('crew',                 directors_arr)
_genre_index    = _build_index('genres',               genres_arr)
_company_index  = _build_index('production_companies', production_companies_arr)

all_movie_posters = {}
