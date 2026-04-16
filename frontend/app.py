import streamlit as st
import os
from dotenv import load_dotenv
from recommended_movies import *

load_dotenv()

tmdb_api_key = os.getenv("TMDB_API_KEY")

recs = get_recommendations(["The Hitchhiker's Guide to the Galaxy", "Star Wars: Return of the Jedi"])

st.title("K-Means Movie Recommendations")

cols = st.columns(len(recs))

for i, movie in enumerate(recs):
    with cols[i]:
        st.subheader(movie.title)
        poster_url = get_movie_poster_url(movie.id, tmdb_api_key)
        
        if poster_url:
            st.image(poster_url, caption=f"Recommendation Score: {movie.score}")
        else:
            st.write("No poster available")
