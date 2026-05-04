import json
from MovieData import MovieData

md = MovieData()
titles = md.get_movies().tolist()

with open('valid_movies.json', 'w') as f:
    json.dump(titles, f)
