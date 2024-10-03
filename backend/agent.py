from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from playlist import Playlist
import sqlite3
import random

# Connexion à la base de données SQLite
conn = sqlite3.connect('music.db', check_same_thread=False)
cursor = conn.cursor()

# Fonctions pour manipuler la base de données
def add_artist(name, total_albums):
    cursor.execute('INSERT INTO artists (name, total_albums) VALUES (?, ?)', (name, total_albums))
    conn.commit()

def add_album(title, artist_id, genre, release_date, total_songs):
    cursor.execute('INSERT INTO albums (title, artist_id, genre, release_date, total_songs) VALUES (?, ?, ?, ?, ?)', 
                   (title, artist_id, genre, release_date, total_songs))
    conn.commit()

def add_song(title, album_id, artist_id):
    cursor.execute('INSERT INTO songs (title, album_id, artist_id) VALUES (?, ?, ?)', (title, album_id, artist_id))
    conn.commit()

def add_song_to_playlist(playlist_id, song_id):
    cursor.execute('INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)', (playlist_id, song_id))
    conn.commit()

def remove_song_from_playlist(playlist_id, song_id):
    cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?', (playlist_id, song_id))
    conn.commit()

def get_songs_from_playlist(playlist_id):
    cursor.execute('''
        SELECT songs.title, artists.name 
        FROM songs 
        INNER JOIN playlist_songs ON songs.song_id = playlist_songs.song_id 
        INNER JOIN artists ON songs.artist_id = artists.artist_id
        WHERE playlist_songs.playlist_id = ?
    ''', (playlist_id,))
    return cursor.fetchall()

