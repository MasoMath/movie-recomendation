"""
Home of Similarity Functions
"""

## Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from MovieData import MovieData

## Semantic Similarity (for Genres and Keywords)
def semantic_similarity(ids, row2=None, attribute='genres', similarity_matrix=None, moviedata=None):
    """
    Returns the similarity between the genres for a pair of movies
    Args:
        ids (int, or list[int]): indicies for "movie 1"
        row2 (int, optional): The specific index of the row of movie 2
            If None (default), the similarity is calculated between movie 1 and all others in the database
        attribute ('genres' or 'keywords'): which attribute to apply semantic similarity to
        similarity_matrix (np.array): The loaded semantic similarity matrix
            If None (default), the similarity matrix is loaded in the function
        moviedata (custom object): The loaded moviedata object
            If None (default), the moviedata object is created in the function
    Note: for repeated function calls, it is reccomended to load in the genre_matrix and moviedata ahead of time
            and pass the loaded objects

    Returns:
        (list[float]) if row2 == (int): the average semantic similarities of the attribute between movie 1 ids and movie 2
        (list[list]) if row2 == None: a list of lists of the average similarity of the attribute between movie 1 ids and all others in the database
        Note: returned list has been "squeezed" to remove singleton dimension(s)

    Warning: If either movie has no listed genres, the similarity returned is NaN
    """
    if attribute not in ['genres', 'keywords']:
        error_text = attribute + ' is not valid semantic attribute.'
        raise ValueError(error_text)
    if not np.any(similarity_matrix): 
        if attribure=='genres':
            similarity_matrix = np.loadtxt('similarity_matrices/genre.csv', delimiter=',')
        elif attribute=='keywords':
            similarity_matrix = np.loadtxt('similarity_matrices/keywords.csv', delimiter=',')
    if moviedata == None:
        moviedata = MovieData()

    if type(ids) == int: ids = [ids] #make it a list if it's only 1 item
    similarities= []
    for row1 in ids:
        attribute1 = moviedata.entry_as_list(attribute, row1)
        
        if row2:
            attribute2 = moviedata.entry_as_list(attribute, row2)
            similarity = similarity_matrix[np.ix_(attribute1, attribute2)]
            similarities.append((np.sum(similarity) / similarity.size).item())
        else:
            attributelist = md.entry_as_list(attribute)
            all_similarities = []
            for attribute2 in attributelist:
                similarity = similarity_matrix[np.ix_(attribute1, attribute2)]
                all_similarities.append((np.sum(similarity) / similarity.size).item())
            similarities.append(all_similarities)
    return np.squeeze(similarities)

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

def categorical_similarity(row1, row2=None, col_name='crew', moviedata=None):
    """
    Check for overlapping categorical elements between specific rows or
        across a column.

    Parameters:

        row1 : int or hashable
            The index of the primary row to compare.

        row2 : int or hashable, optional
            The index of a second row to compare against row1.
            Defaults to None.

        col_name : str, optional
            The column containing lists of categories (e.g., 'original_language')
            Defaults to 'crew'.

        moviedata : MovieData, optional
            An instance of MovieData providing access to the DataFrame. 
            If None, a new MovieData instance is initialized.

    Returns:
        bool or pd.Series
            Returns a boolean if row2 is provided (Row vs Row).
            Returns a pd.Series of booleans if row2 is None (Row vs Column).
    """
    if moviedata is None: moviedata = MovieData()
    df = moviedata.get_data()
    target_set = set(df.at[row1, col_name])
    if row2 is not None: # row v row comparision
        compare_set = set(df.at[row2, col_name])
        return not target_set.isdisjoint(compare_set)
    else: # row v entire column comparision
        results = [
            not target_set.isdisjoint(other_list) 
            for other_list in df[col_name]
        ]
        return pd.Series(results, index=df.index).to_numpy()

def individual_similarity(ids, row=None, col_name='crew', moviedata=None):
    """
    Check for the presence of specific IDs within a DataFrame column.

    Parameters:
    
        ids : int or list of int
            A single ID or a list of IDs to search for in the DataFrame.

        row : int or hashable, optional
            The index of a specific row to compare against 'ids'. 
            If provided, the function returns a single boolean.

        col_name : str, optional
            The column containing lists of IDs. Defaults to 'crew'.

        moviedata : MovieData, optional
            An instance of MovieData providing access to the DataFrame.

    Returns:
        bool or pd.Series
            Returns a boolean if 'row' index is provided.
            Returns a pd.Series of booleans if 'row' is None.
    """
    if moviedata is None: moviedata = MovieData()
    if isinstance(ids,int): ids = [ids]
    target_set = set(ids)
    df = moviedata.get_data()
    if row is not None:
        compare_list = df.at[row, col_name]
        return not target_set.isdisjoint(compare_list)
    else:
        results = [
            not target_set.isdisjoint(row_list) 
            for row_list in df[col_name]
        ]
        return pd.Series(results, index=df.index).to_numpy()

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
