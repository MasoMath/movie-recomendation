"""
Home of Similarity Functions
"""

## Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from MovieData import MovieData

## Semantic Similarity (for Genres and Keywords for specific ids)
def id_semantic_similarity(attr1, attr_series, similarity_matrix, row2=None):
    """
        Calculates the average semantic similarity between sets of attributes.
        
        If row2 is provided, returns the mean similarity between attr1 and the
        attributes at that row index. If row2 is None, returns a list of mean 
        similarities between attr1 and every entry in attr_series.

        Args:
            attr1 (list[int]): A list of integer indices representing
                attributes (e.g., genre IDs) for the primary item.
            attr_series (pd.Series): A pandas Series where each element is a
                list of attribute indices.
                i.e. The column of genres or keywords
            similarity_matrix (np.ndarray): A 2D NumPy array containing
                pairwise similarity scores between individual attributes.
            row2 (int | None): The index of the target row in attr_series to
                compare against, or None to compare against all rows.

        Returns:
            float | list[float]: A single mean similarity score if row2 is
                specified, or a list of mean scores for the entire series.
                Returns np.nan if input attribute lists are empty.
    """
    def get_avg_similarity(attr1, attr2):
        """Calculates the mean of the sub-grid formed by two attribute sets."""
        if not attr1 or not attr2: return np.nan
        sub_matrix = similarity_matrix[np.ix_(attr1, attr2)]
        return sub_matrix.mean()
    
    if row2 is not None: # ids against specific movie
        attr2 = attr_series.iloc[row2]
        return get_avg_similarity(attr1, attr2)
    else: # ids against all movies
        row_similarities = attr_series.apply(
            lambda x: get_avg_similarity(attr1, x))
        return row_similarities.tolist()

## Semantic Similarity (for Genres and Keywords)
def semantic_similarity(
        ids, row2=None, attribute='genres', 
        similarity_matrix=None, moviedata=None):
    """
    Returns the similarity between the genres for a pair of movies
    Args:
        ids (int, or list[int]): indicies for "movie 1"
        row2 (int, optional): The specific index of the row of movie 2
            If None (default), the similarity is calculated between movie 1
            and all others in the database
        attribute ('genres' or 'keywords'): which attribute to apply semantic
            similarity to
        similarity_matrix (np.array): The loaded semantic similarity matrix
            If None (default), the similarity matrix is loaded in the function
        moviedata (custom object): The loaded moviedata object
            If None (default), the moviedata object is created in the function
    Note: for repeated function calls, it is reccomended to load in the
            genre_matrix and moviedata ahead of time and pass the loaded objects

    Returns:
        (list[float]) if row2 == (int): the average semantic similarities of
            the attribute between movie 1 ids and movie 2
        
        (list[list]) if row2 is None: a list of lists of the average similarity
            of the attribute between movie 1 ids and all others in the database
            Note: returned list has been "squeezed" to remove singleton dimension(s)

    Warning: If either movie has no listed genres, the similarity returned is NaN
    """
    if attribute not in ['genres', 'keywords']:
        error_text = attribute + ' is not valid semantic attribute.'
        raise ValueError(error_text)
    if not np.any(similarity_matrix): 
        if attribute=='genres':
            similarity_matrix = np.loadtxt(
                'similarity_matrices/genre.csv', delimiter=',')
        elif attribute=='keywords':
            similarity_matrix = np.loadtxt(
                'similarity_matrices/keywords.csv', delimiter=',')
    if moviedata is None: moviedata = MovieData()

    if type(ids) == int: ids = [ids]
    attr_series = moviedata.get_col(attribute)
    similarities = []
    for row1 in ids:
        attr1 = attr_series.iloc[row1]
        similarities.append(id_semantic_similarity(
            attr1, row2, attr_series, similarity_matrix=similarity_matrix))
    return np.squeeze(similarities)

## Cast & Director Similarity (TF-IDF cosine, ECLAT-style precomputed matrix)
def cast_director_similarity(row1, row2=None, similarity_matrix=None, moviedata=None):
    """
    Returns the cast + director similarity between movies, from a precomputed M x M matrix.
    Args:
        row1 (int): The positional index of movie 1.
        row2 (int, optional): The positional index of movie 2.
            If None (default), the similarity is calculated between movie 1 and all others.
        similarity_matrix (np.array, optional): The loaded (N_movies, N_movies) cosine matrix.
            If None (default), it is loaded from 'similarity_matrices/cast_director.npy'.
        moviedata (MovieData, optional): Only used when row2 is None, to index the returned Series.
    Note: for repeated calls, load the matrix and moviedata ahead of time and pass them in.

    Returns:
        float if row2 is an int: the cast+director cosine similarity between the two movies.
        pandas.Series if row2 is None: similarities to all movies, indexed positionally.
    """
    if similarity_matrix is None:
        similarity_matrix = np.load('similarity_matrices/cast_director.npy')

    if row2 is not None:
        return float(similarity_matrix[row1, row2])

    if moviedata is None:
        moviedata = MovieData()
    sims = similarity_matrix[row1]
    return pd.Series(sims, index=moviedata.get_data().reset_index(drop=True).index)


