from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from playlist import Playlist
import uuid
import os
import random


class PlaylistAgent(Agent):
    def __init__(self, id: str):
        """Playlist agent."""
        super().__init__(id)
        if os.path.exists('music.db'):
            self.db = Playlist(id=uuid.uuid4().hex, init=False)
        else:
            self.db = Playlist(id=uuid.uuid4().hex)
            self.playlist = self.db.create(table='playlists', data={'name': 'My Playlist'})

        self.playlist = self.db.create(table='playlists', data={'name': 'My Playlist'})
        self.db.insert_data(playlist=self.playlist)

        self.commands = {
            "add": "Add a song to the playlist.",
            "remove": "Remove a song from the playlist.",
            "show": "Show the current playlist.",
            "clear": "Clear the playlist.",
            "date album": "Ask about the release date of an album.",
            "genre album": "Ask about the genre of an album.",
            "number songs": "Ask about the number of songs in an album.",
            "number albums": "Ask about the number of albums by an artist.",
            "which album": "Ask which album contains a song.",
            "give song": "Ask for a random song by an artist.",
        }
        self.used_commands = set()
        self.interaction_count = 0 

    def introduce_new_features(self) -> None:
        """Introduce new features that the user hasn't used yet."""
        unused_commands = set(self.commands.keys()) - self.used_commands
        if unused_commands:
            random_command = random.choice(list(unused_commands))
            suggestion_text = f"You haven't tried the '{random_command}' command. {self.commands[random_command]}"
            response = AnnotatedUtterance(
                suggestion_text,
                participant=DialogueParticipant.AGENT,
            )
            self._dialogue_connector.register_agent_utterance(response)


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

    def check_for_suggestions(self):
        if self.interaction_count % 3 == 0:
            self.introduce_new_features()

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

                    # Ajout de la chanson à la base de données
                    artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})
                    if not artist_record:
                        # Si l'artiste n'existe pas, l'ajouter (exemple sans genre et albums pour simplifier)
                        self.db.create(table='artists', data={'name': artist})
                        artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})

                    print(f"artist_record: {artist_record}")
                    artist_id = artist_record[0][0]

                    self.db.create(table='songs', data={'title': title, 'artist_id': artist_id, 'album_id': None})

                    song_record = self.db.read(table='songs', data=['song_id'], where={'title': title, 'artist_id': artist_id})
                    if song_record:
                        song_id = song_record[0][0]
                        self.db.create(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

                    response = AnnotatedUtterance(
                        f"{title} by {artist} has been added to your playlist.",
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

                    # Suppression de la chanson de la playlist
                    print(f"title: {title} - artist: {artist}")
                    try:
                        artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist})
                        song_record = self.db.read(table='songs', data=['song_id'], where={'title': title, 'artist_id': artist_record[0][0]})
                        song_id = song_record[0][0]
                        playlist_song_record = self.db.read(table='playlist_songs', data=['playlist_id'], where={'playlist_id': self.playlist, 'song_id': song_id})
                        print(f"deleted playlist_song _record: {playlist_song_record}")
                        self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

                        response = AnnotatedUtterance(
                            f"{title} by {artist} has been removed from your playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                        response = AnnotatedUtterance(
                            f"{title} by {artist} not found in the playlist.",
                            participant=DialogueParticipant.AGENT,
                        )
                    self._dialogue_connector.register_agent_utterance(response)
                    self.check_for_suggestions()
                    return
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
                )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "date album : " in utterance.text:
                self.used_commands.add("date album")
                album_name = utterance.text.split("date album :")[-1].strip().strip('"').strip("'")

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
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "genre album : " in utterance.text:
                self.used_commands.add("genre album")
                album_name = utterance.text.split("genre album :")[-1].strip().strip('"').strip("'")

                genre_cursor = self.db.read(table='albums', data=['genre'], where={'title': album_name})
                if genre_cursor:
                    response = AnnotatedUtterance(
                        f"The genre of '{album_name}' is {genre_cursor[0][0]}.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't know the genre of the album '{album_name}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "number songs :" in utterance.text:
                self.used_commands.add("number songs")
                artist_name = utterance.text.split("number songs :")[-1].strip().strip('"').strip("'")
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
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "number albums :" in utterance.text:
                self.used_commands.add("number albums")
                artist_name = utterance.text.split("number albums :")[-1].strip().strip('"').strip("'")
                total_albums_record = self.db.read(table='albums', data=['total_albums'], where={'artist_id': artist_id})
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
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return

            elif "which album : " in utterance.text.lower():
                self.used_commands.add("which album")
                song_title = utterance.text.split("which album : ")[-1].strip().strip('"').strip("'")
                album_record = self.db.read_album_from_song(song_title, data=['albums.title'])
                if album_record:
                    response = AnnotatedUtterance(
                        f"The song '{song_title}' is featured in the album(s) '{[album for album in album_record]}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                else:
                    response = AnnotatedUtterance(
                        f"I don't know which album features the song '{song_title}'.",
                        participant=DialogueParticipant.AGENT,
                    )
                self._dialogue_connector.register_agent_utterance(response)
                self.check_for_suggestions()
                return
            
            elif "give song : " in utterance.text:
                self.used_commands.add("give song")
                artist_name = utterance.text.split("give song :")[-1].strip().strip('"').strip("'")

                artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': artist_name})
                song_record = self.db.read(table='songs', data=['title'], where={'artist_id': artist_record[0][0]})
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
                self.check_for_suggestions()
                return
            
            if self.interaction_count % 1 == 0:
                self.introduce_new_features()

        except IndexError as e:
            print(f"Error while processing user utterance: {e}")
            response = AnnotatedUtterance(
                "I don't understand. Please make sure you have the correct format: {command} [title] [artist].",
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
        self.check_for_suggestions()
