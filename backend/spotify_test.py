import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import os
from dotenv import load_dotenv
import json

load_dotenv()
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def fetch_recordings(limit=100, batch_size=100, sleep_time=1.0):    
    artists = ['Radiohead', 'David Guetta', 'The Beatles']

    tracks = []
    for artist in artists:
        result = sp.search(q='artist:' + artist, type='artist')
        artist_id = result['artists']['items'][0]['id']
        artist_name = result['artists']['items'][0]['name']

        albums = sp.artist_albums(artist_id, limit=50)
        for album in albums['items']:
            album_id = album['id']
            album_name = album['name']

            album_tracks = sp.album_tracks(album_id, limit=50)
            album_track_details = sp.audio_features([track['id'] for track in album_tracks['items']])
            for track in album_track_details['tracks']:
                track_id = track['id']
                track_name = track['name']
                tracks.append(track)
    print(f"Fetched {len(tracks)} tracks from {len(artists)} artists.")

    return tracks

songs_data = fetch_recordings(limit=100, batch_size=100)

def save_to_file(data, filename="songs_data.json"):
    with open(filename, 'w') as f:
        json.dump(data, f)

# Save the fetched songs data to a JSON file
save_to_file(songs_data)