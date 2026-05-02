"""
Home of Similarity Functions
"""

## Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from MovieData import MovieData

## Semantic Similarity (for Genres and Keywords)
def semantic_similarity(row1, row2=None, attribute='genres', similarity_matrix=None, moviedata=None):
    """
    Returns the similarity between the genres for a pair of movies
    Args:
        row1 (int): The specific index of the row of the movie 1
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
        (float) if row2 == (int): the average semantic similarity of the attribute between movie 1 and movie 2
        (pandas.Series) if row2 == None: a pandas.Series of the average similarity of the attribute between movie 1 and all others in the database

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

    attribute1 = moviedata.entry_as_list(attribute, row1)
    
    if row2:
        attribute2 = moviedata.entry_as_list(attribute, row2)
        similarity = similarity_matrix[np.ix_(attribute1, attribute2)]
        return (np.sum(similarity) / similarity.size).item()
    else:
        attributelist = md.entry_as_list(attribute)
        all_similarities = []
        for attribute2 in attributelist:
            similarity = similarity_matrix[np.ix_(attribute1, attribute2)]
            all_similarities.append((np.sum(similarity) / similarity.size).item())
        return pd.Series(all_similarities, index=attributelist.index)

## Plot Semantic Similarity
def semantic_similarity_plot(row1, row2, attribute='genres', similarity_matrix=None, moviedata=None, savepath=None):
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
    Note: for repeated function calls, it is reccomended to load in the similarity_matrix and moviedata ahead of time
            and pass the loaded objects
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
    ax.set_xticks(np.arange(len(attribute2)), attributelist[attribute2], rotation=45, ha='right')
    ax.set_xlabel('"' + movie2 + '" ' + attribute.capitalize())
    ax.set_yticks(np.arange(len(attribute1)), attributelist[attribute1], ha='right')
    ax.set_ylabel('"' + movie1 + '" ' + attribute.capitalize())
    fig.colorbar(cax, ax=ax, label='Semantic Similarity')
    title = attribute.capitalize() + ' Similarity Bewteen\n"' + movie1 + '" and\n"' + movie2 + '"\n Average Semantic Similarity: {:1.3f}'.format(avg_similarity)
    ax.set_title(title)

    if savepath:
        fig.savefig(savepath, bbox_inches='tight')