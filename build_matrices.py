"""
Generates the four .npy similarity matrices required by the backend.
Run from the project root with the venv activated:

    python build_matrices.py

Reads:  similarity_matrices/genre.csv, similarity_matrices/keywords.csv
Writes: similarity_matrices/cast_director.npy
        similarity_matrices/production_companies.npy
        similarity_matrices/genre_movie.npy
        similarity_matrices/keywords_movie.npy
"""

import os, time
from collections import defaultdict
import numpy as np
from MovieData import MovieData

OUTDIR = 'similarity_matrices'
os.makedirs(OUTDIR, exist_ok=True)

md = MovieData()
df = md.get_data().reset_index(drop=True)


def eclat_cosine_matrix(df, col, dtype=np.float32):
    N = len(df)
    inv = defaultdict(list)
    for pos, persons in enumerate(df[col].values):
        if isinstance(persons, list):
            for p in set(persons):
                inv[p].append(pos)
    if not inv:
        return np.zeros((N, N), dtype=dtype)

    max_pid = max(inv.keys())
    idf = np.zeros(max_pid + 1, dtype=np.float64)
    for p, movies in inv.items():
        idf[p] = np.log(N / len(movies))

    row_norm_sq = np.zeros(N, dtype=np.float64)
    for pos, persons in enumerate(df[col].values):
        if isinstance(persons, list):
            for p in set(persons):
                row_norm_sq[pos] += idf[p] ** 2

    S = np.zeros((N, N), dtype=np.float64)
    for p, movies in inv.items():
        if len(movies) < 2:
            continue
        m = np.asarray(movies, dtype=np.int64)
        S[np.ix_(m, m)] += idf[p] ** 2

    row_norms = np.sqrt(row_norm_sq)
    safe = np.where(row_norms > 0, row_norms, 1.0)
    S /= np.outer(safe, safe)
    mask = row_norms == 0
    if mask.any():
        S[mask, :] = 0
        S[:, mask] = 0
    np.fill_diagonal(S, np.where(mask, 0.0, 1.0))
    return S.astype(dtype)


def build_movie_attr_matrix(df, col, num_attrs):
    N = len(df)
    M = np.zeros((N, num_attrs), dtype=np.float32)
    for i, attrs in enumerate(df[col].values):
        if isinstance(attrs, list) and attrs:
            w = 1.0 / len(attrs)
            for a in attrs:
                M[i, a] = w
    return M


def lift_to_movie_matrix(G, A):
    S = (G @ A @ G.T).astype(np.float32)
    S = np.clip(S, 0.0, 1.0)
    empty = G.sum(axis=1) == 0
    np.fill_diagonal(S, np.where(empty, 0.0, 1.0))
    return S


# --- cast_director ---
print('Building cast_director...', flush=True)
t = time.time()
S_cast = eclat_cosine_matrix(df, 'cast')
S_dir  = eclat_cosine_matrix(df, 'crew')
S_cd   = (0.7 * S_cast + 0.3 * S_dir).astype(np.float32)
np.save(f'{OUTDIR}/cast_director.npy', S_cd)
print(f'  done ({time.time()-t:.1f}s)  shape={S_cd.shape}  size={os.path.getsize(f"{OUTDIR}/cast_director.npy")/1e6:.1f}MB')

# --- production_companies ---
print('Building production_companies...', flush=True)
t = time.time()
S_prod = eclat_cosine_matrix(df, 'production_companies')
np.save(f'{OUTDIR}/production_companies.npy', S_prod)
print(f'  done ({time.time()-t:.1f}s)  shape={S_prod.shape}')

# --- genre_movie & keywords_movie ---
print('Loading attribute-level CSVs...', flush=True)
genre_mat = np.loadtxt(f'{OUTDIR}/genre.csv',    delimiter=',').astype(np.float32)
kw_mat    = np.loadtxt(f'{OUTDIR}/keywords.csv', delimiter=',').astype(np.float32)
print(f'  genre_mat={genre_mat.shape}  kw_mat={kw_mat.shape}')

print('Building genre_movie...', flush=True)
t = time.time()
G_genre      = build_movie_attr_matrix(df, 'genres', genre_mat.shape[0])
S_genre_movie = lift_to_movie_matrix(G_genre, genre_mat)
np.save(f'{OUTDIR}/genre_movie.npy', S_genre_movie)
print(f'  done ({time.time()-t:.1f}s)  shape={S_genre_movie.shape}')

print('Building keywords_movie...', flush=True)
t = time.time()
G_kw        = build_movie_attr_matrix(df, 'keywords', kw_mat.shape[0])
S_kw_movie  = lift_to_movie_matrix(G_kw, kw_mat)
np.save(f'{OUTDIR}/keywords_movie.npy', S_kw_movie)
print(f'  done ({time.time()-t:.1f}s)  shape={S_kw_movie.shape}')

print('\nAll matrices saved to similarity_matrices/')
