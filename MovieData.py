# from numpy import array
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

        # Merge datasets on movie ID and drop unneeded metadata columns
        # self._clean_data = self._og_movie_data.merge(
        #     self._og_credits_data,
        #     how='inner', left_on='id', right_on='movie_id'
        #     ).drop(columns=[
        #         'homepage', 'overview', 'status', 'tagline',
        #         'title_x', 'title_y', 'movie_id'
        #     ]
        # )

        df_non_cat_data = self._og_movie_data[[
            'id','original_title','budget','original_language','popularity',
            'release_date','revenue','runtime','vote_average','vote_count'
        ]]
                
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

    def save_csv(self, file_path):
        """
            Exports the cleaned dataframe to a CSV file.
        """
        self._clean_data.to_csv('./' + file_path + '.csv')

    def entry_as_list(self, col_name, row_num=None):
        """
            Returns a "list stored as a string" as a list object.

            Args:
                col_name (str): The name of the column to process
                    The only columns that need this are:
                    'genres', 'keywords', 'production_companies', 'production_countries', 
                    'spoken_languages', 'cast', or 'crew'.
                row_num (int, optional): The specific index of the row to convert. 
                    If None (default), the operation is applied to the entire column.

            Returns:
                list or pandas.Series: 
                    - A single list (or list of dicts) if `row_num` is provided.
                    - A pandas.Series of lists if `row_num` is None.

            Raises:
                ValueError: If the string content is not a valid Python literal.
                KeyError: If `col_name` does not exist in the underlying data.
                IndexError: If `row_num` is out of bounds.

            Example:
                >>> # Get all genres as lists
                >>> df_helper.entry_as_list('genres')
                >>> # Get the cast list for the first movie only
                >>> df_helper.entry_as_list('cast', row_num=0)
            """
        if row_num is not None:
            return ast.literal_eval(self._clean_data[col_name][row_num])
        return self._clean_data[col_name].apply(ast.literal_eval)
        

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

            df_clean[col] = df[col].apply(process_cell)
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

            df_clean[col] = df[col].apply(process_cell)
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

            df_clean[col] = df[col].apply(process_cell)
            id_map[col] = names_present
        return df_clean, id_map

    @staticmethod
    def _list_to_dict(id_key, name_key, data):
        """
            Converts a list of dicts into a single dict
            mapping a specific ID to a Name.
        """
        import warnings
        warnings.warn(
                'Deprecated: This function no longer serves a purpose',
                category=DeprecationWarning,
                stacklevel=2
            )
        return {item[id_key]: item[name_key] for item in data}
    
    @staticmethod
    def _sync_and_map(string_list, id_dict):
        """
            Maps strings to existing integer IDs or creates new ones.
            Returns a mapping of IDs found/created for the input strings.
        """
        import warnings
        warnings.warn(
                'Deprecated: This function no longer serves a purpose',
                category=DeprecationWarning,
                stacklevel=2
            )
        existing_values = {v: k for k, v in id_dict.items()}
        next_id = max(id_dict.keys(), default=0) + 1
        for s in string_list:
            if s not in existing_values:
                id_dict[next_id] = s
                existing_values[s] = next_id
                next_id += 1
        result_dict = {existing_values[s]: s for s in string_list}
        return result_dict
