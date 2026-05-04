import kagglehub

path = kagglehub.dataset_download(
    "tmdb/tmdb-movie-metadata", output_dir="./kaggledata"
)

print("Path to dataset files:", path)
