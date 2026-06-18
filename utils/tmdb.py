import os
from pathlib import Path

import requests


BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
DEFAULT_POSTER = "https://via.placeholder.com/500x750/1f1f1f/ffffff?text=No+Poster"


def get_api_key():
    """Read the TMDB key from an environment variable or the legacy api file."""
    env_key = os.getenv("TMDB_API_KEY")
    if env_key:
        return env_key.strip()

    api_file = Path(__file__).resolve().parent.parent / "api"
    if api_file.exists():
        first_line = api_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        if first_line:
            return first_line[0].strip()

    return ""


def poster_url(path, size="w500"):
    if not path:
        return DEFAULT_POSTER
    if str(path).startswith("http"):
        return path
    return f"{IMAGE_BASE_URL}/{size}{path}"


def backdrop_url(path, size="original"):
    if not path:
        return ""
    if str(path).startswith("http"):
        return path
    return f"{IMAGE_BASE_URL}/{size}{path}"


class TMDBClient:
    """Small wrapper around TMDB requests used by Flask routes."""

    def __init__(self):
        self.api_key = get_api_key()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MovieRecommendationApp/1.0"})

    def _get(self, endpoint, params=None):
        if not self.api_key:
            return {}

        query = {"api_key": self.api_key}
        if params:
            query.update(params)

        try:
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                params=query,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print("TMDB ERROR:", exc)
            return {}

    def search_movies(self, query):
        data = self._get("/search/movie", {"query": query})
        return [normalize_search_result(movie) for movie in data.get("results", [])]

    def popular_movies(self, limit=10):
        data = self._get("/movie/popular")
        movies = [normalize_search_result(movie) for movie in data.get("results", [])]
        return movies[:limit]

    def movie_details(self, tmdb_id):
        data = self._get(
            f"/movie/{tmdb_id}",
            {"append_to_response": "credits,videos"},
        )
        if not data or data.get("success") is False:
            return {}
        return normalize_movie_details(data)


def normalize_search_result(movie):
    release_date = movie.get("release_date") or ""
    return {
        "id": movie.get("id"),
        "tmdb_id": movie.get("id"),
        "title": movie.get("title") or movie.get("name") or "Untitled",
        "overview": movie.get("overview") or "",
        "poster_url": poster_url(movie.get("poster_path")),
        "backdrop_url": backdrop_url(movie.get("backdrop_path")),
        "rating": round(float(movie.get("vote_average") or 0), 1),
        "release_date": release_date,
        "release_year": release_date[:4] if release_date else "N/A",
        "popularity": round(float(movie.get("popularity") or 0), 1),
    }


def normalize_movie_details(movie):
    credits = movie.get("credits") or {}
    cast = [
        person.get("name")
        for person in credits.get("cast", [])[:5]
        if person.get("name")
    ]
    directors = [
        person.get("name")
        for person in credits.get("crew", [])
        if person.get("job") == "Director"
    ]
    trailers = [
        video
        for video in (movie.get("videos") or {}).get("results", [])
        if video.get("site") == "YouTube" and video.get("type") == "Trailer"
    ]
    release_date = movie.get("release_date") or ""

    return {
        "id": movie.get("id"),
        "tmdb_id": movie.get("id"),
        "title": movie.get("title") or "Untitled",
        "overview": movie.get("overview") or "No overview available.",
        "poster_url": poster_url(movie.get("poster_path")),
        "backdrop_url": backdrop_url(movie.get("backdrop_path")),
        "rating": round(float(movie.get("vote_average") or 0), 1),
        "release_date": release_date,
        "release_year": release_date[:4] if release_date else "N/A",
        "genres": [genre.get("name") for genre in movie.get("genres", [])],
        "runtime": movie.get("runtime") or 0,
        "language": (movie.get("original_language") or "N/A").upper(),
        "popularity": round(float(movie.get("popularity") or 0), 1),
        "cast": cast,
        "director": ", ".join(directors[:2]),
        "trailer_key": trailers[0].get("key") if trailers else "",
    }
