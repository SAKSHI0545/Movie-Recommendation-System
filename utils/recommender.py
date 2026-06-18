import pickle
from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MOVIES_PATH = MODEL_DIR / "movies.pkl"
SIMILARITY_PATH = MODEL_DIR / "similarity.pkl"


class MovieRecommender:
    """Loads prebuilt similarity files and returns content-based matches."""

    def __init__(self):
        self.movies = None
        self.similarity = None
        self.load()

    @property
    def is_ready(self):
        return self.movies is not None and self.similarity is not None

    def load(self):
        try:
            if MOVIES_PATH.exists() and SIMILARITY_PATH.exists():
                with MOVIES_PATH.open("rb") as movies_file:
                    self.movies = pickle.load(movies_file)
                with SIMILARITY_PATH.open("rb") as similarity_file:
                    self.similarity = pickle.load(similarity_file)
        except Exception as exc:
            print("RECOMMENDER LOAD ERROR:", exc)
            self.movies = None
            self.similarity = None

    def recommend(self, title=None, tmdb_id=None, limit=10):
        if not self.is_ready:
            return []

        index = self._find_index(title=title, tmdb_id=tmdb_id)
        if index is None:
            return []

        distances = sorted(
            list(enumerate(self.similarity[index])),
            reverse=True,
            key=lambda item: item[1],
        )

        recommendations = []
        for movie_index, score in distances[1 : limit + 1]:
            row = self.movies.iloc[movie_index]
            recommendations.append(
                {
                    "movie_id": int(row["movie_id"]),
                    "tmdb_id": int(row["movie_id"]),
                    "title": row["title"],
                    "similarity": round(float(score), 3),
                }
            )
        return recommendations

    def _find_index(self, title=None, tmdb_id=None):
        if tmdb_id:
            matches = self.movies[self.movies["movie_id"] == int(tmdb_id)]
            if not matches.empty:
                return matches.index[0]

        if title:
            normalized = title.strip().lower()
            titles = self.movies["title"].str.lower()
            exact = self.movies[titles == normalized]
            if not exact.empty:
                return exact.index[0]

            contains = self.movies[titles.str.contains(normalized, regex=False, na=False)]
            if not contains.empty:
                return contains.index[0]

        return None
