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


def get_movie_poster_url(movie_id: int, tmdb_api_key: str) -> str:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}"

    try:
        response = requests.get(url, timeout=3)
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    poster_path = response.json().get('poster_path')
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None

def _hydrate_movie_from_row(row, score: float) -> HydratedMovie:
    genre_names = genres_arr[row['genres']].tolist() if isinstance(row['genres'], list) else []
    cast_names = actors_arr[row['cast']].tolist() if isinstance(row['cast'], list) else []
    director_names = directors_arr[row['crew']].tolist() if isinstance(row['crew'], list) else []
    raw_pc = row['production_companies'] if 'production_companies' in row.index else []
    if isinstance(raw_pc, list) and len(raw_pc) > 0:
        company_names = production_companies_arr[raw_pc].tolist()
    else:
        company_names = []

    release_date = str(row['release_date']) if pd.notna(row['release_date']) else "Unknown"
    movie_id = int(row['id'])
    
    poster_url = all_movie_posters.get(movie_id)
    if not poster_url:
        poster_url = get_movie_poster_url(movie_id, tmdb_api_key)
        all_movie_posters[movie_id] = poster_url

    return HydratedMovie(
        id=movie_id,
        score=score,
        title=row['original_title'],
        genres=genre_names,
        cast=cast_names,
        release_date=release_date,
        directors=director_names,
        production_companies=company_names,
        poster_url=poster_url
    )

def hydrate_recommended_movies(movie_recommendations: list[MovieIdAndScore]) -> list[HydratedMovie]:
    hydrated_results = []
    for rec in movie_recommendations:
        if rec.id not in df.index:
            continue

        row = df.loc[rec.id]
        hydrated_results.append(_hydrate_movie_from_row(row, rec.score))

    return hydrated_results


#TODO: Don't append None
def hydrate_input_movies(input_movies: list[str]) -> list[HydratedMovie]:
    hydrated_results = []
    for title in input_movies:
        matching_rows = movie_data_instance.find_movies(title)
        if matching_rows.empty:
            hydrated_results.append(None)
            continue

        row = matching_rows.iloc[0]
        hydrated_results.append(_hydrate_movie_from_row(row, 1.0))

    return hydrated_results

def fake_ml_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    num_recommendations = 10
    random_ids = random.sample(all_movie_ids, num_recommendations)
    return [MovieIdAndScore(id=m_id, score=round(random.random(), 3)) for m_id in random_ids]

# Weights for the blended score served by /api/recommend.
# Sparse components (cast_director, production_companies) carry the bulk of the
# weight because they have real zeros for unrelated movies. Dense components
# (genre, keyword) are mean-centered at load time so they contribute signed
# adjustments around zero instead of a flat ~0.4 baseline.
SIMILARITY_WEIGHTS = {
    'cast_director':        0.45,
    'production_companies': 0.20,
    'keyword':              0.20,
    'genre':                0.15,
}

def blended_recommend(movie_title: str, k: int = 10) -> list[MovieIdAndScore]:
    matches = movie_data_instance.find_movies(movie_title)
    if matches.empty:
        return []
    query_tmdb_id = int(matches.iloc[0]['id'])
    query_pos = tmdb_id_to_pos.get(query_tmdb_id)
    if query_pos is None:
        return []
    sims = (
        SIMILARITY_WEIGHTS['cast_director']        * cast_director_matrix[query_pos]
        + SIMILARITY_WEIGHTS['production_companies'] * production_companies_matrix[query_pos]
        + SIMILARITY_WEIGHTS['keyword']              * keywords_movie_matrix[query_pos]
        + SIMILARITY_WEIGHTS['genre']                * genre_movie_matrix[query_pos]
    ).copy()
    sims[query_pos] = -1  # exclude self
    top_pos = np.argpartition(-sims, k)[:k]
    top_pos = top_pos[np.argsort(-sims[top_pos])]
    return [
        MovieIdAndScore(id=int(pos_to_tmdb_id[p]), score=float(sims[p]))
        for p in top_pos
    ]

def send_input_to_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    titles = movie_input.movies.items
    if not titles:
        return []
    return blended_recommend(titles[0])

movie_data_instance = MovieData(
    path_to_movie='../kaggledata/tmdb_5000_movies.csv',
    path_to_credits='../kaggledata/tmdb_5000_credits.csv'
)

all_movie_ids = movie_data_instance.get_data()['id'].tolist()

df = movie_data_instance.get_data()
# Positional-index <-> TMDB-id mapping (matrix uses positional, df uses TMDB id below)
_tmdb_ids_in_order = df['id'].values
tmdb_id_to_pos = {int(tid): i for i, tid in enumerate(_tmdb_ids_in_order)}
pos_to_tmdb_id = np.asarray(_tmdb_ids_in_order, dtype=np.int64)

df.set_index('id', drop=False, inplace=True)
genres_arr = movie_data_instance.get_genres()
actors_arr = movie_data_instance.get_actors()
directors_arr = movie_data_instance.get_directors()
production_companies_arr = movie_data_instance.get_prod_companies()

_matrices_dir = os.path.join(os.path.dirname(__file__), '..', 'similarity_matrices')
cast_director_matrix        = np.load(os.path.join(_matrices_dir, 'cast_director.npy'))
production_companies_matrix = np.load(os.path.join(_matrices_dir, 'production_companies.npy'))
genre_movie_matrix          = np.load(os.path.join(_matrices_dir, 'genre_movie.npy'))
keywords_movie_matrix       = np.load(os.path.join(_matrices_dir, 'keywords_movie.npy'))

# Mean-center the dense (SpaCy-derived) components per row so they contribute
# signed adjustments around zero instead of a flat ~0.4 baseline that compresses
# the blended score. Sparse components (cast_director, production_companies) are
# left as-is because they already have real zeros for unrelated movies.
genre_movie_matrix    -= genre_movie_matrix.mean(axis=1, keepdims=True)
keywords_movie_matrix -= keywords_movie_matrix.mean(axis=1, keepdims=True)

all_movie_posters = {}

