from flask import Flask, redirect, render_template, request, session, url_for

from database import conn, cursor
from utils.recommender import MovieRecommender
from utils.tmdb import DEFAULT_POSTER, TMDBClient


app = Flask(__name__)
app.secret_key = "movie_secret_key"

tmdb_client = TMDBClient()
recommender = MovieRecommender()


def execute(query, values=None, commit=False):
    """Run a query using the existing shared MySQL connection."""
    conn.ping(reconnect=True, attempts=1, delay=0)
    cursor.execute(query, values or ())
    if commit:
        conn.commit()


def fetchone_dict(query, values=None):
    execute(query, values)
    row = cursor.fetchone()
    if not row:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def fetchall_dict(query, values=None):
    execute(query, values)
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def ensure_column(table_name, column_name, definition):
    execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
    if not cursor.fetchone():
        execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}",
            commit=True,
        )


def ensure_schema():
    """Create the new tables and columns used by the upgraded platform."""
    execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            genre VARCHAR(255),
            rating FLOAT,
            overview TEXT,
            poster_url VARCHAR(500),
            tmdb_id INT,
            release_date VARCHAR(20),
            runtime INT,
            language VARCHAR(50),
            popularity FLOAT
        )
        """,
        commit=True,
    )

    movie_columns = {
        "genre": "VARCHAR(255)",
        "rating": "FLOAT",
        "overview": "TEXT",
        "poster_url": "VARCHAR(500)",
        "tmdb_id": "INT",
        "release_date": "VARCHAR(20)",
        "runtime": "INT",
        "language": "VARCHAR(50)",
        "popularity": "FLOAT",
    }
    for column, definition in movie_columns.items():
        ensure_column("movies", column, definition)

    execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        commit=True,
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            movie_id INT,
            tmdb_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        commit=True,
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS search_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            query VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        commit=True,
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS recently_viewed (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            movie_id INT,
            tmdb_id INT,
            title VARCHAR(255) NOT NULL,
            poster_url VARCHAR(500),
            rating FLOAT,
            release_year VARCHAR(10),
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        commit=True,
    )


def login_required():
    return "user_id" in session


def movie_detail_url(movie):
    if movie.get("tmdb_id"):
        return url_for("tmdb_movie", movie_id=movie["tmdb_id"])
    return url_for("movie_details", movie_id=movie["id"])


def normalize_local_movie(movie):
    if not movie:
        return {}

    release_date = str(movie.get("release_date") or "")
    normalized = {
        "id": movie.get("id"),
        "local_id": movie.get("id"),
        "tmdb_id": movie.get("tmdb_id"),
        "title": movie.get("title") or "Untitled",
        "genre": movie.get("genre") or "Unknown",
        "genres": [genre.strip() for genre in str(movie.get("genre") or "").split(",") if genre.strip()],
        "rating": round(float(movie.get("rating") or 0), 1),
        "overview": movie.get("overview") or "No overview available.",
        "poster_url": movie.get("poster_url") or movie.get("poster") or DEFAULT_POSTER,
        "release_date": release_date,
        "release_year": release_date[:4] if release_date else "N/A",
        "runtime": movie.get("runtime") or 0,
        "language": (movie.get("language") or "N/A").upper(),
        "popularity": round(float(movie.get("popularity") or 0), 1),
    }
    normalized["detail_url"] = movie_detail_url(normalized)
    return normalized


def normalize_many_local(movies):
    return [normalize_local_movie(movie) for movie in movies]


def ensure_local_movie_from_tmdb(tmdb_id):
    movie = tmdb_client.movie_details(tmdb_id)
    if not movie:
        return None

    existing = fetchone_dict("SELECT * FROM movies WHERE tmdb_id = %s", (tmdb_id,))
    genre_text = ", ".join(movie.get("genres") or [])
    values = (
        movie["title"],
        genre_text,
        movie["rating"],
        movie["overview"],
        movie["poster_url"],
        movie["tmdb_id"],
        movie["release_date"],
        movie["runtime"],
        movie["language"],
        movie["popularity"],
    )

    if existing:
        execute(
            """
            UPDATE movies
            SET title=%s, genre=%s, rating=%s, overview=%s, poster_url=%s,
                tmdb_id=%s, release_date=%s, runtime=%s, language=%s, popularity=%s
            WHERE id=%s
            """,
            values + (existing["id"],),
            commit=True,
        )
        return existing["id"]

    execute(
        """
        INSERT INTO movies
            (title, genre, rating, overview, poster_url, tmdb_id, release_date,
             runtime, language, popularity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        values,
        commit=True,
    )
    return cursor.lastrowid


