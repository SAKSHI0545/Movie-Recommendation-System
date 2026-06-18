# 🎬 Content-Based Movie Recommendation Platform

A full-stack Movie Recommendation Platform built using **Flask**, **Python**, **MySQL**, and the **TMDB API**. The application allows users to search movies, view detailed information, manage favorites and watchlists, and receive intelligent movie recommendations using a **Content-Based Recommendation System** powered by **CountVectorizer** and **Cosine Similarity**.

---

## ✨ Features

### 👤 User Authentication
- User Registration
- Secure Login
- Session Management

### 🎬 Movie Features
- Search Movies using TMDB API
- View Detailed Movie Information
- Movie Posters
- Ratings
- Genres
- Runtime
- Cast Information
- Release Date
- Popularity Score

### 🤖 Recommendation Engine
- Content-Based Movie Recommendation
- CountVectorizer for Feature Extraction
- Cosine Similarity Algorithm
- "You May Also Like" Recommendations
- Fast Recommendation Retrieval using Pickle Models

### ❤️ Personalization
- User-specific Favorites
- User-specific Watchlist
- Recently Viewed Movies
- Search History

### 📊 Dashboard
- Trending Movies
- Recently Viewed Movies
- Favorites
- Watchlist
- Recommended Movies

### 🎨 User Interface
- Responsive Design
- Dark Theme
- Flask + Jinja2 Templates

---

# 🛠 Tech Stack

| Category | Technologies |
|----------|--------------|
| **Backend** | Python, Flask |
| **Frontend** | HTML, CSS, Jinja2 |
| **Database** | MySQL |
| **Machine Learning** | Pandas, NumPy, Scikit-learn |
| **Recommendation Algorithm** | CountVectorizer, Cosine Similarity |
| **API** | TMDB API |
| **Tools** | Git, GitHub, VS Code, Postman |

---

# 🧠 How the Recommendation System Works

This project uses a **Content-Based Filtering** approach.

Instead of recommending movies based on ratings from other users, the recommendation engine compares movie content and suggests movies with similar characteristics.

The recommendation model considers:

- Genres
- Keywords
- Cast
- Director
- Movie Overview

### Recommendation Pipeline

```
TMDB Dataset
        │
        ▼
Data Cleaning
        │
        ▼
Feature Engineering
        │
        ▼
CountVectorizer
        │
        ▼
Cosine Similarity Matrix
        │
        ▼
Movie Recommendations
```

The trained recommendation model is loaded when the Flask application starts, making recommendations fast without retraining the model for every request.

---

# 📂 Dataset

This project uses the **TMDB 5000 Movie Dataset**.

Dataset files:

- `tmdb_5000_movies.csv`
- `tmdb_5000_credits.csv`

Place both files inside:

```
datasets/
```

---

# ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/SAKSHI0545/Movie-Recommendation-System.git
```

### Move into the Project

```bash
cd Movie-Recommendation-System
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Database

Create a MySQL database named:

```
movie_app
```

Update your database credentials before running the application.

---

# 🚀 Generate Recommendation Model

Run:

```bash
python ml/train_recommender.py
```

This generates:

```
models/
│── movies.pkl
│── similarity.pkl
```

> **Note:** `similarity.pkl` is intentionally excluded from this repository because it exceeds GitHub's 100 MB file size limit. It can be regenerated anytime using the training script.

---

# ▶️ Run the Application

```bash
python app.py
```

Open your browser:

```
http://127.0.0.1:5000
```

---

# 📁 Project Structure

```
Movie-Recommendation-System
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── datasets/
│   ├── tmdb_5000_movies.csv
│   └── tmdb_5000_credits.csv
│
├── ml/
│   ├── train_recommender.py
│   └── __init__.py
│
├── models/
│   ├── movies.pkl
│   └── similarity.pkl (Generated Locally)
│
├── static/
├── templates/
└── utils/
```

---

# 📸 Screenshots

> Screenshots will be added soon.

Suggested screenshots:

- Home Page
- Login Page
- Dashboard
- Search Results
- Movie Details
- Recommendation Section
- Favorites
- Watchlist

---

# 🔮 Future Enhancements

- Personalized recommendations based on user favorites
- Movie Reviews and Ratings
- Recommendation Feedback System
- Mood-Based Movie Recommendations
- Recently Trending Movies
- Email Notifications
- Cloud Deployment

---

# 👩‍💻 Author

**Sakshi Marne**

Computer Engineering Student

**Skills:** Python • Flask • SQL • Machine Learning • REST APIs • Git • GitHub

---

⭐ If you found this project useful, consider giving it a star.