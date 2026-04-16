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

All categorical data has been converted into `ints`. The genres, keywords, production_companies,cast, and "directors" columns all had prexisting ids and those are used. For production_countries and spoken_languages, those have ids created (starting from 1) and are split into two dictionaries "codes" and "names". The "codes" are the 2-character ISO codes for a country or language where "names" are the full strings. eg:

- Running `md.get_prod_country_codes()` returns a dictionary displaying {1: 'US', 2: 'UK', etc.}
- Running `md.get_prod_country_names()` returns a dictionary displaying {1: 'United States of America', 2: 'United Kingdom', etc.}

To obtain the different dictionaries simply call a getter method. A copy of original movie and credit datasets can be gotten by these getters, as well as a copy of the merged "clean data." All of datasets are returned as `pandas.DataFrame` objects. Due to the limitations of this object (or at least in the implementation I whipped up) the columns:

- genres
- keywords
- production_companies
- cast
- crew (this will return the directors specifically)
- production_countries
- spoken_languages

have entries stored as strings. To access them, you will need to specifically call the `entry_as_list()` function. This will return an entry in a column as as list or if you don't provide a specific row number it will return the entire column as a column of lists. eg:

```python

# returns all cast members (actors) in the first movie (Avatar 2009)
md.entry_as_list('cast',0)

# returns the all casts members (actors) for all movies
md.entry_as_list('cast')
```