## Plot Semantic Similarity
def semantic_similarity_plot(
        row1, row2, attribute='genres',
        similarity_matrix=None, moviedata=None, savepath=None):
    """
    Generates a matrix plot for the genre semantic similarity of a pair of movies
    Args:
        row1 (int): The specific index of the row of the movie 1
        row2 (int): The specific index of the row of movie 2
        similarity_matrix (np.array): The loaded semantic similarity matrix
            If None (default), the similarity matrix is loaded in the function
        moviedata (custom object): The loaded moviedata object
            If None (default), the moviedata object is created in the function
        savepath (str, optional): where to save the figure
            If None (default), figure is not saved
    Note: for repeated function calls, it is reccomended to load in the
            similarity_matrix and moviedata ahead of time and pass the loaded objects
    """
    if attribute not in ['genres', 'keywords']:
        error_text = attribute + ' is not valid semantic attribute.'
        raise ValueError(error_text)
    
    if not np.any(similarity_matrix): 
        if attribute=='genres':
            similarity_matrix = np.loadtxt(
                'similarity_matrices/genre.csv', delimiter=',')
        elif attribute=='keywords':
            similarity_matrix = np.loadtxt(
                'similarity_matrices/keywords.csv', delimiter=',')
    if moviedata is None: moviedata = MovieData()

    moviedf = moviedata.get_data()
    movie1 = moviedf.iloc[row1]['original_title']
    attribute1 = moviedata.entry_as_list(attribute, row1)
    movie2 = moviedf.iloc[row2]['original_title']
    attribute2 = moviedata.entry_as_list(attribute, row2)
    similarity = similarity_matrix[np.ix_(attribute1, attribute2)]
    avg_similarity = (np.sum(similarity) / similarity.size).item()

    if attribute=='genres':
        attributelist = moviedata.get_genres()
    elif attribute=='keywords':
        attributelist = moviedata.get_keywords()
    
    fig, ax = plt.subplots()
    cax = ax.matshow(similarity)
    ax.xaxis.set_ticks_position("bottom")
    ax.set_xticks(
        np.arange(len(attribute2)),
        attributelist[attribute2],
        rotation=45, ha='right')
    ax.set_xlabel('"' + movie2 + '" ' + attribute.capitalize())
    ax.set_yticks(
        np.arange(len(attribute1)), attributelist[attribute1], ha='right')
    ax.set_ylabel('"' + movie1 + '" ' + attribute.capitalize())
    fig.colorbar(cax, ax=ax, label='Semantic Similarity')
    ax.set_title(
        attribute.capitalize() + ' Similarity Bewteen\n"' + movie1 + 
        '" and\n"' + movie2 + '"\n Average Semantic Similarity: {:1.3f}'
        .format(avg_similarity)
    )

    if savepath: fig.savefig(savepath, bbox_inches='tight')

def individual_similarity(ids, row=None, col_name='crew', moviedata=None):
    """
    Check for the presence of specific IDs within a DataFrame column.

    Args:
        ids (int | list[int]): A single ID or a list of IDs to search for.
        row (int | hashable, optional): Specific row index to compare against
            'ids'. If None, compares against all rows.
        col_name (str): The column containing lists of IDs. Defaults to 'crew'.
        moviedata (MovieData, optional): Instance providing access to the
            DataFrame.

    Returns:
        bool | np.ndarray: Boolean if 'row' is provided, otherwise a NumPy
            array of booleans.
    """
    if moviedata is None: moviedata = MovieData()
    if isinstance(ids, (int, float)): ids = [ids]
    target_set = set(ids)
    if row is not None:
        compare_list = moviedata.get_data().at[row, col_name]
        return not target_set.isdisjoint(compare_list)
    else:
        return np.fromiter(
            (
                not target_set.isdisjoint(row_list)
                for row_list in moviedata.get_col(col_name)
            ),
            dtype=bool,
            count=len(moviedata)
        )

def categorical_similarity(row1, row2=None, col_name='crew', moviedata=None):
    """
    Check for overlapping categorical elements between specific rows or across a column.

    This function acts as a wrapper for individual_similarity, extracting the 
    col_name from row1 before performing the comparison.

    Args:
        row1 (int | hashable): The index of the primary row to extract IDs from.
        row2 (int | hashable, optional): The index of a second row to compare against.
        col_name (str): The column containing lists of categories. Defaults to 'crew'.
        moviedata (MovieData, optional): Instance providing access to the DataFrame.

    Returns:
        bool | np.ndarray: Boolean if row2 is provided, otherwise a NumPy array of booleans.
    """
    if moviedata is None: moviedata = MovieData()
    target_ids = moviedata.get_data().at[row1, col_name]
    return individual_similarity(
        ids=target_ids, 
        row=row2, 
        col_name=col_name, 
        moviedata=moviedata
    )


def continuous_similarity(row1, row2=None, attribute='cost', moviedata=None):
    '''
        TODO: Implement a similarity funciton for continuous data
        Potentially should be more than 1 function, up to implementation
    '''
    if moviedata is None: moviedata = MovieData()
    return np.ones(len(moviedata))

def aggregate_similarity(weights=None, moviedata=None, DEV_WEIGHTS_SIZE=3, DEV_DUMMY_DATA=None):
    '''
        TODO: Implement an aggregate similarity funciton for everything
        for specific movie against things
        and
        for specific genre, actor, director etc
    '''
    if moviedata is None: moviedata = MovieData()
    if weights is None: weights = np.ones(DEV_WEIGHTS_SIZE)
    if DEV_DUMMY_DATA is None :
        return np.ones(len(moviedata))
    else:
        return DEV_DUMMY_DATA
