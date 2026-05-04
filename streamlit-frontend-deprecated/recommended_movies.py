from dataclasses import dataclass
import requests

@dataclass
class RecommendedMovie:
    id: int
    title: str
    score: float

def get_recommendations(user_movies: list[str]) -> list[RecommendedMovie]:
    #arbitrary test data, this would come from the ML model
    return [
        RecommendedMovie(1895, "Star Wars: Episode III - Revenge of the Sith",  0.95),
        RecommendedMovie(787, "Mr. & Mrs. Smith", 0.88),
        RecommendedMovie(155, "The Dark Knight", 0.76)
    ]


def get_movie_poster_url(movie_id: int, tmdb_api_key: str):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}"
    response = requests.get(url)
    response.raise_for_status() 
    poster_path = response.json().get('poster_path')
    
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None

def get_recommended_movie_poster_urls(rec_movies: list[RecommendedMovie], tmdb_api_key: str):
    poster_urls = [] 
    for movie in rec_movies:
        poster_urls.append(get_movie_poster_url(movie.id,tmdb_api_key))
    return poster_urls
