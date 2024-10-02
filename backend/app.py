from dialoguekit.platforms import FlaskSocketPlatform
from agent import PlaylistAgent
import sqlite3

conn = sqlite3.connect('music.db', check_same_thread=False) 
cursor = conn.cursor()

def init_db():
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

    conn.commit()

init_db()

def add_artist(name, total_albums):
    cursor.execute('INSERT INTO artists (name, total_albums) VALUES (?, ?)', (name, total_albums))
    conn.commit()

def add_album(title, artist_id, genre, release_date, total_songs):
    cursor.execute('INSERT INTO albums (title, artist_id, genre, release_date, total_songs) VALUES (?, ?, ?, ?, ?)', 
                   (title, artist_id, genre, release_date, total_songs))
    conn.commit()

def add_song(title, duration, album_id, artist_id):
    cursor.execute('INSERT INTO songs (title, duration, album_id, artist_id) VALUES (?, ?, ?, ?)', (title, duration, album_id, artist_id))
    conn.commit()

def add_playlist(name):
    cursor.execute('INSERT INTO playlists (name) VALUES (?)', (name,))
    conn.commit()

def add_song_to_playlist(playlist_id, song_id):
    cursor.execute('INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)', (playlist_id, song_id))
    conn.commit()

def get_playlists():
    cursor.execute('SELECT * FROM playlists')
    return cursor.fetchall()

def get_songs_in_playlist(playlist_id):
    cursor.execute('''
        SELECT songs.title 
        FROM songs 
        INNER JOIN playlist_songs ON songs.song_id = playlist_songs.song_id 
        WHERE playlist_songs.playlist_id = ?
    ''', (playlist_id,))
    return cursor.fetchall()

platform = FlaskSocketPlatform(PlaylistAgent)

platform.start()


