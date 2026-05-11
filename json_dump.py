import json
from MovieData import MovieData

md = MovieData()


directors = md.get_og_movie_data();
print(directors)
titles = md.get_movies().tolist()

with open('test.json', 'w') as f:
    json.dump(titles, f)