def add_favorite_movie(user_id, movie_id):
    execute(
        "SELECT id FROM favorites WHERE user_id=%s AND movie_id=%s",
        (user_id, movie_id),
    )
    if not cursor.fetchone():
        execute(
            "INSERT INTO favorites(user_id, movie_id) VALUES(%s, %s)",
            (user_id, movie_id),
            commit=True,
        )


def add_watchlist_movie(user_id, movie_id, tmdb_id=None):
    execute(
        "SELECT id FROM watchlist WHERE user_id=%s AND movie_id=%s",
        (user_id, movie_id),
    )
    if not cursor.fetchone():
        execute(
            "INSERT INTO watchlist(user_id, movie_id, tmdb_id) VALUES(%s, %s, %s)",
            (user_id, movie_id, tmdb_id),
            commit=True,
        )


def get_user_favorites(user_id, limit=None):
    limit_sql = "LIMIT %s" if limit else ""
    values = (user_id, limit) if limit else (user_id,)
    rows = fetchall_dict(
        f"""
        SELECT movies.*
        FROM movies
        JOIN favorites ON movies.id = favorites.movie_id
        WHERE favorites.user_id = %s
        ORDER BY movies.id DESC
        {limit_sql}
        """,
        values,
    )
    return normalize_many_local(rows)


def get_user_watchlist(user_id, limit=None):
    limit_sql = "LIMIT %s" if limit else ""
    values = (user_id, limit) if limit else (user_id,)
    rows = fetchall_dict(
        f"""
        SELECT movies.*
        FROM movies
        JOIN watchlist ON movies.id = watchlist.movie_id
        WHERE watchlist.user_id = %s
        ORDER BY movies.id DESC
        {limit_sql}
        """,
        values,
    )
    return normalize_many_local(rows)


def save_search(user_id, query):
    if query:
        execute(
            "INSERT INTO search_history(user_id, query) VALUES(%s, %s)",
            (user_id, query),
            commit=True,
        )


def get_recent_searches(user_id):
    rows = fetchall_dict(
        """
        SELECT query, MAX(created_at) AS searched_at
        FROM search_history
        WHERE user_id = %s
        GROUP BY query
        ORDER BY searched_at DESC
        LIMIT 10
        """,
        (user_id,),
    )
    return [row["query"] for row in rows]


