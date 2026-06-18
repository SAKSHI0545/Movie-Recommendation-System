import requests

api_key = "e5da186a6593516ba73e6c57124a3f18"

url = "https://api.themoviedb.org/3/movie/popular"

params = {
    "api_key": api_key
}

try:

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    data = response.json()

    print(data)

except Exception as e:

    print("ERROR:", e)