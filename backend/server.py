from helpers import *
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@app.post("/api/recommend")
def recommend_movie():
    data = request.get_json()
    print("recv from client", "\n\n", data, "\n\n")
    
    try:
        formatted_inputs = format_raw_input(data)
    except ValidationError as e:
        return jsonify({"error": "Invalid payload", "details": e.errors()}), 400
        
    print(formatted_inputs)

    movie_recs = send_input_to_model(formatted_inputs)
    movie_recs_hydrated = hydrate_recommended_movies(movie_recs)

    original_movies_hydrated = hydrate_input_movies(formatted_inputs.movies.items)

    #Need to make it obvious where we end the input movies and start the recommended movies
    ret = (original_movies_hydrated + movie_recs_hydrated)   

    print("sending to client idx 0,1:","\n\n",  ret[0], "\n\n", ret[1])
    return jsonify(ret)

  
