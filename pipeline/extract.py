# pipeline/extract.py
import requests
import pandas as pd
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
MAX_PAGES = 5

HEADERS = {"accept": "application/json"}

ENDPOINTS = {
    "popular":   "/movie/popular",
    "top_rated": "/movie/top_rated",
}


def fetch_genre_map() -> dict:
    url = f"{BASE_URL}/genre/movie/list"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    genres = response.json().get("genres", [])
    print({g["id"]: g["name"] for g in genres})
    return {g["id"]: g["name"] for g in genres}


def fetch_page(endpoint: str, page: int) -> tuple:
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY, "language": "en-US", "page": page}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("results", []), data.get("total_pages", 1)


def fetch_movies(source_list: str, endpoint: str) -> list:
    all_movies = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for page in range(1, MAX_PAGES + 1):
        results, total_pages = fetch_page(endpoint, page)
        print(f"  [{source_list}] page {page}/{min(MAX_PAGES, total_pages)} — {len(results)} movies")

        for movie in results:
            movie["source_list"] = source_list
            movie["scraped_at"] = scraped_at
            movie["source_url"] = f"{BASE_URL}{endpoint}?page={page}"
            movie["pipeline_version"] = "1.0.0"
            all_movies.append(movie)

        if page >= total_pages:
            break

        time.sleep(0.25)

    return all_movies


def extract() -> tuple[pd.DataFrame, dict]:
    print("Fetching genre map...")
    genre_map = fetch_genre_map()

    raw_movies = []
    for source_list, endpoint in ENDPOINTS.items():
        print(f"\nFetching [{source_list}]...")
        movies = fetch_movies(source_list, endpoint)
        raw_movies.extend(movies)

    raw_df = pd.DataFrame(raw_movies)

    # handle cross-list and within-list duplicates
    both_ids = set(
        raw_df[raw_df["source_list"] == "popular"]["id"]
    ) & set(
        raw_df[raw_df["source_list"] == "top_rated"]["id"]
    )

    raw_df["source_list"] = raw_df["id"].apply(
        lambda x: "both" if x in both_ids else
        raw_df.loc[raw_df["id"] == x, "source_list"].iloc[0]
    )

    raw_df = raw_df.sort_values("popularity", ascending=False)
    raw_df = raw_df.drop_duplicates(subset=["id"], keep="first")

    print(f"\nExtracted {len(raw_df)} movies after dedup.")
    print(f"Movies in both lists: {len(both_ids)}")

    return raw_df, genre_map