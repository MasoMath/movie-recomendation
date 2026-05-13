import os
import re

from helpers import *
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError


@dataclass
class Payload:
    input_movies: list[HydratedMovie]
    recommended_movies: list[HydratedMovie]

app = Flask(__name__)

_env_origins = os.getenv("FLASK_CORS_ORIGINS", "").strip()
if _env_origins:
    _cors_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    _cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

_localhost_any_port = re.compile(r"^http://(localhost|127\.0\.0\.1):\d+$")

CORS(
    app,
    resources={r"/api/*": {"origins": _cors_origins + [_localhost_any_port]}},
)

@app.post("/api/recommend")
def recommend_movie():
    data = request.get_json()
    #print("recv from client", "\n\n", data, "\n\n")
    
    try:
        formatted_inputs = format_raw_input(data)
    except ValidationError as e:
        return jsonify({"error": "Invalid payload", "details": e.errors()}), 400
        
    #print(formatted_inputs)

    movie_recs = send_input_to_model(formatted_inputs)
    movie_recs_hydrated = hydrate_recommended_movies(movie_recs)

    original_movies_hydrated = hydrate_input_movies(formatted_inputs.movies.items)

    payload = Payload(original_movies_hydrated,movie_recs_hydrated)

    #print(payload)

    return jsonify(payload)

  
