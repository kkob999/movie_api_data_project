# pipeline/load.py
from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

def get_engine():
    return create_engine(
        DB_URL, 
        pool_pre_ping=True,
        # This makes inserts MUCH faster for Postgres
        executemany_mode='values',
        executemany_values_page_size=1000
    )

def load(movies_df: pd.DataFrame, movie_genres_df: pd.DataFrame) -> None:
    print("Starting Load...")
    engine = get_engine()

    try:
        with engine.begin() as conn:
            if not movies_df.empty:
                records = movies_df.to_dict(orient="records")
                conn.execute(text("""
                    INSERT INTO movies (
                        tmdb_id, title, language, release_date,
                        rating, vote_count, popularity, overview,
                        source_list, scraped_at, source_url,
                        pipeline_version, decade, rating_tier, popularity_score
                    ) VALUES (
                        :tmdb_id, :title, :language, :release_date,
                        :rating, :vote_count, :popularity, :overview,
                        :source_list, :scraped_at, :source_url,
                        :pipeline_version, :decade, :rating_tier, :popularity_score
                    )
                    ON CONFLICT (tmdb_id) DO UPDATE SET
                        rating           = EXCLUDED.rating,
                        vote_count       = EXCLUDED.vote_count,
                        popularity       = EXCLUDED.popularity,
                        scraped_at       = EXCLUDED.scraped_at
                """), records)

            if not movie_genres_df.empty:
                genre_records = movie_genres_df.to_dict(orient="records")
                conn.execute(text("""
                    INSERT INTO movie_genres (tmdb_id, genre_id, genre_name)
                    VALUES (:tmdb_id, :genre_id, :genre_name)
                    ON CONFLICT (tmdb_id, genre_id) DO NOTHING
                """), genre_records)
                
        print("Load Finished!")
    finally:
        engine.dispose()