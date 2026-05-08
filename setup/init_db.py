# setup/init_db.py
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")


def init_db():
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'movies'
            );
        """))
        movies_exists = result.scalar()

        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'movie_genres'
            );
        """))
        genres_exists = result.scalar()

        if movies_exists and genres_exists:
            print("✅ Tables already exist — skipping creation.")
            return

        print("⚠️ Tables not found — creating...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                tmdb_id          INTEGER PRIMARY KEY,
                title            TEXT NOT NULL,
                language         VARCHAR(10),
                release_date     DATE,
                rating           NUMERIC(3, 1),
                vote_count       INTEGER,
                popularity       NUMERIC(10, 3),
                overview         TEXT,
                source_list      VARCHAR(20),
                scraped_at       TIMESTAMPTZ,
                source_url       TEXT,
                pipeline_version VARCHAR(20),
                decade           VARCHAR(10),
                rating_tier      VARCHAR(20),
                popularity_score NUMERIC(10, 4)
            );

            CREATE TABLE IF NOT EXISTS movie_genres (
                tmdb_id    INTEGER REFERENCES movies(tmdb_id),
                genre_id   INTEGER,
                genre_name TEXT,
                PRIMARY KEY (tmdb_id, genre_id)
            );
        """))
        conn.commit()
        print("✅ Tables created successfully.")


if __name__ == "__main__":
    init_db()