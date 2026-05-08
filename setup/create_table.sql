DROP TABLE IF EXISTS movie_genres;
DROP TABLE IF EXISTS movies;

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