class PlaylistAgent(Agent):
    def __init__(self, id: str):
        """Playlist agent."""
        super().__init__(id)
        self.playlist = Playlist()

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            "Hello, I'm here to assist you with making your personalized music playlist.\n" + '\n' +
            "Commands:" + '\n'
            "add <artist> - <title>: add a song to the playlist" + '\n' +
            "remove <artist> - <title>: remove a song from the playlist" + '\n' +
            "clear: clear the playlist" + '\n' +
            "show: show the playlist" + '\n' +
            "date album : album"+ '\n'+
            "number albums : artist "+ '\n'+
            "which album : title"+ '\n'+
            "genre album : album" + '\n' +
            "number songs : artist" + '\n'
            "give song : artist" + '\n',
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def goodbye(self) -> None:
        """Sends the agent's goodbye message."""
        utterance = AnnotatedUtterance(
            "It was nice talking to you. Bye!",
            dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance."""
        if utterance.text == "EXIT":
            self.goodbye()
            return

        try:
            if utterance.text.startswith("add"):
                parts = utterance.text[4:].split(' - ')
                if len(parts) == 2:
                    title = parts[0].strip('"')
                    artist = parts[1].strip('"')

                    # Ajout de la chanson à la base de données
                    cursor.execute('SELECT artist_id FROM artists WHERE name = ?', (artist,))
                    artist_record = cursor.fetchone()
                    if artist_record is None:
                        # Si l'artiste n'existe pas, l'ajouter (exemple sans genre et albums pour simplifier)
                        add_artist(artist, 0)
                        cursor.execute('SELECT artist_id FROM artists WHERE name = ?', (artist,))
                        artist_record = cursor.fetchone()

                    artist_id = artist_record[0]
                    # On ajoute une chanson avec une durée fixe pour simplifier
                    add_song(title, None, artist_id)

                    # Récupérer l'ID de la chanson ajoutée
                    cursor.execute('SELECT song_id FROM songs WHERE title = ? AND artist_id = ?', (title, artist_id))
                    song_record = cursor.fetchone()
                    if song_record:
                        song_id = song_record[0]
                        add_song_to_playlist(1, song_id)  # Ajout à la playlist avec ID 1

                    response = AnnotatedUtterance(
                        f"{title} by {artist} has been added to your playlist.",
                        participant=DialogueParticipant.AGENT,
                    )
                    self._dialogue_connector.register_agent_utterance(response)
                    return
                else:
                    response = AnnotatedUtterance(
                        "Please use the format: add \"song_title\" - \"artist_name\".",
                        participant=DialogueParticipant.AGENT,
                    )
                    self._dialogue_connector.register_agent_utterance(response)
                    return

            elif utterance.text.startswith("remove"):
                parts = utterance.text[7:].split(' - ')
                if len(parts) == 2:
                    title = parts[0].strip('"')
                    artist = parts[1].strip('"')

                    # Suppression de la chanson de la playlist
                    cursor.execute('SELECT song_id FROM songs WHERE title = ? AND artist_id = (SELECT artist_id FROM artists WHERE name = ?)', (title, artist))
                    song_record = cursor.fetchone()
                    if song_record:
                        song_id = song_record[0]
                        remove_song_from_playlist(1, song_id)  # Suppression de la chanson de la playlist avec ID 1

                        response = AnnotatedUtterance(
                            f"{title} by {artist} has been removed from your playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"{title} by {artist} not found in the playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                    self._dialogue_connector.register_agent_utterance(response)
                    return
                else:
                    response = AnnotatedUtterance(
                        "Please use the format: remove \"song_title\" - \"artist_name\".",
                        participant=DialogueParticipant.AGENT,
                    )
                    self._dialogue_connector.register_agent_utterance(response)
                    return


            elif utterance.text.startswith("show"):
                # Montre les chansons de la playlist
                songs = get_songs_from_playlist(1)  # Supposons que l'ID de la playlist est 1 pour l'exemple
                text = ""
                for song in songs:
                    text += f"{song[0]} by {song[1]}\n"  # song[0] est le titre, song[1] l'ID de l'artiste

                if not text:
                    text = "The playlist is empty, try adding new songs."

                response = AnnotatedUtterance(
                    text,
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)
                return

            elif utterance.text.startswith("clear"):
                # Supprimer toutes les chansons de la playlist
                cursor.execute('DELETE FROM playlist_songs')
                response = AnnotatedUtterance(
                    "Your playlist has been cleared.",
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)
                return
            
            elif "date album : " in utterance.text:
                album_name = utterance.text.split("date album :")[-1].strip().strip('"').strip("'")
                cursor.execute('SELECT release_date FROM albums WHERE title = ?', (album_name,))
                release_date_record = cursor.fetchone()
                if release_date_record:
                    response = AnnotatedUtterance(
                        f"The album '{album_name}' was released on {release_date_record[0]}.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't know when the album '{album_name}' was released.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return
            
            elif "genre album : " in utterance.text:
                album_name = utterance.text.split("genre album :")[-1].strip().strip('"').strip("'")
                cursor.execute('SELECT genre FROM albums WHERE title = ?', (album_name,))
                genre_cursor = cursor.fetchone()
                if genre_cursor:
                    response = AnnotatedUtterance(
                        f"The genre of '{album_name}' is {genre_cursor[0]}.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't know the genre of the album '{album_name}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return
            
            elif "number songs :" in utterance.text:
                artist_name = utterance.text.split("number songs :")[-1].strip().strip('"').strip("'")
                cursor.execute('''
                    SELECT COUNT(songs.song_id)
                    FROM songs
                    JOIN artists ON songs.artist_id = artists.artist_id
                    WHERE artists.name = ?
                    GROUP BY artists.name;
                ''', (artist_name,))  
                total_songs_cursor = cursor.fetchone()
                if total_songs_cursor:
                    total_songs = total_songs_cursor[0]
                    response = AnnotatedUtterance(
                        f"The artist '{artist_name}' has {total_songs} songs.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't have information on the number of songs for the artist '{artist_name}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return

            elif "number albums :" in utterance.text:
                artist_name = utterance.text.split("number albums :")[-1].strip().strip('"').strip("'")
                cursor.execute('SELECT total_albums FROM artists WHERE name = ?', (artist_name,))
                total_albums_record = cursor.fetchone()
                if total_albums_record:
                    response = AnnotatedUtterance(
                        f"The artist '{artist_name}' has released {total_albums_record[0]} albums.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't have information about the artist '{artist_name}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return

            elif "which album : " in utterance.text.lower():
                song_title = utterance.text.split("which album : ")[-1].strip().strip('"').strip("'")
                cursor.execute('''
                    SELECT albums.title 
                    FROM albums 
                    INNER JOIN songs ON albums.album_id = songs.album_id 
                    WHERE songs.title = ?
                ''', (song_title,))
                album_record = cursor.fetchone()
                if album_record:
                    response = AnnotatedUtterance(
                        f"The song '{song_title}' is featured in the album '{album_record[0]}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't know which album features the song '{song_title}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return
            
            elif "give song : " in utterance.text:
                artist_name = utterance.text.split("give song :")[-1].strip().strip('"').strip("'")
                cursor.execute('SELECT title FROM songs WHERE artist_id = (SELECT artist_id FROM artists WHERE name = ?)', (artist_name,))
                song_record = cursor.fetchall()
                if song_record:
                    random_song = random.choice(song_record)
                    response = AnnotatedUtterance(
                        f"Here's a song by {artist_name}: {random_song}.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"Sorry, I couldn't find any songs by {artist_name}.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                return

        except IndexError as e:
            print(f"Error while processing user utterance: {e}")
            response = AnnotatedUtterance(
                "I don't understand. Please make sure you have the correct format: {command} [title] [artist].",
                participant=DialogueParticipant.AGENT,
            )
            self._dialogue_connector.register_agent_utterance(response)
            return

        response = AnnotatedUtterance(
            "I don't understand. Please try again.",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)
