# movie-recomendation

## Setting up your environment `venv`
In order to isolate dependencies on your machine, use a python virtual environment (venv)

```bash
python3 -m venv venv
source venv/bin/activate
```
Once inside the virtual environment, install the project dependencies:
```bash
pip install -r requirements.txt
```
If you add a new dependency to the project, just add the package name to the requirements.txt file

After your first setup, you just need to run 
```bash 
source venv/bin/activate
```
when you start working, and 
```bash
pip install -r requirements.txt
```
when a new dependency is added to the project


## `MovieData.py` usage

This class loads in and handles most of the tedious backend for having the dataset in a "usable" state. To use the class simply do:

```python
from MovieData import MovieData
md = MovieData()
```

All categorical data has been converted into `ints` ennumerated from 0. The specific columns this applies to are genres, keywords, production_companies, cast, "directors", production_countries, and spoken_languages columns. production_countries and spoken_languages columns are split into two lists "codes" and "names". The "codes" are the 2-character ISO codes for a country or language where "names" are the full strings written in the language itself. eg:

- Running `md.get_prod_country_codes()` returns a `numpy.ndarray` displaying ['US', 'UK', etc.]
- Running `md.get_prod_country_names()` returns a `numpy.ndarray` displaying ['United States of America', 'United Kingdom', etc.]

The categorical data stored in the "clean data" lists of `int`s. These `int`s correspond to the indicies of the associated categorical object in the list that contains all of that column's entries. eg:

```python
# To see the genres for The Dark Knight Rises
all_genres = md.get_genres() 
>>> array(['Action', 'Adventure', etc...], dtype='<U15')

tdkr = md.entry_as_list('genres', 3)
>>> [0, 4, 5, 6]

all_genres[tdkr]
>>> array(['Action', 'Crime', 'Drama', 'Thriller'], dtype='<U15')
```

The country codes and names share the same indexing. Similarily, the language codes and names share their own indexing.

To obtain the different list call a getter method. A copy of original movie and credit datasets can be gotten by these getters, as well as a copy of the merged "clean data." All of datasets are returned as `pandas.DataFrame` objects. The following columns:

- genres
- keywords
- production_companies
- cast
- crew (this will return the directors specifically)
- production_countries
- spoken_languages

in the clean data are stored as strings. To access them, you will need to specifically call the `entry_as_list()` function. This will return an entry in a column as as list or if you don't provide a specific row number it will return the entire column as a `pandas.Series` object. eg:

```python
# returns all cast members (actors) in the first movie (Avatar 2009)
md.entry_as_list('cast',0)
>>> [0,1,2,3,4,5,etc...]

# returns the all casts members (actors) for all movies
md.entry_as_list('cast')
>>> pandas.Series
```






## `streamlit` Frontend
To test out the frontend, navigate to
```bash
movie-recommendation/frontend/
```
and run
```bash
streamlit run app.py
```
