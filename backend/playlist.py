from typing import List
from song import Song
import sqlite3

class Playlist():
    def __init__(self, id, name="music.db", init=True):
    # Connexion à la base de données SQLite
        self.id = id
        self.conn = sqlite3.connect(name, check_same_thread=False)
        if init:
            self.init_db()

    def create(self, table: str, data: dict[str, str]):
        print(f"request: {'INSERT INTO ' + table + ' (' + ', '.join(data.keys()) + ') VALUES (' + ', '.join(['?'] * len(data)) + ')', tuple(data.values())}")
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

    def read(self, table: str, data: list[str], where: dict[str, str] = {}):
        print(f"data: {', '.join(data)}")
        print(f"where: {' AND '.join([key + ' = ?' for key in where.keys()]), tuple(where.values())}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT ' + ', '.join(data) + ' FROM ' + table + ' WHERE ' + ' AND '.join([key + ' = ?' for key in where.keys()]), tuple(where.values()))
        return cursor.fetchall()

    def read_songs_from_playlist(self, playlist_id, data: dict[str, str] = {}):
        print(f"read from playlist data: {', '.join(data)}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT ' + ', '.join(data) + ' FROM songs ' +
            'INNER JOIN playlist_songs ON songs.song_id = playlist_songs.song_id ' +
            'INNER JOIN artists ON songs.artist_id = artists.artist_id ' +
            'WHERE playlist_songs.playlist_id = ?', (playlist_id,))
        return cursor.fetchall()
    
    def read_album_from_song(self, song_id, data: list[str] = ("*")):
        cursor = self.conn.cursor()
        cursor.execute('SELECT ' + ', '.join(data) + ' FROM albums ' +
            'INNER JOIN songs ON albums.album_id = songs.album_id ' +
            'WHERE song_id = ?', (song_id,))
        return cursor.fetchall()
    
    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                total_albums INTEGER
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                album_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                playlist_id INTEGER,
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