import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sakshi",
    database="movie_app"
)

cursor = conn.cursor()

