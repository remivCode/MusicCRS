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
            "genre song": {
                "desc": "Ask about the genre of a song.",
                "syntax": "genre song : <title> - <artist>",
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

    def connect_playlist(self, playlist: int, db: Playlist) -> None:
        self.playlist = playlist
        self.db = db

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
                parts = utterance.text[4:].split(' - ')
                if len(parts) == 2:
                    title = parts[0].strip('"')
                    artist = parts[1].strip('"')

                    song = Song(title=title, artist=artist, album=None)
                    try:
                        artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})
                        artist_id = artist_record[0][0]
                        song_record = self.db.read(table='songs', data=['song_id', 'album_id'], where={'title': title, 'artist_id': artist_id})

                        album_record = self.db.read(table='albums', data=['title'], where={'album_id': song_record[0][1]})
                        if album_record:
                            song.album = album_record[0][0]
                        else:
                            song.album = "Unknown"
                        song_id = song_record[0][0]
                        self.db.create(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

                        response = self.generate_add_response(song)
                    except Exception as e:
                        print(e)
                        response = AnnotatedUtterance(
                            f"The song \"{title}\" by \"{artist}\" does not exist in the database.",
                            participant=DialogueParticipant.AGENT,
                        )

                    self._dialogue_connector.register_agent_utterance(response)
                    self.check_for_suggestions()
                    return
                else:
                    response = AnnotatedUtterance(
                        "Please use the format: add \"song_title\" - \"artist_name\".",
                        participant=DialogueParticipant.AGENT,
                    )

                    self._dialogue_connector.register_agent_utterance(response)
                    return

            elif utterance.text.startswith("remove"):
                self.used_commands.add("remove")
                parts = utterance.text[7:].split(' - ')
                if len(parts) == 2:
                    title = parts[0].strip('"')
                    artist = parts[1].strip('"')

                    song = Song(title=title, artist=artist or None, album=None)

                    try:
                        artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})
                        song_record = self.db.read(table='songs', data=['song_id'], where={'title': title, 'artist_id': artist_record[0][0]})
                        song_id = song_record[0][0]

                        self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

                        response = self.generate_remove_response(song)
                    except Exception as e:
                        print(f"Error: {e}")
                        response = AnnotatedUtterance(
                            f"{title} by {artist} not found in the playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                else:
                    response = AnnotatedUtterance(
                        "Please use the format: remove \"song_title\" - \"artist_name\".",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif utterance.text.startswith("show"):
                self.used_commands.add("show")
                print(f"playlist: {self.playlist}")
                songs = self.db.read_songs_from_playlist(playlist_id=self.playlist, data=('songs.title', 'artists.name'))
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
                album_name = utterance.text.split("date album :")[-1].strip().strip('"').strip("'")

                try:
                    release_date_record = self.db.read(table='albums', data=['release_date'], where={'title': album_name})
                    if release_date_record:
                        response = AnnotatedUtterance(
                            f"The album '{album_name}' was released on {release_date_record[0][0]}.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know when the album '{album_name}' was released.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The album \"{album_name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "genre song : " in utterance.text:
                self.used_commands.add("genre song")
                parts = utterance.text[13:].split(' - ')
                title = parts[0].strip('"').strip("'")
                artist = parts[1].strip('"').strip("'")

                try:
                    artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})
                    if artist_record:
                        artist_id = artist_record[0][0]
                        genre_cursor = self.db.read(table='songs', data=['genre'], where={'title': title, 'artist_id': artist_id})
                        print(f"genre_cursor: {genre_cursor}")
                        if genre_cursor:
                            response = AnnotatedUtterance(
                                f"\"{title}\"'s genres are {genre_cursor[0][0]}.",
                                participant=DialogueParticipant.AGENT,
                            )
                        else:
                            response = AnnotatedUtterance(
                                f"I don't know the genre of the song '{title}'.",
                                participant=DialogueParticipant.AGENT,
                            )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know the artist '{artist}'.",
                            participant=DialogueParticipant.AGENT,
                        )

                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The song \"{title}\" by \"{artist}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )

                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "number songs :" in utterance.text:
                self.used_commands.add("number songs")
                artist_name = utterance.text.split("number songs :")[-1].strip().strip('"').strip("'")

                try:
                    artist = self.db.read(table='artists', data=['artist_id'], where={'name': artist_name})
                    if artist:
                        artist_id = artist[0][0]
                        total_songs_by_album_by_artist = self.db.read(
                            table='albums',
                            data=['total_songs'],
                            where={'artist_id': str(artist_id)}
                        )
                        if total_songs_by_album_by_artist:
                            total_songs = sum([item[0] for item in total_songs_by_album_by_artist])
                            
                            response = AnnotatedUtterance(
                                f"The artist '{artist_name}' has {total_songs} songs.",
                                participant=DialogueParticipant.AGENT,
                            )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't have information on the number of songs for the artist '{artist_name}'.",
                            participant=DialogueParticipant.AGENT,
                        )

                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist_name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "number albums :" in utterance.text:
                self.used_commands.add("number albums")
                artist_name = utterance.text.split("number albums :")[-1].strip().strip('"').strip("'")

                try:
                    artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist_name})
                    total_albums_record = self.db.read(table='artists', data=['total_albums'], where={'artist_id': artist_record[0][0]})
                    if total_albums_record:
                        response = AnnotatedUtterance(
                            f"The artist '{artist_name}' has released {total_albums_record[0][0]} albums.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't have information about the artist '{artist_name}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist_name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "which album : " in utterance.text.lower():
                self.used_commands.add("which album")
                song_title = utterance.text.split("which album : ")[-1].strip().strip('"').strip("'")

                try:
                    album_record = self.db.read_album_from_song(song_title=song_title, data=['albums.title'])
                    if album_record:
                        response = AnnotatedUtterance(
                            f"The song '{song_title}' is featured in the album(s) '{', '.join(album[0] for album in album_record)}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"I don't know which album features the song '{song_title}'.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The song \"{title}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "give song : " in utterance.text:
                self.used_commands.add("give song")
                artist_name = utterance.text.split("give song :")[-1].strip().strip('"').strip("'")

                try:
                    artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist_name})

                    song_record = self.db.read(table='songs', data=['title'], where={'artist_id': artist_record[0][0]})
                    if song_record:
                        random_song = random.choice(song_record)
                        response = AnnotatedUtterance(
                            f"Here's a song by {artist_name}: {random_song[0]}.",
                            participant=DialogueParticipant.AGENT,
                        )
                    else:
                        response = AnnotatedUtterance(
                            f"Sorry, I couldn't find any songs by {artist_name}.",
                            participant=DialogueParticipant.AGENT,
                        )
                except Exception as e:
                    response = AnnotatedUtterance(
                        f"The artist \"{artist_name}\" does not exist in the database.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            if self.interaction_count % 1 == 0:
                self.introduce_new_features()

        except IndexError as e:
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

    def generate_add_response(self, song: Song) -> AnnotatedUtterance:
        """
        Generates a response when a song is added to the playlist.

        Args:
            song: The Song instance that was added to the playlist.

        Returns:
            AnnotatedUtterance: The response to be sent to the user.
        """
        response = AnnotatedUtterance(
            song.title + " by " + song.artist + " has been added to your playlist.",
            participant=DialogueParticipant.AGENT,
            intent=Intent(label="add")
        )

        annotations = [
            Annotation(
                slot="artist",
                value=song.artist
            ),
            Annotation(
                slot="title",
                value=song.title
            ),
            Annotation(
                slot="album",
                value=song.album
            )
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
            song.title + " by " + song.artist + " has been removed from your playlist.",
            participant=DialogueParticipant.AGENT,
            intent=Intent(label="remove")
        )

        annotations = [
            Annotation(
                slot="artist",
                value=song.artist
            ),
            Annotation(
                slot="title",
                value=song.title
            ),
            Annotation(
                slot="album",
                value=song.album
            )
        ]
        response.add_annotations(annotations)

        return response
        self.check_for_suggestions()
