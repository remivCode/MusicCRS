from typing import List
from dialoguekit.core.annotated_utterance import AnnotatedUtterance, Annotation
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from dialoguekit.core.intent import Intent
from playlist import Playlist
import uuid
import os
import time
from threading import Thread
import random
from song import Song
import datetime
import sqlite3
from entity_linker import EntityLinker


class PlaylistAgent(Agent):
    def __init__(self, id: str):
        """Playlist agent."""
        super().__init__(id)

        self.commands = {
            "add": {
                "desc": "Add a song to the playlist.",
                "syntax": "add <title> - <artist>",
                },
            "remove": {
                "desc": "Remove a song from the playlist.",
                "syntax": "remove <title> - <artist>",
                },
            "show": {
                "desc": "Show the current playlist.",
                "syntax": "show",
                },
            "clear": {
                "desc": "Clear the playlist.",
                "syntax": "clear",
                },
            "date album": {
                "desc": "Ask about the release date of an album.",
                "syntax": "date album : <album>",
                },
            "genre artist": {
                "desc": "Ask about the genre of a song.",
                "syntax": "genre artist : <artist>",
                },
            "number songs": {
                "desc": "Ask about the number of songs in an artist.",
                "syntax": "number songs : <artist>",
                },
            "number albums": {
                "desc": "Ask about the number of albums by an artist.",
                "syntax": "number albums : <artist>",
                },
            "which album": {
                "desc": "Ask which album contains a song.",
                "syntax": "which album : <title>",
                },
            "give song": {
                "desc": "Ask for a random song by an artist.",
                "syntax": "give song : <artist>",
                },
        }
        self.used_commands = set()
        self.interaction_count = 0 

    def introduce_new_features(self) -> None:
        """Introduce new features that the user hasn't used yet."""
        unused_commands = set(self.commands.keys()) - self.used_commands
        if unused_commands:
            random_command = random.choice(list(unused_commands))
            suggestion_text = f"You haven't tried the '{random_command}' command. {self.commands[random_command]['syntax']}"
            response = AnnotatedUtterance(
                suggestion_text,
                participant=DialogueParticipant.AGENT,
            )
            time.sleep(0.5)
            self._dialogue_connector.register_agent_utterance(response)

    def get_commands(self) -> list:
        return [{
            "key": key,
            "desc": value["desc"],
            "syntax": value["syntax"],
        } for key, value in self.commands.items()]

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        msg = "Hello, I'm here to assist you with making your personalized music playlist.\n" + '\n' + "Commands:" + '\n' + '\n'.join([f"{value['syntax']}: {value['desc']}" for value in self.commands.values()])
        
        utterance = AnnotatedUtterance(
            msg,
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

    def connect_playlist(self, playlist: int, db: Playlist, entity_linker: EntityLinker) -> None:
        self.playlist = playlist
        self.db = db
        self.entity_linker = entity_linker

        print(f"agent playlist id {self.playlist}")

    def check_for_suggestions(self):
        if self.interaction_count % 3 == 0:
            Thread(target=self.introduce_new_features).start()

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance."""
        self.interaction_count += 1
        print(f"interaction_count: {self.interaction_count}")

        if utterance.text == "EXIT":
            self.goodbye()
            return

        try:
            if utterance.text.startswith("add"):
                self.used_commands.add("add")
                artists = self.entity_linker.recognize_artist(utterance.text)
                if artists:
                    context = {"artists": [artist[0] for artist in artists]}
                else:
                    context = {}
                songs = self.entity_linker.recognize_song(utterance.text[4:], context=context)
                if songs:
                    try:
                        response = self.generate_add_response(songs)
                    except sqlite3.IntegrityError as e:
                        print(e)
                        response = AnnotatedUtterance(
                            f"The song \"{songs[0].title}\" by \"{songs[0].artist}\" is already in the playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                else:
                    response = AnnotatedUtterance(
                            f"Sorry but I couldn't understand which song you want to add.",
                            participant=DialogueParticipant.AGENT,
                        )

                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif utterance.text.startswith("remove"):
                self.used_commands.add("remove")
                playlist_songs = [Song(id_=song[0], title=song[1], artist_name=song[2], album_name=song[3], artist_id=song[4], album_id=song[5]) for song in self.db.read_songs_from_playlist(playlist_id=self.playlist, data=('songs.id', 'songs.name', 'artists.name', 'albums.name', 'artists.id', 'albums.id'))]
                songs = self.entity_linker.recognize_song_in_playlist(utterance.text, playlist_songs)
                song_to_delete = songs[0][0]
                print(f"song_to_delete: {song_to_delete}")
                try:
                    self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_to_delete.id})
                    response = self.generate_remove_response(song_to_delete)
                except Exception as e:
                    print(f"Error: {e}")
                    response = AnnotatedUtterance(
                        f"{song_to_delete.title} by {song_to_delete.artist_name} not found in the playlist.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif utterance.text.startswith("show"):
                self.used_commands.add("show")
                print(f"playlist: {self.playlist}")
                songs = self.db.read_songs_from_playlist(playlist_id=self.playlist, data=['songs.name', 'artists.name'])
                text = ""
                print(f"songs: {songs}")
                for song in songs:
                    text += f"{song[0]} by {song[1]}\n"  # song[0] est le titre, song[1] l'ID de l'artiste

                if not text:
                    text = "The playlist is empty, try adding new songs."

                response = AnnotatedUtterance(
                    text,
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif utterance.text.startswith("clear"):

                self.used_commands.add("clear")
                self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist})

                response = AnnotatedUtterance(
                    "Your playlist has been cleared.",
                    participant=DialogueParticipant.AGENT,
                    intent=Intent(label="clear")
                )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "date album : " in utterance.text:
                self.used_commands.add("date album")

                try:
                    artists = self.entity_linker.recognize_artist(utterance.text)
                    if artists:
                        context = {"artists": [artist[0] for artist in artists]}
                    else:
                        context = {}

                    albums = self.entity_linker.recognize_album(utterance.text, context=context)
                    album = albums[0][0]
                    release_date_record = self.db.read(table='albums', data=['release_date'], where=f'id = "{album.id}"')
                    if release_date_record:
                        release_date_timestamp = release_date_record[0][0]
                        date = datetime.datetime.fromtimestamp(release_date_timestamp / 1000)
                        response = AnnotatedUtterance(
                            f"The album '{album.name}' was released on {date.strftime('%Y-%m-%d')}.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know when the album '{album.name}' was released.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The album \"{album.name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "genre artist : " in utterance.text:
                self.used_commands.add("genre artist")
                artists = self.entity_linker.recognize_artist(utterance.text)
                artist = artists[0][0]

                try:
                    artist_record = self.db.read(table='artists', data=['id', 'genre', 'name'], where=f'id = "{artist.id}"')
                    if artist_record:
                        artist_id = artist_record[0][0]
                        artist_genre = artist_record[0][1]
                        artist_name = artist_record[0][2]
                        print(f"artist_genre: {artist_genre}")
                        plural_singular = "genres are"
                        if len(artist_genre) < 2:
                            plural_singular = " genre is"
                        if artist_genre:
                            response = AnnotatedUtterance(
                                f"{artist_name}'s {plural_singular} {', '.join(artist_genre)}.",
                                participant=DialogueParticipant.AGENT,
                            )
                        else:
                            response = AnnotatedUtterance(
                                f"I don't know the genre of the artist '{artist_name}'.",
                                participant=DialogueParticipant.AGENT,
                            )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know the artist '{artist}'.",
                            participant=DialogueParticipant.AGENT,
                        )

                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist.name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )

                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "number songs :" in utterance.text:
                self.used_commands.add("number songs")
                artists = self.entity_linker.recognize_artist(utterance.text)
                artist = artists[0][0]

                try:
                    total_songs_by_album_by_artist = self.db.read(
                        table='albums',
                        data=['total_songs'],
                        where=f'artist_id = "{str(artist.id)}"'
                    )
                    if total_songs_by_album_by_artist:
                        total_songs = sum([item[0] for item in total_songs_by_album_by_artist])
                        
                        response = AnnotatedUtterance(
                            f"The artist '{artist.name}' has {total_songs} songs.",
                            participant=DialogueParticipant.AGENT,
                        )

                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist.name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "number albums :" in utterance.text:
                self.used_commands.add("number albums")

                artists = self.entity_linker.recognize_artist(utterance.text)
                artist = artists[0][0]

                try:
                    total_albums_record = self.db.read(table='artists', data=['total_albums'], where=f'id = "{artist.id}"')
                    if total_albums_record:
                        response = AnnotatedUtterance(
                            f"The artist '{artist.name}' has released {total_albums_record[0][0]} albums.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't have information about the artist '{artist.name}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    print(e)
                    response = AnnotatedUtterance(
                        f"The artist \"{artist.name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "which album : " in utterance.text.lower():
                self.used_commands.add("which album")
                artists = self.entity_linker.recognize_artist(utterance.text)
                if artists:
                    context = {"artists": [artist[0] for artist in artists]}
                else:
                    context = {}
                songs = self.entity_linker.recognize_song(utterance.text, context=context)
                song = songs[0][0]

                try:
                    album_record = self.db.read_album_from_song(song_id=song.id, data=['albums.name'])
                    if album_record:
                        response = AnnotatedUtterance(
                            f"The song '{song.title}' is featured in the album(s) '{', '.join(album[0] for album in album_record)}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know which album features the song '{song.title}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The song \"{song.title}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "give song : " in utterance.text:
                self.used_commands.add("give song")
                artists = self.entity_linker.recognize_artist(utterance.text)
                artist = artists[0][0]

                try:
                    song_record = self.db.read(table='songs', data=['name'], where=f'artist_id = "{artist.id}"')
                    if song_record:
                        random_song = random.choice(song_record)
                        response = AnnotatedUtterance(
                            f"Here's a song by {artist.name}: {random_song[0]}.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"Sorry, I couldn't find any songs by {artist.name}.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist.name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

        except InterruptedError as e:
            print(f"Error while processing user utterance: {e}")
            response = AnnotatedUtterance(
                "I don't understand. Please make sure you have the correct format.",
                participant=DialogueParticipant.AGENT,
            )
            self._dialogue_connector.register_agent_utterance(response)
            self.check_for_suggestions()
            return

        response = AnnotatedUtterance(
            "I don't understand. Please try again.",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)

    def generate_add_response(self, songs: List[Song]) -> AnnotatedUtterance:
        """
        Generates a response to display the songs to add

        Args:
            song: The Song instance that was added to the playlist.

        Returns:
            AnnotatedUtterance: The response to be sent to the user.
        """
        response = AnnotatedUtterance(
            "Please select the songs you want to add to the playlist : ",
            participant=DialogueParticipant.AGENT,
            intent=Intent(label="add")
        )

        annotations = [
            Annotation(
                slot=i,
                value={
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist_name,
                    "album": song.album_name
                }
            ) for i, (song, score) in enumerate(songs)
        ]
        response.add_annotations(annotations)

        return response
    
    def generate_remove_response(self, song: Song) -> AnnotatedUtterance:
        """
        Generates a response when a song is removed from the playlist.

        Args:
            song: The Song instance that was removed from the playlist.

        Returns:
            AnnotatedUtterance: The response to be sent to the user.
        """
        response = AnnotatedUtterance(
            song.title + " by " + song.artist_name + " has been removed from your playlist.",
            participant=DialogueParticipant.AGENT,
            intent=Intent(label="remove")
        )

        annotations = [
            Annotation(
                slot="song",
                value={
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist_name,
                    "album": song.album_name
                }
            )
        ]
        response.add_annotations(annotations)

        return response
