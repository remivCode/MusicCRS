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

def insert_data():
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
    
    # Ajouter des playlists
    playlists = [
        ('Top Hits'),
        ('Chill Vibes'),
        ('Rock Anthems')
    ]
    cursor.executemany('INSERT INTO playlists (name) VALUES (?);', [(name,) for name in playlists])

    # Ajouter des chansons aux playlists
    playlist_songs = [
        (1, 1),  # Top Hits -> Shake It Off
        (1, 2),  # Top Hits -> Blinding Lights
        (1, 3),  # Top Hits -> Hello
        (2, 4),  # Chill Vibes -> Thunder
        (2, 5),  # Chill Vibes -> Paradise
        (3, 6),  # Rock Anthems -> Sugar
        (3, 7)   # Rock Anthems -> Rope
    ]
    cursor.executemany('INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?);', playlist_songs)

    conn.commit()

# Initialiser la base de données
init_db()
# Insérer des données
#insert_data()

platform = FlaskSocketPlatform(PlaylistAgent)

platform.start()
