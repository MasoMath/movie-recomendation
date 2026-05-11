import os, sys, random, requests


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#^this is just so that I don't have to move around the files to access MovieData

from MovieData import MovieData
from dataclasses import dataclass
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
    poster_url: str

class Category(BaseModel):
    items: list[str]
    weight: float

class InputFormatted(BaseModel):
    movies: Category
    actors: Category
    directors: Category
    genres: Category
    
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
    #print(random_ids)
    return [MovieIdAndScore(id=m_id, score=round(random.random(), 3)) for m_id in random_ids]

def send_input_to_model(movie_input: InputFormatted) -> list[MovieIdAndScore]:
    movies = fake_ml_model(movie_input)
    return movies

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

all_movie_posters = {}

