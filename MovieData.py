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
        self._clean_data = self._og_movie_data.merge(
            self._og_credits_data,
            how='inner', left_on='id', right_on='movie_id'
            ).drop(columns=[
                'homepage', 'overview', 'status', 'tagline',
                'title_x', 'title_y', 'movie_id'
            ]
        )

        # Initialize Master Lookup Tables for various movie attributes
        self._genres_dict =     {}
        self._keywords_dict =   {}
        self._prod_comp_dict =  {}
        self._prod_coun_dict =  {}
        self._prod_coun_name =  {}
        self._spoke_lang_dict = {}
        self._spoke_lang_name = {}
        self._actor_dict =      {}
        self._director_dict =   {}

        # Iterate through rows to parse nested string-list into the dicts
        for i in range(len(self._og_movie_data)):
            # Standard extraction for categories that have unique num IDs
            self._clean_df_w_id(
                self._genres_dict, self._og_movie_data, self._clean_data,
                'genres', i
            )
            self._clean_df_w_id(
                self._keywords_dict, self._og_movie_data,
                self._clean_data, 'keywords', i
            )
            self._clean_df_w_id(
                self._prod_comp_dict, self._og_movie_data,
                self._clean_data, 'production_companies', i
            )

            # Special extraction for categories using non-num IDs
            self._clean_df_wo_id(
                self._prod_coun_dict, self._prod_coun_name,
                self._og_movie_data, self._clean_data,
                'production_countries', i, id_key='iso_3166_1'
            )
            self._clean_df_wo_id(
                self._spoke_lang_dict, self._spoke_lang_name,
                self._og_movie_data, self._clean_data,
                'spoken_languages', i, id_key='iso_639_1'
            )

            # Extract Cast and Director from the Credits dataframe
            self._clean_df_w_id(
                self._actor_dict, self._og_credits_data,
                self._clean_data,'cast',i
            )
            self._extract_director(
                self._director_dict, self._og_credits_data,
                self._clean_data, i
            )


    # --- Getters for DataFrames and Lookup Dictionaries ---
    def get_og_movie_data(self):    return self._og_movie_data.copy()
    def get_og_credit_data(self):   return self._og_credits_data.copy()
    def get_data(self):             return self._clean_data.copy()
    
    def get_keys(self):                 return self._clean_data.keys()
    def get_genres(self):               return self._genres_dict
    def get_keywords(self):             return self._keywords_dict
    def get_prod_companies(self):       return self._prod_comp_dict
    def get_prod_country_codes(self):   return self._prod_coun_dict
    def get_prod_country_names(self):   return self._prod_coun_name
    def get_spoken_lang_codes(self):    return self._spoke_lang_dict
    def get_spoken_lang_names(self):    return self._spoke_lang_name
    def get_actors(self):               return self._actor_dict
    def get_directors(self):            return self._director_dict 

    def save_csv(self, file_path):
        """
            Exports the cleaned dataframe to a CSV file.
        """
        self._clean_data.to_csv('./' + file_path + '.csv')

    def entry_as_list(self, col_name, row_num=None):
        """
            Converts a string-represented list in the dataframe
            back into a Python list.

            The only columns which need this are:
                genres,
                keywords,
                production_companies,
                production_countries,
                spoken_languages,
                cast,
                crew
        """
        if row_num is not None:
            return ast.literal_eval(self._clean_data[col_name][row_num])
        return self._clean_data[col_name].apply(ast.literal_eval)
        

    @staticmethod
    def _list_to_dict(id_key, name_key, data):
        """
            Converts a list of dicts into a single dict
            mapping a specific ID to a Name.
        """
        return {item[id_key]: item[name_key] for item in data}
    
    @staticmethod
    def _sync_and_map(string_list, id_dict):
        """
            Maps strings to existing integer IDs or creates new ones.
            Returns a mapping of IDs found/created for the input strings.
        """
        existing_values = {v: k for k, v in id_dict.items()}
        next_id = max(id_dict.keys(), default=0) + 1
        for s in string_list:
            if s not in existing_values:
                id_dict[next_id] = s
                existing_values[s] = next_id
                next_id += 1
        result_dict = {existing_values[s]: s for s in string_list}
        return result_dict

    def _clean_df_w_id(
            self, dictionary, df, df_clean, col_name, i,
            id_key='id', name_key='name'
        ):
        """
            Processes columns where items already have unique numeric IDs.
            Replaces JSON strings in the dataframe with a simple list
            of ID keys.
        """
        col_as_dict = self._list_to_dict(
                id_key, name_key,
                ast.literal_eval(df[col_name][i])
        )
        df_clean.at[i, col_name] = str(list(col_as_dict.keys()))
        dictionary.update(col_as_dict)

    def _clean_df_wo_id(
            self, dictionary, name_dict, df, df_clean, col_name, i,
            id_key='id', name_key='name'
        ):
        """
            Processes columns without numeric IDs (like country/lang codes).
            Syncs codes to our master dict and updates the dataframe with
            generated IDs.
        """
        col_as_dict = self._list_to_dict(
                id_key,name_key,
                ast.literal_eval(df[col_name][i])
        )
        dict_to_add = self._sync_and_map(list(col_as_dict.keys()), dictionary)
        self._sync_and_map(list(col_as_dict.values()), name_dict)
        df_clean.at[i, col_name] = str(list(dict_to_add.keys()))
        dictionary.update(dict_to_add)

    def _extract_director(self, dictionary, df,df_clean,i):
        """
            Filters the 'crew' list to specifically extract members with
            the 'Director' job.
        """
        col_as_dict = {
            item['id']: item['name']
            for item in ast.literal_eval(df['crew'][i])
            if item['job'] == 'Director'
        }
        # Update the main dataframe column to only contain Director IDs
        df_clean.at[i, 'crew'] = str(list(col_as_dict.keys()))
        dictionary.update(col_as_dict)