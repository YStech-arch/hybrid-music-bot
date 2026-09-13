import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    response.raise_for_status()
    return response.json()["access_token"]


def search_track(query):
    token = get_token()

    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={
            "Authorization": f"Bearer {token}"
        },
        params={
            "q": query,
            "type": "track",
            "limit": 5,
        },
    )

    print("Search HTTP:", response.status_code)

    if not response.ok:
        print("Spotify response:")
        print(response.text)
        return []

    return response.json()["tracks"]["items"]


query = input("Cari lagu: ")

tracks = search_track(query)

print("\nHasil Spotify:\n")

for i, track in enumerate(tracks, 1):
    artists = ", ".join(
        artist["name"] for artist in track["artists"]
    )

    print(f"{i}. {track['name']}")
    print(f"   Artis : {artists}")
    print(f"   Album : {track['album']['name']}")
    print(f"   URL   : {track['external_urls']['spotify']}")
    print()
