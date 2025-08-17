import streamlit as st
import pickle
import requests

# ✅ Load saved data
movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# 🔑 TMDB API key
API_KEY = "0db09ca80c8038aaf73b2bff68708a54"

# 🔍 Fetch poster from TMDB
def fetch_poster(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_title}"
    response = requests.get(url)
    data = response.json()
    if data['results']:
        poster_path = data['results'][0].get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    return None

# 🔁 Recommender logic
def recommend(movie):
    movie = movie.lower()
    if movie not in movies['title'].str.lower().values:
        return [], []

    index = movies[movies['title'].str.lower() == movie].index[0]
    distances = similarity[index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movie_list:
        title = movies.iloc[i[0]].title
        recommended_movies.append(title)
        recommended_posters.append(fetch_poster(title))

    return recommended_movies, recommended_posters

# 🧠 Dopamine UI
st.set_page_config(page_title="🎬  Movie Recommender", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #0F0F0F;
        color: #FFFFFF;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF00C8, #00FFE7);
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 0.6em 1.5em;
        transition: 0.3s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #00FFE7, #FF00C8);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #FF00C8;'>💫 Your Movie Dose</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #AAAAAA;'>Fuel your next binge session with great picks 🎯</h4>", unsafe_allow_html=True)
st.write("")

# 🎯 Input
selected_movie = st.selectbox("🎬 Type or Select a Movie:", movies['title'].values)

# 🚀 Recommend
if st.button(f"🎯 Recommend me movies like "):
    names, posters = recommend(selected_movie)

    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #00FFE7;'>🎉 Handpicked Just for You:</h3>", unsafe_allow_html=True)
    st.write("")

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            if posters[i]:
                st.image(posters[i], use_container_width=True, caption=names[i])

            else:
                st.markdown(f"<div style='color: #FFDD00; text-align: center;'>{names[i]}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888888;'>
            Built with ❤️ <strong></strong> <strong></strong><br>
            
        </div>
    """, unsafe_allow_html=True)
