# pipeline/pipeline.py
from extract import extract
from transform import transform
from load import load


def run_pipeline():
    print("=" * 40)
    print("Starting TMDB Pipeline")
    print("=" * 40)

    print("\n[1/3] Extracting...")
    raw_df, genre_map = extract()

    print("\n[2/3] Transforming...")
    movies_df, movie_genres_df = transform(raw_df, genre_map)

    print("\n[3/3] Loading...")
    load(movies_df, movie_genres_df)

    print("\n" + "=" * 40)
    print("✅ Pipeline completed successfully.")
    print("=" * 40)


if __name__ == "__main__":
    run_pipeline()