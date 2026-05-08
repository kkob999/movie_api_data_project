# pipeline/transform.py
import pandas as pd
import math
import ast


def rating_tier(r: float) -> str:
    if r >= 9.0:   return "Master Piece"
    elif r >= 8.0: return "Excellent"
    elif r >= 7.0: return "Good"
    elif r >= 6.0: return "Average"
    else:          return "Below Average"
    
def parse_release_date(val):
    if pd.isna(val):
        return None
    # if bigint (unix ms from read_json), convert via unit
    if isinstance(val, (int, float)):
        return pd.to_datetime(val, unit="ms").date()
    # if string "2024-03-15" from TMDB directly
    return pd.to_datetime(val, errors="coerce").date()


def transform(df: pd.DataFrame, genre_map: dict) -> tuple[pd.DataFrame, pd.DataFrame]:

    # ── movies_df ─────────────────────────────────────────────────────────────
    movies_df = df[[
        "id", "title", "original_language", "release_date",
        "vote_average", "vote_count", "popularity",
        "overview", "source_list", "scraped_at",
        "source_url", "pipeline_version"
    ]].rename(columns={
        "id":                "tmdb_id",
        "original_language": "language",
        "vote_average":      "rating",
    }).copy()

    # release_date → proper date
    movies_df["release_date"] = movies_df["release_date"].apply(parse_release_date)

    # decade bucket
    movies_df["decade"] = movies_df["release_date"].apply(
    lambda x: f"{(x.year // 10 * 10)}s" if x is not None else "Unknown"
)

    # rating tier
    movies_df["rating_tier"] = movies_df["rating"].apply(rating_tier)

    # popularity score
    movies_df["popularity_score"] = movies_df.apply(
        lambda row: round((row["rating"] / 10) * math.log10(row["vote_count"]), 4)
        if row["vote_count"] > 0 else 0,
        axis=1
    )

    # scraped_at → proper timestamp
    movies_df["scraped_at"] = pd.to_datetime(movies_df["scraped_at"], utc=True, errors="coerce")

    # ── movie_genres_df ────────────────────────────────────────────────────────
    genre_map = {int(k): v for k, v in genre_map.items()}
    genres_rows = []
    
    for _, row in df.iterrows():
        print("RAW:", row["genre_ids"], type(row["genre_ids"]))
        for genre_id in row["genre_ids"]:
            
            print("GENRE_ID:", genre_id, type(genre_id))
            print(genre_map.get(genre_id, "Unknown"))

            genres_rows.append({
                "tmdb_id": row["id"],
                "genre_id": genre_id,
                "genre_name": genre_map.get(genre_id, "Unknown")
            })

    movie_genres_df = pd.DataFrame(genres_rows)

    print(f"movies_df:       {len(movies_df)} rows")
    print(f"movie_genres_df: {len(movie_genres_df)} rows")

    return movies_df, movie_genres_df