def track_recently_viewed(user_id, movie):
    if not user_id or not movie:
        return

    execute(
        """
        DELETE FROM recently_viewed
        WHERE user_id=%s AND (
            (movie_id IS NOT NULL AND movie_id=%s)
            OR (tmdb_id IS NOT NULL AND tmdb_id=%s)
        )
        """,
        (user_id, movie.get("local_id") or movie.get("id"), movie.get("tmdb_id")),
        commit=True,
    )
    execute(
        """
        INSERT INTO recently_viewed
            (user_id, movie_id, tmdb_id, title, poster_url, rating, release_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            movie.get("local_id"),
            movie.get("tmdb_id"),
            movie.get("title"),
            movie.get("poster_url"),
            movie.get("rating"),
            movie.get("release_year"),
        ),
        commit=True,
    )


def get_recently_viewed(user_id, limit=10):
    rows = fetchall_dict(
        """
        SELECT movie_id AS id, movie_id AS local_id, tmdb_id, title, poster_url,
               rating, release_year
        FROM recently_viewed
        WHERE user_id=%s
        ORDER BY viewed_at DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    for row in rows:
        row["detail_url"] = movie_detail_url(row)
    return rows


def enrich_recommendations(recommendations, limit=10):
    enriched = []
    seen = set()

    for recommendation in recommendations:
        tmdb_id = recommendation.get("tmdb_id") or recommendation.get("movie_id")
        if not tmdb_id or tmdb_id in seen:
            continue

        movie = tmdb_client.movie_details(tmdb_id)
        if movie:
            movie["detail_url"] = url_for("tmdb_movie", movie_id=tmdb_id)
            enriched.append(movie)
            seen.add(tmdb_id)

        if len(enriched) >= limit:
            break

    return enriched


def recommend_for_movie(movie, limit=10):
    recommendations = recommender.recommend(
        title=movie.get("title"),
        tmdb_id=movie.get("tmdb_id"),
        limit=limit,
    )
    return enrich_recommendations(recommendations, limit=limit)


def recommend_for_user(user_id, limit=10):
    seeds = []
    for movie in get_user_favorites(user_id, limit=5):
        seeds.append(movie)
    for movie in get_user_watchlist(user_id, limit=5):
        seeds.append(movie)
    for movie in get_recently_viewed(user_id, limit=5):
        seeds.append(movie)

    recommendations = []
    seen = set()
    for seed in seeds:
        for movie in recommender.recommend(
            title=seed.get("title"),
            tmdb_id=seed.get("tmdb_id"),
            limit=5,
        ):
            tmdb_id = movie.get("tmdb_id")
            if tmdb_id and tmdb_id not in seen:
                recommendations.append(movie)
                seen.add(tmdb_id)

    enriched = enrich_recommendations(recommendations, limit=limit)
    if enriched:
        return enriched

    popular = tmdb_client.popular_movies(limit=limit)
    for movie in popular:
        movie["detail_url"] = url_for("tmdb_movie", movie_id=movie["tmdb_id"])
    return popular


def get_trending_movies(limit=10):
    popular = tmdb_client.popular_movies(limit=limit)
    if popular:
        for movie in popular:
            movie["detail_url"] = url_for("tmdb_movie", movie_id=movie["tmdb_id"])
        return popular

    rows = fetchall_dict("SELECT * FROM movies ORDER BY rating DESC LIMIT %s", (limit,))
    return normalize_many_local(rows)


@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        execute(
            "INSERT INTO users(username, password) VALUES(%s, %s)",
            (username, password),
            commit=True,
        )
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password),
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")
        error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect("/login")

    user_id = session["user_id"]
    return render_template(
        "dashboard.html",
        username=session["username"],
        trending=get_trending_movies(limit=10),
        favorite_movies=get_user_favorites(user_id, limit=10),
        watchlist_movies=get_user_watchlist(user_id, limit=10),
        recently_viewed=get_recently_viewed(user_id, limit=10),
        recommended_movies=recommend_for_user(user_id, limit=10),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/movies")
def movies():
    if not login_required():
        return redirect("/login")

    all_movies = normalize_many_local(fetchall_dict("SELECT * FROM movies"))
    return render_template("movies.html", movies=all_movies)


@app.route("/favorite/<int:movie_id>")
def favorite(movie_id):
    if not login_required():
        return redirect("/login")

    add_favorite_movie(session["user_id"], movie_id)
    return redirect(request.referrer or "/movies")


@app.route("/favorite/tmdb/<int:tmdb_id>")
def favorite_tmdb(tmdb_id):
    if not login_required():
        return redirect("/login")

    movie_id = ensure_local_movie_from_tmdb(tmdb_id)
    if movie_id:
        add_favorite_movie(session["user_id"], movie_id)
    return redirect(request.referrer or url_for("tmdb_movie", movie_id=tmdb_id))


@app.route("/favorites")
def favorites():
    if not login_required():
        return redirect("/login")

    return render_template(
        "favorites.html",
        movies=get_user_favorites(session["user_id"]),
    )


@app.route("/remove_favorite/<int:movie_id>")
def remove_favorite(movie_id):
    if not login_required():
        return redirect("/login")

    execute(
        "DELETE FROM favorites WHERE user_id = %s AND movie_id = %s",
        (session["user_id"], movie_id),
        commit=True,
    )
    return redirect(request.referrer or "/favorites")


@app.route("/watchlist")
def watchlist():
    if not login_required():
        return redirect("/login")

    return render_template(
        "favorites.html",
        movies=get_user_watchlist(session["user_id"]),
        page_title="My Watchlist",
        empty_message="Your watchlist is empty.",
        remove_endpoint="remove_watchlist",
    )


@app.route("/watchlist/add/<int:movie_id>")
def add_watchlist(movie_id):
    if not login_required():
        return redirect("/login")

    add_watchlist_movie(session["user_id"], movie_id)
    return redirect(request.referrer or "/movies")


@app.route("/watchlist/add/tmdb/<int:tmdb_id>")
def add_watchlist_tmdb(tmdb_id):
    if not login_required():
        return redirect("/login")

    movie_id = ensure_local_movie_from_tmdb(tmdb_id)
    if movie_id:
        add_watchlist_movie(session["user_id"], movie_id, tmdb_id=tmdb_id)
    return redirect(request.referrer or url_for("tmdb_movie", movie_id=tmdb_id))


@app.route("/watchlist/remove/<int:movie_id>")
def remove_watchlist(movie_id):
    if not login_required():
        return redirect("/login")

    execute(
        "DELETE FROM watchlist WHERE user_id = %s AND movie_id = %s",
        (session["user_id"], movie_id),
        commit=True,
    )
    return redirect(request.referrer or "/watchlist")


@app.route("/recommendations")
def recommendations():
    if not login_required():
        return redirect("/login")

    return render_template(
        "recommendations.html",
        movies=recommend_for_user(session["user_id"], limit=20),
        model_ready=recommender.is_ready,
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    if not login_required():
        return redirect("/login")

    query = request.form.get("movie") if request.method == "POST" else request.args.get("q", "")
    query = (query or "").strip()
    movies_found = []

    if query:
        save_search(session["user_id"], query)
        movies_found = tmdb_client.search_movies(query)
        for movie in movies_found:
            movie["detail_url"] = url_for("tmdb_movie", movie_id=movie["tmdb_id"])

    return render_template(
        "search.html",
        movies=movies_found,
        query=query,
        recent_searches=get_recent_searches(session["user_id"]),
    )


@app.route("/save_movie", methods=["POST"])
def save_movie():
    if not login_required():
        return redirect("/login")

    title = request.form["title"]
    genre = request.form.get("genre", "")
    rating = request.form.get("rating", 0)
    overview = request.form.get("overview", "")
    poster_url_value = request.form.get("poster_url", "")

    movie = fetchone_dict("SELECT * FROM movies WHERE title=%s", (title,))
    if movie:
        movie_id = movie["id"]
    else:
        execute(
            """
            INSERT INTO movies(title, genre, rating, overview, poster_url)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (title, genre, rating, overview, poster_url_value),
            commit=True,
        )
        movie_id = cursor.lastrowid

    add_favorite_movie(session["user_id"], movie_id)
    return redirect("/favorites")


@app.route("/home")
def netflix_home():
    if not login_required():
        return redirect("/login")

    rows = normalize_many_local(fetchall_dict("SELECT * FROM movies ORDER BY rating DESC"))
    action_movies = [movie for movie in rows if movie.get("genre") == "Action"]
    sci_fi_movies = [movie for movie in rows if movie.get("genre") == "Sci-Fi"]

    return render_template(
        "home.html",
        trending=get_trending_movies(limit=10),
        action_movies=action_movies,
        sci_fi_movies=sci_fi_movies,
        favorite_movies=get_user_favorites(session["user_id"], limit=10),
    )


@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = normalize_local_movie(
        fetchone_dict("SELECT * FROM movies WHERE id = %s", (movie_id,))
    )
    if not movie:
        return redirect("/movies")

    if login_required():
        track_recently_viewed(session["user_id"], movie)

    recommendations = recommend_for_movie(movie, limit=10)
    return render_template(
        "movie_details.html",
        movie=movie,
        recommendations=recommendations,
    )


@app.route("/tmdb_movie/<int:movie_id>")
def tmdb_movie(movie_id):
    movie = tmdb_client.movie_details(movie_id)
    if movie:
        movie["detail_url"] = url_for("tmdb_movie", movie_id=movie_id)
        if login_required():
            track_recently_viewed(session["user_id"], movie)

    recommendations = recommend_for_movie(movie, limit=10) if movie else []
    return render_template(
        "tmdb_movie.html",
        movie=movie,
        recommendations=recommendations,
    )


ensure_schema()


if __name__ == "__main__":
    app.run(debug=False)
