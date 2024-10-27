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
    def __init__(self, id, path=os.path.join("data", "spotify.sqlite"), init=True):
    # Connexion à la base de données SQLite
        self.id = id
        self.conn = sqlite3.connect(path, check_same_thread=False)
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

    def read(self, table: str, data: list[str] = ("*"), where: str = "", limit=None):
        cursor = self.conn.cursor()
        request = 'SELECT ' + ', '.join(data) + ' FROM ' + table
        if where:
            request += ' WHERE ' + where
        if limit:
            request += ' LIMIT ' + str(limit)
        cursor.execute(request)
        return cursor.fetchall()

    def read_songs_from_playlist(self, playlist_id, data: dict[str, str] = {}):
        cursor = self.conn.cursor()
        cursor.execute('SELECT ' + ', '.join(data) + ' FROM songs ' +
            'INNER JOIN playlist_songs ON songs.id = playlist_songs.song_id ' +
            'INNER JOIN artists ON songs.artist_id = artists.id ' +
            'INNER JOIN albums ON songs.album_id = albums.id ' +
            'WHERE playlist_songs.playlist_id = ?', (playlist_id,))
        return cursor.fetchall()
    
    def read_album_from_song(self, song_title, data: list[str] = ("*")):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT DISTINCT ''' + ', '.join(data) + '''
        FROM albums
        INNER JOIN songs ON albums.id = songs.album_id
        WHERE songs.name = ?
    ''', (song_title,))
        return cursor.fetchall()
    
    def init_db(self):
        print("Initializing database...")

        download_path = os.path.join("data", "archive.zip")
        if not os.path.exists(download_path):
            print("Downloading data...")
            curl_command = ["curl", "-L", "-o", download_path,"https://www.kaggle.com/api/v1/datasets/download/maltegrosse/8-m-spotify-tracks-genre-audio-features", "--ssl-no-revoke"]
            result = subprocess.run(curl_command, check=True)
        zip_path = os.path.expanduser(download_path)

        print("Extracting data...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("data")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id TEXT,
                song_id TEXT,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                FOREIGN KEY (song_id) REFERENCES songs(id),
                PRIMARY KEY (playlist_id, song_id)
            );
        ''')
        
        self.conn.commit()

    def populate_data(self):
        print("Populating data...")
        cursor = self.conn.cursor()

        print("Creating indexes...")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_audio_features_id ON audio_features (id);")
        print("Index created: idx_audio_features_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tracks_audio_feature_id ON tracks (audio_feature_id);")
        print("Index created: idx_tracks_audio_feature_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tracks_id ON tracks (id);")
        print("Index created: idx_tracks_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_artists_id ON artists (id);")
        print("Index created: idx_artists_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_albums_id ON albums (id);")
        print("Index created: idx_albums_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_artist_genre_genre_id ON r_artist_genre (genre_id);")
        print("Index created: idx_r_artist_genre_genre_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_artist_genre_artist_id ON r_artist_genre (artist_id);")
        print("Index created: idx_r_artist_genre_artist_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_track_artist_artist_id ON r_track_artist (artist_id);")
        print("Index created: idx_r_track_artist_artist_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_track_artist_track_id ON r_track_artist (track_id);")
        print("Index created: idx_r_track_artist_track_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_albums_artists_artist_id ON r_albums_artists (artist_id);")
        print("Index created: idx_r_albums_artist_artist_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_albums_artists_album_id ON r_albums_artists (album_id);")
        print("Index created: idx_r_albums_artist_album_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_albums_tracks_album_id ON r_albums_tracks (album_id);")
        print("Index created: idx_r_albums_tracks_album_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_r_albums_tracks_track_id ON r_albums_tracks (track_id);")
        print("Index created: idx_r_albums_tracks_track_id")

        cursor.execute("""
            DELETE FROM tracks
            WHERE id NOT IN (
                SELECT id FROM tracks
                ORDER BY RANDOM()
                LIMIT 1500000
            );
        """)

        cursor.execute("SELECT COUNT(*) FROM tracks;")
        print(f"Total tracks: {cursor.fetchone()[0]}")

        cursor.execute("CREATE TABLE IF NOT EXISTS songs AS SELECT * FROM tracks INNER JOIN audio_features ON tracks.audio_feature_id = audio_features.id INNER JOIN r_track_artist ON tracks.id = r_track_artist.track_id  INNER JOIN r_albums_tracks ON tracks.id = r_albums_tracks.track_id;")
        print("Created songs table")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_songs_id ON songs (id);")
        print("Index created: idx_songs_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_songs_album_id ON songs (album_id);")
        print("Index created: idx_songs_album_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_songs_artist_id ON songs (artist_id);")
        print("Index created: idx_songs_artist_id")

        cursor.execute("ALTER TABLE albums ADD COLUMN artist_id TEXT;")
        cursor.execute("""
            UPDATE albums
            SET artist_id = (
                SELECT r_albums_artists.artist_id 
                FROM r_albums_artists 
                WHERE r_albums_artists.album_id = albums.id
            );
        """)
        print("Updated albums with artist_id")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_albums_artist_id ON albums (artist_id);")
        print("Index created: idx_albums_artist_id")

        cursor.execute("ALTER TABLE artists ADD COLUMN genre TEXT;")
        cursor.execute("""
            UPDATE artists
            SET genre = (
                SELECT r_artist_genre.genre_id 
                FROM r_artist_genre 
                WHERE r_artist_genre.artist_id = artists.id
            );
        """)
        print("Updated artists with genre")

        cursor.execute('''
            ALTER TABLE albums
            ADD COLUMN total_songs INTEGER
        ''')

        # Update the song_count column for each album
        cursor.execute('''
            UPDATE albums
            SET total_songs = (
                SELECT COUNT(*)
                FROM songs
                WHERE songs.album_id = albums.id
            )
        ''')
        print("Updated albums with total_songs")

        cursor.execute('''
            ALTER TABLE artists
            ADD COLUMN total_albums INTEGER
        ''')

        # Update the song_count column for each album
        cursor.execute('''
            UPDATE artists
            SET total_albums = (
                SELECT COUNT(*)
                FROM albums
                WHERE albums.artist_id = artists.id
            )
        ''')
        print("Updated artists with total_albums")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';") 
        table_names = [table[0] for table in cursor.fetchall()] 
        print("Tables:", table_names) 

        os.makedirs("data/new_schema", exist_ok=True) 
        for table_name in table_names: 
            cursor.execute(f"PRAGMA table_info('{table_name}');") 
            column_names = [column[1] for column in cursor.fetchall()] 
            with open(f"data/new_schema/{table_name}.csv", "w") as f: 
                f.write(",".join(column_names) + "\n") 
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;") 
                row = cursor.fetchone()
                if row:
                    f.write(",".join([str(column) for column in row]) + "\n") 
        
        res = cursor.execute('SELECT COUNT(*) FROM songs;')
        print(f"Total songs added: {res.fetchone()[0]}")
        self.conn.commit()

