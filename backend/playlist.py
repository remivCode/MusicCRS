from typing import List

import sqlite3
import musicbrainzngs
import time
import json
import subprocess
import zipfile
import os
import pandas as pd


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
                total_albums INTEGER
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                album_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist_id INTEGER,
                genre TEXT,
                release_date TEXT,
                total_songs INTEGER,
                FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                song_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                album_id INTEGER,
                artist_id INTEGER,
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
        print("Inserting data...")
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
        download_path = "./archive.zip"
        # curl_command = ["curl", "-L", "-o", download_path,"https://www.kaggle.com/api/v1/datasets/download/joebeachcapital/30000-spotify-songs"]
        # result = subprocess.run(curl_command, check=True)
        zip_path = os.path.expanduser("./archive.zip")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("extracted_files")
        csv_path = os.path.join(os.path.expanduser("extracted_files"), 'spotify_songs.csv')
        data = pd.read_csv(csv_path)
        return data['track_artist'].unique()


    def fetch_recordings(self, limit=1000000, batch_size=100, sleep_time=1.0):  
        musicbrainzngs.set_useragent("MyMusicApp", "1.0", "r.vialleton@stud.uis.n")

        recordings = []
        
        artist_names=self.extract_kaggle_data()
        for i,name in enumerate(artist_names):
            if len(recordings) >= limit:
                break
            offset = 0
            while(offset < 300 and len(recordings) < limit):
                try:
                    print(f"Fetching recordings for {name}...")
                    result = musicbrainzngs.search_recordings(artist=name, limit=batch_size, offset=offset)
                    recordings_batch = result['recording-list']

                    if not recordings_batch:
                        print("No more recordings found, continue.")
                        break

                    if recordings_batch[0]['artist-credit'][0]['artist']['name'] != name:
                        print("No more recordings found, continue.")
                        break

                    recordings.extend(recordings_batch)
                    print(f"Fetched {len(recordings)} recordings so far.")
                    
                    # Increment offset for pagination
                    offset += batch_size
                    
                    # Sleep to respect rate limits
                    time.sleep(sleep_time)
                    
                except musicbrainzngs.WebServiceError as e:
                    print(f"Error fetching data: {e}")
                    time.sleep(5)  # Wait and retry in case of an error

        return recordings

    def populate_data(self):
        print("Populating data...")
        cursor = self.conn.cursor()

        recordings = self.fetch_recordings(limit=1000,batch_size=100)
        for recording in recordings:
            try:
                record_id = recording['id']
                record_title = recording['title']
                artist_id = recording['artist-credit'][0]['artist']['id']
                artist_name = recording['artist-credit'][0]['artist']['name']
                album_id = recording['release-list'][0]['id']
                album_name = recording['release-list'][0]['title']
                album_date = recording['release-list'][0]['date']

                artist_record = self.read(table='artists', where={'artist_id': artist_id})
                if not artist_record:
                    cursor.execute('INSERT INTO artists (artist_id, name, total_albums) VALUES (?, ?, ?);', (artist_id, artist_name, 0))
                
                album_record = self.read(table='albums', where={'album_id': album_id})
                if not album_record:
                    cursor.execute('INSERT INTO albums (album_id, title, artist_id, genre, release_date, total_songs) VALUES (?, ?, ?, ?, ?, ?);', (album_id, album_name, artist_id, 'Unknown', album_date, 0))
                    cursor.execute('UPDATE artists SET total_albums = total_albums + 1 WHERE artist_id = ?;', (artist_id,))

                song_record = self.read(table='songs', where={'song_id': record_id})
                if not song_record:
                    cursor.execute('INSERT INTO songs (song_id, title, album_id, artist_id) VALUES (?, ?, ?, ?);', (record_id, record_title, album_id, artist_id))
                    cursor.execute('UPDATE albums SET total_songs = total_songs + 1 WHERE album_id = ?;', (album_id,))

            except Exception as e:
                print(f"Error populating data: {e}\nrecording: {recording}")
                continue
        
        res = cursor.execute('SELECT COUNT(*) FROM songs;')
        print(f"Total songs added: {res.fetchone()[0]}")
        self.conn.commit()

