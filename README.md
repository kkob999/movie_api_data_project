# Movie API Data Pipeline

An automated ETL pipeline that fetches movie data from the TMDB API, transforms it, and loads it into a cloud PostgreSQL database on a daily schedule using Apache Airflow.

## Architecture

```mermaid
graph TB
    F[Apache Airflow\nDaily Schedule]
    F --> pipeline

    subgraph pipeline[ETL Pipeline]
        B[Extract] --> C[Transform] --> D[Load]
    end

    A[TMDB API] --> B
    D --> E[Neon PostgreSQL]
```

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12 | Core language |
| Apache Airflow 2.9 | Pipeline orchestration |
| TMDB API | Data source |
| Pandas | Data transformation |
| SQLAlchemy + psycopg2 | Database connection |
| Neon PostgreSQL | Cloud database |
| Docker | Local Airflow environment |

## Project Structure

```
movie_api_data_project/
├── .env                    # API key and DB URL (not committed)
├── .gitignore
├── docker-compose.yaml     # Airflow setup
├── requirements.txt
├── README.md
│
├── dags/
│   └── dags.py             # Airflow DAG definition
│
├── pipeline/
│   ├── __init__.py
│   ├── extract.py          # Fetch data from TMDB API
│   ├── transform.py        # Clean and enrich raw data
│   └── load.py             # Upsert data to Neon PostgreSQL
│
├── setup/
│   ├── __init__.py
│   ├── create_tables.sql   # Raw SQL for table creation
│   └── init_db.py          # Creates tables if not exist
│
└── sql/
    └── analysis.sql        # Analytical queries on top of the data
```

## Data Schema

**movies** table
| Column | Type | Description |
|---|---|---|
| tmdb_id | INTEGER | Primary key from TMDB |
| title | TEXT | Movie title |
| language | VARCHAR(10) | Original language code e.g. `en`, `ja` |
| release_date | DATE | Release date (NULL if not available) |
| rating | NUMERIC(5, 3) | TMDB vote average e.g. `8.444` |
| vote_count | INTEGER | Number of votes on TMDB |
| popularity | NUMERIC(10, 3) | TMDB raw popularity score |
| overview | TEXT | Movie description |
| source_list | VARCHAR(20) | `popular`, `top_rated`, or `both` |
| scraped_at | TIMESTAMPTZ | Timestamp when data was fetched (UTC) |
| source_url | TEXT | TMDB API endpoint used |
| pipeline_version | VARCHAR(20) | Pipeline version tag e.g. `1.0.0` |
| decade | VARCHAR(10) | Derived decade bucket e.g. `2020s` |
| rating_tier | VARCHAR(20) | `Master Piece`, `Excellent`, `Good`, `Average`, `Below Average` |
| popularity_score | NUMERIC(10, 4) | Normalized score: `(rating / 10) × log10(vote_count)` |

**movie_genres** table
| Column | Type | Description |
|---|---|---|
| tmdb_id | INTEGER | Foreign key referencing `movies.tmdb_id` |
| genre_id | INTEGER | TMDB genre ID |
| genre_name | TEXT | Genre name e.g. `Action`, `Drama` |

## Setup & How to Run

### Prerequisites
- Docker Desktop
- Python 3.12
- A free TMDB API key from [themoviedb.org](https://www.themoviedb.org/)
- A free Neon PostgreSQL database from [neon.tech](https://neon.tech/)

### 1. Clone the repo
```bash
git clone https://github.com/kkob999/movie_api_data_project.git
cd movie_api_data_project
```

### 2. Create `.env` file
```
TMDB_API_KEY=8c92760b884e5eb7b4f4db976360eed7
DB_URL=postgresql://neondb_owner:npg_RKrdX6Y3Mpti@ep-wild-smoke-an8wqj0r.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require
```

### 3. Start Airflow
```bash
# first time only
docker compose up airflow-init

# start webserver and scheduler
docker compose up -d airflow-webserver airflow-scheduler
```

### 4. Trigger the pipeline
- Open `http://localhost:8080`
- Login: `admin` / `admin`
- Find `tmdb_pipeline` and click ▶️

The DAG will:
1. Check and create database tables if they don't exist
2. Fetch movies from TMDB popular and top_rated endpoints
3. Transform and enrich the data
4. Upsert into Neon PostgreSQL

### 5. Stop Airflow
```bash
docker compose down
```

## Key Design Decisions

**Upsert over truncate-and-reload** — The pipeline uses `INSERT ... ON CONFLICT DO UPDATE` so each daily run updates existing records with fresh ratings and popularity scores without wiping historical data.

**Junction table for genres** — Genre IDs from TMDB are exploded into a separate `movie_genres` table rather than stored as a comma-separated string. This enables clean SQL joins and proper genre filtering.

**source_list tagging** — Movies are tagged as `popular`, `top_rated`, or `both` to track which list they appear in. Movies in `both` represent the sweet spot between trending and critically acclaimed.

**Deduplication logic** — TMDB's paginated API can return the same movie twice across pages due to real-time ranking shifts. These are handled by sorting by popularity descending and deduplicating on `tmdb_id`.
