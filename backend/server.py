import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#^this is just so that I don't have to move around the files to access MovieData

from MovieData import MovieData
from flask import Flask, request, jsonify
from dataclasses import dataclass
from flask_cors import CORS
import random
import pandas as pd
from dotenv import load_dotenv
import requests

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


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

movie_data_instance = MovieData(
    path_to_movie='../kaggledata/tmdb_5000_movies.csv',
    path_to_credits='../kaggledata/tmdb_5000_credits.csv'
)

all_movie_ids = movie_data_instance.get_data()['id'].tolist()

def get_movie_poster_url(movie_id: int, tmdb_api_key: str) -> str:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}"
    response = requests.get(url)
    response.raise_for_status() 
    poster_path = response.json().get('poster_path')
    
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None


def hydrate_movies(movie_recommendations: list[MovieIdAndScore]) -> list[HydratedMovie]:
    df = movie_data_instance.get_data()
    genres_arr = movie_data_instance.get_genres()
    actors_arr = movie_data_instance.get_actors()
    directors_arr = movie_data_instance.get_directors()
    
    hydrated_results = []
    for rec in movie_recommendations:
        matching_rows = df[df['id'] == rec.id]
        if matching_rows.empty:
            continue
            
        row = matching_rows.iloc[0]
        
        genre_names = genres_arr[row['genres']].tolist() if isinstance(row['genres'], list) else []
        cast_names = actors_arr[row['cast']].tolist() if isinstance(row['cast'], list) else []
        director_names = directors_arr[row['crew']].tolist() if isinstance(row['crew'], list) else []
        
        release_date = str(row['release_date']) if pd.notna(row['release_date']) else "Unknown"
        poster_url = get_movie_poster_url(rec.id, tmdb_api_key)

        hydrated_results.append(HydratedMovie(
            id=rec.id,
            score=rec.score,
            title=row['original_title'],
            genres=genre_names,
            cast=cast_names,
            release_date=release_date,
            directors=director_names,
            poster_url=poster_url
        ))
        
    return hydrated_results

def hydrate_movie_by_title(title: str) -> HydratedMovie:
    matching_rows = movie_data_instance.find_movies(title)
    if matching_rows.empty:
        print("WE COULD NOT FIND THE MOVIE IN THE DATAFRAME")
        return None
        
    row = matching_rows.iloc[0]
    
    genres_arr = movie_data_instance.get_genres()
    actors_arr = movie_data_instance.get_actors()
    directors_arr = movie_data_instance.get_directors()
    
    genre_names = genres_arr[row['genres']].tolist() if isinstance(row['genres'], list) else []
    cast_names = actors_arr[row['cast']].tolist() if isinstance(row['cast'], list) else []
    director_names = directors_arr[row['crew']].tolist() if isinstance(row['crew'], list) else []
    
    release_date = str(row['release_date']) if pd.notna(row['release_date']) else "Unknown"
    movie_id = int(row['id'])
    poster_url = get_movie_poster_url(movie_id, tmdb_api_key)

    return HydratedMovie(
        id=movie_id,
        score=1.0, 
        title=row['original_title'],
        genres=genre_names,
        cast=cast_names,
        release_date=release_date,
        directors=director_names,
        poster_url=poster_url
    )

def fake_ml_model(movie_input: str) -> list[MovieIdAndScore]:
    num_recommendations = 5
    random_ids = random.sample(all_movie_ids, num_recommendations)
    print(random_ids)
    return [MovieIdAndScore(id=m_id, score=round(random.random(), 3)) for m_id in random_ids]



def send_input_to_model(movie_input: str) -> list[MovieIdAndScore]:
    """
    Send the input movie to the model and get back an array of recommended movies. This is probably just an id and score?
    Using this intermediate function because I figure I'll have to mutate the data somehow or something idk man
    """
    movies = fake_ml_model(movie_input)
    return movies


@app.post("/api/recommend")
def recommend_movie():
    data = request.get_json()
    input_movie = data['query']
    movie_recs = send_input_to_model(input_movie)
    movie_recs_hydrated = hydrate_movies(movie_recs)
    original_movie_hydrated = hydrate_movie_by_title(input_movie)
    return jsonify([original_movie_hydrated] + movie_recs_hydrated)



   
