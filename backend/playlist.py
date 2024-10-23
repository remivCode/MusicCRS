from typing import List

import sqlite3
import musicbrainzngs
import time
import subprocess
import zipfile
import os
import pandas as pd
import random
import logging

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from dotenv import load_dotenv

load_dotenv()
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=0, backoff_factor=0.6, status_retries=0)

class Playlist():
    def __init__(self, id, name="music.db", init=True):
    # Connexion à la base de données SQLite
        self.id = id
        self.conn = sqlite3.connect(name, check_same_thread=False)
        if init:
            self.init_db()

    def create(self, table: str, data: dict[str, str]):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO ' + table + ' (' + ', '.join(data.keys()) + ') VALUES (' + ', '.join(['?'] * len(data)) + ')', tuple(data.values()))
        self.conn.commit()
        return cursor.lastrowid

    def delete(self, table: str, data: dict[str, str] = {}):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM ' + table + ' WHERE ' + ' AND '.join([key + ' = ?' for key in data.keys()]), tuple(data.values()))
        self.conn.commit()
    
    def update(self, table: str, data: dict[str, str], where: dict[str, str] = {}):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE ' + table + ' SET ' + ', '.join([key + ' = ?' for key in data.keys()]) + ' WHERE ' + ' AND '.join([key + ' = ?' for key in where.keys()]), tuple(data.values()) + tuple(where.values()))
        self.conn.commit()

    def read(self, table: str, data: list[str] = ("*"), where: dict[str, str] = {}):
        cursor = self.conn.cursor()
        request = 'SELECT ' + ', '.join(data) + ' FROM ' + table
        if where:
            request += ' WHERE ' + ' AND '.join([key + ' = ?' for key in where.keys()])
        cursor.execute(request, tuple(where.values()))
        return cursor.fetchall()

    def read_songs_from_playlist(self, playlist_id, data: dict[str, str] = {}):
        cursor = self.conn.cursor()
        cursor.execute('SELECT ' + ', '.join(data) + ' FROM songs ' +
            'INNER JOIN playlist_songs ON songs.song_id = playlist_songs.song_id ' +
            'INNER JOIN artists ON songs.artist_id = artists.artist_id ' +
            'INNER JOIN albums ON songs.album_id = albums.album_id ' +
            'WHERE playlist_songs.playlist_id = ?', (playlist_id,))
        return cursor.fetchall()
    
    def read_album_from_song(self, song_title, data: list[str] = ("*")):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT DISTINCT ''' + ', '.join(data) + '''
        FROM albums
        INNER JOIN songs ON albums.album_id = songs.album_id
        WHERE songs.title = ?
    ''', (song_title,))
        return cursor.fetchall()
    
    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                artist_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                total_albums INTEGER,
                genre TEXT,
                popularity INTEGER
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                album_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist_id INTEGER,
                release_date TEXT,
                total_songs INTEGER,
                genre TEXT,
                popularity INTEGER,
                FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                song_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                album_id INTEGER,
                artist_id INTEGER,
                duration_ms INTEGER,
                featuring TEXT,
                GENRE TEXT,
                acousticness FLOAT,
                danceability FLOAT,
                energy FLOAT,
                instrumentalness FLOAT,
                key INTEGER,
                liveness FLOAT,
                loudness FLOAT,
                mode INTEGER,
                speechiness FLOAT,
                tempo FLOAT,
                time_signature INTEGER,
                valence FLOAT,
                FOREIGN KEY (album_id) REFERENCES albums(album_id),
                FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id TEXT,
                song_id INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id),
                PRIMARY KEY (playlist_id, song_id)
            );
        ''')

        self.conn.commit()

    def insert_data(self, playlist: int = 1):
        logging.info("Inserting data...")
        cursor = self.conn.cursor()
        # Ajouter des artistes
        artists = [
            ('Taylor Swift', 10),
            ('The Weeknd', 5),
            ('Adele', 3),
            ('Imagine Dragons', 6),
            ('Coldplay', 8),
            ('Maroon 5', 6),
            ('Foo Fighters', 10)
        ]
        cursor.executemany('INSERT INTO artists (name, total_albums) VALUES (?, ?);', artists)
        
        # Ajouter des albums
        albums = [
            ('1989', 1, 'Pop', '2014-10-27', 14),
            ('After Hours', 2, 'R&B', '2020-03-20', 14),
            ('25', 3, 'Pop', '2015-11-20', 11),
            ('Evolve', 4, 'Rock', '2017-06-23', 11),
            ('Ghost Stories', 5, 'Rock', '2014-05-19', 9),
            ('Songs About Jane', 6, 'Pop', '2002-06-25', 12),
            ('Wasting Light', 7, 'Rock', '2011-04-12', 11)
        ]
        cursor.executemany('INSERT INTO albums (title, artist_id, genre, release_date, total_songs) VALUES (?, ?, ?, ?, ?);', albums)
        
        # Ajouter des chansons
        songs = [
            ('Shake It Off', 1, 1),
            ('Blinding Lights', 2, 2),
            ('Hello', 3, 3),
            ('Thunder', 4, 4),
            ('Paradise', 5, 5),
            ('Sugar', 6, 6),
            ('Rope', 7, 7),
            ('Demons', 4, 1),
            ('Viva La Vida', 5, 2),
            ('Maps', 6, 3)
        ]
        cursor.executemany('INSERT INTO songs (title, album_id, artist_id) VALUES (?, ?, ?);', songs)
        
        # Ajouter des chansons aux playlists
        playlist_songs = [
            (playlist, 1),  # Top Hits -> Shake It Off
            (playlist, 2),  # Top Hits -> Blinding Lights
            (playlist, 3),  # Top Hits -> Hello
            (playlist, 4),  # Chill Vibes -> Thunder
            (playlist, 5),  # Chill Vibes -> Paradise
            (playlist, 6),  # Rock Anthems -> Sugar
            (playlist, 7)   # Rock Anthems -> Rope
        ]
        cursor.executemany('INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?);', playlist_songs)

        self.conn.commit()


    def extract_kaggle_data(self):
        os.makedirs("./data/kaggle_artists", exist_ok=True)
        download_path = "./data/kaggle_artists/kaggle_archive.zip"
        if not os.path.exists(download_path):
            curl_command = ["curl", "-L", "-o", download_path,"https://www.kaggle.com/api/v1/datasets/download/joebeachcapital/30000-spotify-songs", "--ssl-no-revoke"]
            result = subprocess.run(curl_command, check=True)

        os.makedirs(os.path.join("data", "kaggle_artists"), exist_ok=True)
        csv_path = os.path.join("data", "kaggle_artists", 'spotify_songs.csv')
        if not os.path.exists(csv_path):
            zip_path = os.path.expanduser(download_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.join("data", "kaggle_artists"))
        data = pd.read_csv(csv_path)
        return data['track_artist'].unique().tolist()

    def safe_call_api(self, method):
        max_retries = 5
        retry_delay = 0
        for attempt in range(max_retries):
            try:
                print(f"Call {self.call_count}")
                if (self.call_count % 500 == 0) and (self.call_count > 0):
                    time.sleep(30)
                result = method()
                time.sleep(0.06)
                self.call_count += 1
                return result
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    if "Retry-After" in e.headers:
                        retry_after = e.headers.get("Retry-After")
                    else:
                        retry_after = 5
                    # Exponential backoff
                    retry_delay += 2**attempt * 0.1 + retry_after
                    print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay + random.uniform(0, 1))  # add some jitter to the delay
                else:
                    raise e
        raise Exception("Max retries exceeded")

    def populate_data(self, limit=1000000, artist_limit=300): 
        logging.info("Populating data...") 
        self.call_count = 0
        cursor = self.conn.cursor()

        tracks = []
        counter = 0
        
        artist_names=self.extract_kaggle_data()
        for i,name in enumerate(artist_names):
            try:
                logging.info(f"Fetching artist {i+1}/{len(artist_names)}: {name}, {counter} songs added so far")
                if counter > limit:
                    break
                artist_counter = 0

                artist_data = {}
                search = self.safe_call_api(lambda: sp.search(q='artist:' + name, type='artist'))
                artist_data['id'] = search['artists']['items'][0]['id']
                artist_data['name'] = search['artists']['items'][0]['name']
                artist_data['genres'] = search['artists']['items'][0]['genres']
                artist_data['popularity'] = search['artists']['items'][0]['popularity']

                cursor.execute('INSERT INTO artists (artist_id, name, total_albums, genre, popularity) VALUES (?, ?, ?, ?, ?);', (artist_data['id'], artist_data['name'], 0, ', '.join(artist_data['genres']), artist_data['popularity']))

                artist_albums = self.safe_call_api(lambda: sp.artist_albums(artist_data['id'], limit=40))
                album_ids = [album['id'] for album in artist_albums['items'] if album['album_type'] != 'compilation']
                albums = []
                for i in range(0, len(album_ids), 20):
                    albums.extend(sp.albums(album_ids[i:i+20])['albums'])

                artist_albums = []
                for album in albums:
                    album_data = {}
                    album_data['id'] = album['id']
                    album_data['name'] = album['name']
                    album_data['total_tracks'] = album['total_tracks']
                    album_data['release_date'] = album['release_date']
                    album_data['genres'] = ', '.join(album['genres'])
                    album_data['popularity'] = album['popularity']
                    album_data['artist_id'] = artist_data['id']
                    artist_albums.append(album_data)

                    album_tracks = []
                    for track in album['tracks']['items']:
                        if counter > limit or artist_counter > artist_limit:
                            break

                        if track['id'] in [track['id'] for track in tracks]:
                            continue
                        track_data = {}
                        track_data['id'] = track['id'] 
                        track_data['title'] = track['name']
                        track_data['featuring'] = ', '.join([artist['name'] for artist in track['artists'] if artist['name'] != artist_data['name']])
                        track_data['duration_ms'] = track['duration_ms']
                        track_data['genre'] = album_data['genres']
                        track_data['artist_id'] = artist_data['id']
                        track_data['album_id'] = album_data['id']
                        track_data['artist'] = artist_data
                        track_data['album'] = album_data
                        album_tracks.append(track_data)

                    track_features = []
                    for i in range(0, len(album_tracks), 100):
                        track_features.extend(self.safe_call_api(lambda: sp.audio_features([track['id'] for track in album_tracks[i:i+100]])))

                    for idx, feature in enumerate(track_features):
                        try:
                            album_tracks[idx]['acousticness'] = feature['acousticness']
                            album_tracks[idx]['danceability'] = feature['danceability']
                            album_tracks[idx]['energy'] = feature['energy']
                            album_tracks[idx]['instrumentalness'] = feature['instrumentalness']
                            album_tracks[idx]['key'] = feature['key']
                            album_tracks[idx]['liveness'] = feature['liveness']
                            album_tracks[idx]['loudness'] = feature['loudness']
                            album_tracks[idx]['mode'] = feature['mode']
                            album_tracks[idx]['speechiness'] = feature['speechiness']
                            album_tracks[idx]['tempo'] = feature['tempo']
                            album_tracks[idx]['time_signature'] = feature['time_signature']
                            album_tracks[idx]['valence'] = feature['valence']
                            counter += 1
                            artist_counter += 1
                        except Exception as e:
                            album_tracks.remove(album_tracks[idx])
                    
                    tracks.extend(album_tracks)

                    if counter > limit or artist_counter > artist_limit:
                        break
                
                cursor.executemany('INSERT INTO albums (album_id, title, artist_id, release_date, total_songs, genre, popularity) VALUES (:id, :name, :artist_id, :release_date, :total_tracks, :genres, :popularity);', artist_albums)
                cursor.execute('UPDATE artists SET total_albums = total_albums + ? WHERE artist_id = ?;', (len(album_data), artist_data['id'],))
            except Exception as e:
                logging.error(f"Error fetching data: {e}")
                time.sleep(1)

        cursor.executemany('INSERT INTO songs (song_id, title, album_id, artist_id, genre, featuring, duration_ms, acousticness, danceability, energy, instrumentalness, key, liveness, loudness, mode, speechiness, tempo, time_signature, valence) VALUES (:id, :title, :album_id, :artist_id, :genre, :featuring, :duration_ms, :acousticness, :danceability, :energy, :instrumentalness, :key, :liveness, :loudness, :mode, :speechiness, :tempo, :time_signature, :valence);', (tracks))

        res = cursor.execute('SELECT COUNT(*) FROM songs;')
        logging.info(f"Total songs added: {res.fetchone()[0]}")
        self.conn.commit()
        cursor.close()

