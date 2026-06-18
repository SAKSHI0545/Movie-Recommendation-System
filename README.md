# AI-Powered Movie Recommendation Platform

MovieFlix is a Flask and MySQL movie recommendation app upgraded with an AI-powered content-based recommendation engine. It keeps the original registration, login, dashboard, search, favorites, and TMDB integration while adding cosine-similarity recommendations, watchlist, search history, and recently viewed movies.

## Tech Stack

- Python and Flask
- MySQL
- Jinja2 templates
- HTML and CSS
- TMDB API for movie metadata and posters
- pandas, numpy, scikit-learn
- CountVectorizer and cosine similarity

## Features

- User registration and session-based login
- TMDB movie search with poster, title, rating, and release year
- Detailed movie pages with poster, overview, genres, release date, runtime, rating, language, popularity, cast, and optional trailer link
- Content-based "You May Also Like" recommendations from your own trained model
- User-specific favorites stored in MySQL
- User-specific watchlist stored in MySQL
- Recent search history per user
- Recently viewed movies on the dashboard
- Dashboard sections for trending movies, recently viewed, favorites, watchlist, and recommended movies
- Netflix-inspired dark responsive interface

## Dataset

Download these files and place them in the `datasets/` folder:

- `tmdb_5000_movies.csv`
- `tmdb_5000_credits.csv`

The model uses:

- genres
- keywords
- cast
- director
- overview

Generate the model files with:

```bash
python ml/train_recommender.py
```

This creates:

- `models/movies.pkl`
- `models/similarity.pkl`

Flask loads these pickle files at startup. It does not rebuild the model on every request.

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Create a MySQL database named `movie_app`, then update `database.py` if your MySQL username or password is different.

The app reads the TMDB API key from either:

- the `TMDB_API_KEY` environment variable
- the first line of the existing `api` file

## Running The Project

Train the recommendation model first if the dataset files are available:

```bash
python ml/train_recommender.py
```

Start Flask:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The app creates the new `watchlist`, `search_history`, and `recently_viewed` tables automatically if they do not exist.

## Screenshots

Add screenshots here:

- Login page
- Dashboard
- Search results
- Movie details page
- Favorites and watchlist

## Future Enhancements

- Password hashing with Werkzeug
- Pagination for search and library pages
- User rating feedback to improve recommendations
- Movie review comments
- Admin panel for managing local movies
- Deployment configuration for production hosting
