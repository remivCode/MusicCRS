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
    name = 'Radiohead'

    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
    return artist

songs_data = fetch_recordings(limit=100, batch_size=100)

def save_to_file(data, filename="songs_data.json"):
    with open(filename, 'w') as f:
        json.dump(data, f)

# Save the fetched songs data to a JSON file
save_to_file(songs_data)