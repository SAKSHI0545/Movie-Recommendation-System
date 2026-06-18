import ast
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "datasets"
MODEL_DIR = ROOT_DIR / "models"


def parse_names(value, limit=None):
    try:
        items = ast.literal_eval(value)
        names = [item["name"].replace(" ", "") for item in items if item.get("name")]
        return names[:limit] if limit else names
    except (ValueError, SyntaxError, TypeError):
        return []


def parse_director(value):
    try:
        crew = ast.literal_eval(value)
        for person in crew:
            if person.get("job") == "Director":
                return [person.get("name", "").replace(" ", "")]
    except (ValueError, SyntaxError, TypeError):
        pass
    return []


def build_model():
    movies_path = DATASET_DIR / "tmdb_5000_movies.csv"
    credits_path = DATASET_DIR / "tmdb_5000_credits.csv"

    if not movies_path.exists() or not credits_path.exists():
        raise FileNotFoundError(
            "Place tmdb_5000_movies.csv and tmdb_5000_credits.csv inside datasets/."
        )

    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)

    merged = movies.merge(credits, on="title")
    merged = merged[["id", "title", "overview", "genres", "keywords", "cast", "crew"]]
    merged.dropna(inplace=True)

    merged["genres"] = merged["genres"].apply(parse_names)
    merged["keywords"] = merged["keywords"].apply(parse_names)
    merged["cast"] = merged["cast"].apply(lambda value: parse_names(value, limit=3))
    merged["director"] = merged["crew"].apply(parse_director)
    merged["overview"] = merged["overview"].apply(lambda text: str(text).split())

    merged["tags"] = (
        merged["overview"]
        + merged["genres"]
        + merged["keywords"]
        + merged["cast"]
        + merged["director"]
    )

    model_movies = merged[["id", "title", "tags"]].copy()
    model_movies["tags"] = model_movies["tags"].apply(lambda words: " ".join(words).lower())
    model_movies.rename(columns={"id": "movie_id"}, inplace=True)

    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    vectors = vectorizer.fit_transform(model_movies["tags"]).toarray()
    similarity = cosine_similarity(vectors)

    MODEL_DIR.mkdir(exist_ok=True)
    with (MODEL_DIR / "movies.pkl").open("wb") as movies_file:
        pickle.dump(model_movies[["movie_id", "title", "tags"]], movies_file)
    with (MODEL_DIR / "similarity.pkl").open("wb") as similarity_file:
        pickle.dump(similarity, similarity_file)

    print("Generated models/movies.pkl and models/similarity.pkl")


if __name__ == "__main__":
    build_model()
