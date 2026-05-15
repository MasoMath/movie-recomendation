import os, sys, random, requests
from concurrent.futures import ThreadPoolExecutor

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_ROOT)

from MovieData import MovieData
from similarity import aggregate_similarity
from dataclasses import dataclass
from pydantic import BaseModel
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
tmdb_api_key = os.getenv("TMDB_API_KEY")

TMDB_REQUEST_TIMEOUT = 10
NUM_RECOMMENDATIONS = 10

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
    items: list[int]
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
        response = requests.get(url,timeout=TMDB_REQUEST_TIMEOUT)
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
    valid_recs = [(rec, df.loc[rec.id]) for rec in movie_recommendations if rec.id in df.index]
    if not valid_recs:
        return []

    uncached_ids = [int(row['id']) for _, row in valid_recs if not all_movie_posters.get(int(row['id']))]
    if uncached_ids:
        with ThreadPoolExecutor(max_workers=len(uncached_ids)) as executor:
            for movie_id, url in executor.map(lambda mid: (mid, get_movie_poster_url(mid, tmdb_api_key)), uncached_ids):
                all_movie_posters[movie_id] = url

    return [_hydrate_movie_from_row(row, rec.score) for rec, row in valid_recs]


def hydrate_input_movies(input_movie_indices: list[int]) -> list[HydratedMovie]:
    hydrated_results = []
    for idx in input_movie_indices:
        row = movie_data_instance.get_data().iloc[idx]
        hydrated_results.append(_hydrate_movie_from_row(row, 1.0))
    return hydrated_results

def fake_ml_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    random_ids = random.sample(all_movie_ids, NUM_RECOMMENDATIONS)
    return [MovieIdAndScore(id=m_id, score=round(random.random(), 3)) for m_id in random_ids]

def send_input_to_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    return fake_ml_model(movie_input)



movie_data_instance = MovieData(
    path_to_movie='../kaggledata/tmdb_5000_movies.csv',
    path_to_credits='../kaggledata/tmdb_5000_credits.csv'
)

all_movie_ids = movie_data_instance.get_data()['id'].tolist()

df = movie_data_instance.get_data()
df.set_index('id', drop=False, inplace=True)
genres_arr = movie_data_instance.get_genres()
actors_arr = movie_data_instance.get_actors()
directors_arr = movie_data_instance.get_directors()
production_companies_arr = movie_data_instance.get_prod_companies()

all_movie_posters = {}

try:
    genre_matrix = np.loadtxt('../similarity_matrices/genre.csv', delimiter=',')
    keyword_matrix = np.loadtxt('../similarity_matrices/keywords.csv', delimiter=',')
except FileNotFoundError:
    genre_matrix = None
    keyword_matrix = None
    print("Similarity Matrices not found")

