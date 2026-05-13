import json
from MovieData import MovieData

md = MovieData()


titles = md.get_movies().tolist()
directors = md.get_directors().tolist()
cast = md.get_actors().tolist()
genres = md.get_genres().tolist()
production_companies = md.get_prod_companies().tolist()

with open('frontend/src/assets/valid_movies.json', 'w') as f:
    json.dump(titles, f)

with open('frontend/src/assets/valid_actors.json', 'w') as f:
    json.dump(cast, f)

with open('frontend/src/assets/valid_directors.json','w') as f:
    json.dump(directors, f)

with open('frontend/src/assets/valid_genres.json', 'w') as f:
    json.dump(genres, f)

with open('frontend/src/assets/valid_production_companies.json', 'w') as f:
    json.dump(production_companies, f)
