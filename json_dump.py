import json
from MovieData import MovieData

md = MovieData()


titles = md.get_movies().tolist()
directors = md.get_directors().tolist()
cast = md.get_actors().tolist()
genres = md.get_genres().tolist()

with open('valid_movies.json', 'w') as f:
    json.dump(titles, f)

with open('valid_actors.json', 'w') as f:
    json.dump(cast, f)

with open('valid_directors.json','w') as f:
    json.dump(directors, f)

with open('valid_genres.json', 'w') as f:
    json.dump(genres, f)
