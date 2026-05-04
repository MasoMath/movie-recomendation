from flask import Flask, request, jsonify
from dataclasses import dataclass
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@dataclass
class MovieIdAndScore:
    id: int
    score: float

def send_input_to_model(movie_input: str) -> list[MovieIdAndScore]:
    """
    Send the input movie to the model and get back an array of recommended movies. This is probably just an id and score?
    """

@app.post("/api/recommend")
def recommend_movie():
    data = request.get_json()
    print(data)
    return jsonify({
                       "id": 420,
                       "score": 0.69,
                   })
    
