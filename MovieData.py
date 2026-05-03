import numpy as np
import pandas as pd
import ast

class MovieData:
    """
        Handles loading, cleaning, and relational mapping for the
        TMDB 5000 Movies dataset.
        Flattens nested JSON-like strings into usable dictionaries and IDs.
    """

    def __init__(self,
                path_to_movie='./kaggledata/tmdb_5000_movies.csv',
                path_to_credits='./kaggledata/tmdb_5000_credits.csv'):
        # Load raw datasets
        self._og_movie_data = pd.read_csv(path_to_movie)
        self._og_credits_data = pd.read_csv(path_to_credits)

        # extracts df data that is already numeric
        df_non_cat_data = self._og_movie_data[[
            'id','original_title','budget','original_language','popularity',
            'release_date','revenue','runtime','vote_average','vote_count'
        ]]
        
        # converts categorical data into int data
        df_gkp, self._dict_gkp = self._clean_dataframe(
            self._og_movie_data,
            ['genres','keywords','production_companies']
        )
        df_cl, self._dict_cl = self._clean_dataframe_multi_id(
            self._og_movie_data,
            ['production_countries', 'spoken_languages'],
            ['iso_3166_1', 'iso_639_1']
        )
        df_cast, self._dict_cast = self._clean_dataframe(
            self._og_credits_data,
            ['cast'],id='movie_id'
        )
        df_crew, self._dict_crew = self._clean_director(
            self._og_credits_data,['crew']
        )
        # merges above cleaned df slices into 1 df
        df = df_gkp.merge(df_cl).merge(
            df_cast.merge(df_crew),left_on='id',right_on='movie_id'
        ).drop(columns=['movie_id'])
        self._clean_data = df_non_cat_data.merge(df)


    # --- Getters for DataFrames and Lookup Dictionaries ---
    def get_og_movie_data(self):    return self._og_movie_data.copy()
    def get_og_credit_data(self):   return self._og_credits_data.copy()
    def get_data(self):             return self._clean_data.copy()
    
    def get_genres(self):               return np.array(self._dict_gkp['genres'])
    def get_keywords(self):             return np.array(self._dict_gkp['keywords'])
    def get_prod_companies(self):       return np.array(self._dict_gkp['production_companies'])
    def get_prod_country_codes(self):   return np.array(self._dict_cl['iso_production_countries'])
    def get_prod_country_names(self):   return np.array(self._dict_cl['production_countries'])
    def get_spoken_lang_codes(self):    return np.array(self._dict_cl['iso_spoken_languages'])
    def get_spoken_lang_names(self):    return np.array(self._dict_cl['spoken_languages'])
    def get_actors(self):               return np.array(self._dict_cast['cast'])
    def get_directors(self):            return np.array(self._dict_crew['crew'])
    def get_movies(self):               return self._clean_data['original_title']

    def save_csv(self, file_path):
        """
            Exports the cleaned dataframe to a CSV file.
        """
        self._clean_data.to_csv('./' + file_path + '.csv')

    def entry_as_list(self, col_name, row_num=None):
        """
            DEPRECATED. Returns a "list stored as a string" as a list object.
            
            This function is no longer needed as data is now pre-parsed.
            It will be removed in a future version.

            Args:
                col_name (str): The name of the column to process.
                row_num (int, optional): The specific index of the row to convert. 

            Returns:
                list or pandas.Series: The requested data.
        """
        import warnings
        warnings.warn(
            "entry_as_list() is no longer needed and will be removed in a future update." +
            "\nCall find_movies() or index the get_data() DataFrame directly",
            DeprecationWarning,
            stacklevel=2
        )
        if row_num is not None:
            return self.get_data()[col_name][row_num]
        return self.get_data()[col_name]
        
    def find_movies(self,movies):
        """
            Finds movies by title (str) or by row index (int).

            Args:
                movies (str, int, or list): A single title, a single row index, 
                    or a list containing either titles or indices.

            Returns:
                pandas.DataFrame: A subset of the original DataFrame containing 
                    only the rows that match the provided titles exactly.

                    If str are provided and a movie is not present or has a typo,
                    the movie is not returned.
                    
            Example:
                >>> MovieData.find_movies("The Dark Knight Rises")
                >>> MovieData.find_movies(["Avatar", "Titanic"])
                >>> MovieData.find_movies(3)
                >>> MovieData.find_movies([0, 25])
        """
        if isinstance(movies,(str, int)): movies = [movies]
        if isinstance(movies[0], int):
            return self._clean_data.iloc[movies]
        else:
            return self._clean_data.loc[
                self._clean_data['original_title'].isin(movies)
            ]

    @staticmethod
    def _clean_dataframe(df, col_names, id='id'):
        """
        Processes multiple columns, giving each its own unique ID mapping.
        Returns the cleaned dataframe and a nested dictionary of mappings.
        """
        id_map = {}
        df_clean = df[[id]+col_names].copy()

        for col in col_names:
            name_to_id = {}
            names_present = []
            next_id = 0
            
            def process_cell(cell_value):
                nonlocal next_id
                items = ast.literal_eval(cell_value)
                row_ids = []

                for item in items:
                    name = item.get('name')
                    if name not in name_to_id:
                        names_present.append(name)
                        name_to_id[name] = next_id
                        next_id += 1
                    row_ids.append(name_to_id[name])
                return str(row_ids)

            df_clean[col] = df[col].apply(process_cell).apply(ast.literal_eval)
            id_map[col] = names_present
            
        return df_clean, id_map


    @staticmethod
    def _clean_dataframe_multi_id(df, col_names, keys):
        """
        Processes multiple columns that have multiple identifiers,
        giving each its own unique ID mapping.
        Returns the cleaned dataframe and a nested dictionary of mappings.
        """
        id_map = {}
        df_clean = df[['id']+col_names].copy()

        for i in range(len(keys)):
            key = keys[i]
            col = col_names[i]
            name_to_id = {}
            names_present = []
            codes_present = []
            next_id = 0
            
            def process_cell(cell_value):
                nonlocal next_id
                nonlocal key
                items = ast.literal_eval(cell_value)
                row_ids = []

                for item in items:
                    iso_code = item.get(key)
                    name = item.get('name')
                    if name not in name_to_id:
                        names_present.append(name)
                        codes_present.append(iso_code)
                        name_to_id[name] = next_id
                        next_id += 1
                    row_ids.append(name_to_id[name])
                return str(row_ids)

            df_clean[col] = df[col].apply(process_cell).apply(ast.literal_eval)
            id_map[col] = names_present
            id_map['iso_'+col] = codes_present         
        return df_clean, id_map

    @staticmethod
    def _clean_director(df, col_names):
        """
        Processes multiple columns, giving each its own unique ID mapping.
        Returns the cleaned dataframe and a nested dictionary of mappings.
        """
        id_map = {}
        df_clean = df[['movie_id']+col_names].copy()

        for col in col_names:
            name_to_id = {}
            names_present = []
            next_id = 0
            
            def process_cell(cell_value):
                nonlocal next_id
                items = ast.literal_eval(cell_value)
                row_ids = []

                for item in items:
                    job = item.get('job')
                    if job == 'Director':
                        name = item.get('name')
                        if name not in name_to_id:
                            names_present.append(name)
                            name_to_id[name] = next_id
                            next_id += 1
                        row_ids.append(name_to_id[name])
                return str(row_ids)

            df_clean[col] = df[col].apply(process_cell).apply(ast.literal_eval)
            id_map[col] = names_present
        return df_clean, id_map

    