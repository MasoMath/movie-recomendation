from helpers import *

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


@app.post("/api/recommend")
def recommend_movie():
    data = request.get_json()
    input_movie = data['query']
    movie_recs = send_input_to_model(input_movie)
    movie_recs_hydrated = hydrate_movies(movie_recs)
    original_movie_hydrated = hydrate_movie_by_title(input_movie)
    return jsonify([original_movie_hydrated] + movie_recs_hydrated)



   
