from __future__ import annotations
import os, uuid

from flask import request
import logging

from dialoguekit.platforms.flask_socket_platform import FlaskSocketPlatform, logger, SocketIORequest, ChatNamespace
from dialoguekit.connector import DialogueConnector
from typing import Type, Dict, Any, List, cast
from dataclasses import asdict, dataclass
from dialoguekit.core import Utterance, AnnotatedUtterance

from custom_user import CustomUser
from playlist import Playlist

from song import Song

from dialoguekit.participant import Agent

@dataclass
class CustomMessage:
    text: str
    intent: str = None
    annotations: List[Dict[str, Any]] = None

    @classmethod
    def from_utterance(self, utterance: Utterance) -> CustomMessage:
        """Converts an utterance to a message.

        Args:
            utterance: An instance of Utterance.

        Returns:
            An instance of Message.
        """
        logging.info("Converting message...")
        logging.debug(utterance.annotations)
        message = CustomMessage(utterance.text)
        if isinstance(utterance, AnnotatedUtterance):
            message.intent = str(utterance.intent)
            message.annotations = [
                        {"slot": annotation.slot, "value": annotation.value}
                        for annotation in utterance.annotations
                    ]
        logging.debug(message)
        return message

@dataclass
class CustomResponse:
    recipient: str
    message: CustomMessage

class CustomPlatform(FlaskSocketPlatform):

    def __init__(self, agent_class: Type[Agent]) -> None:
        super().__init__(agent_class=agent_class)
        self._active_users: Dict[str, CustomUser] = {}
        if os.path.exists('music.db'):
            self.db = Playlist(id=uuid.uuid4().hex, init=False)
        else:
            self.db = Playlist(id=uuid.uuid4().hex)
            self.db.populate_data()

        self.playlist = self.db.create(table='playlists', data={'name': 'My Playlist'})
        # self.db.insert_data(playlist=self.playlist)

    def connect(self, user_id: str) -> None:
        """Connects a user to an agent.

        Args:
            user_id: User ID.
        """
        logging.info("Connecting...")
        self._active_users[user_id] = CustomUser(user_id)

        agent = self.get_new_agent()
        agent.connect_playlist(self.playlist, self.db)
        commands = agent.get_commands()
        self.socketio.emit("commands", commands, room=user_id)
        
        user = self._active_users[user_id]
        user.connect_playlist(self.playlist, self.db)
    
        logging.debug(f"platform playlist id {self.playlist}")

        songs = self.db.read_songs_from_playlist(playlist_id=self.playlist, data=('songs.title', 'artists.name', 'albums.title'))
        song_data = [{"title": song[0], "artist": song[1], "album": song[2]} for song in songs]
        self.socketio.emit("playlist", song_data, room=user_id)

        dialogue_connector = DialogueConnector(
            agent=agent,
            user=user,
            platform=self,
        )
        dialogue_connector.start()

    def start(self, host: str = "127.0.0.1", port: str = "5000") -> None:
        """Starts the platform.

        Args:
            host: Hostname.
            port: Port.
        """
        logging.info("Starting namespace...")
        self.socketio.on_namespace(CustomNamespace("/", self))
        self.socketio.run(self.app, host=host, port=port)

    def display_agent_utterance(
        self, user_id: str, utterance: Utterance
    ) -> None:
        """Emits agent utterance to the client.

        Args:
            user_id: User ID.
            utterance: An instance of Utterance.
        """
        message = CustomMessage.from_utterance(utterance)
        self.socketio.send(
            asdict(CustomResponse(user_id, message)),
            room=user_id,
        )

    def remove(self, user_id: str, remove: dict) -> None:
        song = Song(remove["title"], remove["artist"], remove["album"])
        try:
            artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': song.artist})
            song_record = self.db.read(table='songs', data=['song_id'], where={'title': song.title, 'artist_id': artist_record[0][0]})
            song_id = song_record[0][0]
            playlist_song_record = self.db.read(table='playlist_songs', data=['playlist_id'], where={'playlist_id': self.playlist, 'song_id': song_id})
            logging.debug(f"deleted playlist_song _record: {playlist_song_record}")
            self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

        except Exception as e:
            logging.error(f"Error: {e}")
            

    def add(self, user_id: str, add: dict) -> None:
        song = Song(add["title"], add["artist"], add["album"])
        artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': song.artist})
        if not artist_record:
            # Si l'artiste n'existe pas, l'ajouter (exemple sans genre et albums pour simplifier)
            self.db.create(table='artists', data={'name': song.artist})
            artist_record = self.db.read(table='artists', data=['artist_id'], where={'name': song.artist})

        artist_id = artist_record[0][0]

        album_record = self.db.read(table='albums', data=['album_id'], where={'title': song.album})
        if not album_record:
            if not song.album:
                song.album = "Unknown"
            self.db.create(table='albums', data={'title': song.album})
            album_record = self.db.read(table='albums', data=['album_id'], where={'title': song.album})

        album_id = album_record[0][0]

        self.db.create(table='songs', data={'title': song.title, 'artist_id': artist_id, 'album_id': album_id})

        song_record = self.db.read(table='songs', data=['song_id'], where={'title': song.title, 'artist_id': artist_id})
        if song_record:
            song_id = song_record[0][0]
            self.db.create(table='playlist_songs', data={'playlist_id': self.playlist, 'song_id': song_id})

    def clear(self, user_id: str) -> None:
        self.db.delete(table='playlist_songs', data={'playlist_id': self.playlist})

class CustomNamespace(ChatNamespace):
    def __init__(self, namespace: str, platform: CustomPlatform) -> None:
        super().__init__(namespace, platform)

    def on_connect(self) -> None:
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.connect(req.sid)
        logger.info(f"Client connected; user_id: {req.sid}")

    def on_remove(self, data: dict) -> None:
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.remove(req.sid, data["remove"])
        logger.info(f"Message received: {data}")

    def on_add(self, data: dict) -> None:
        logging.info("Adding song...")
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.add(req.sid, data["add"])
        logger.info(f"Message received: {data}")

    def on_clear(self, data: dict) -> None:
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.clear(req.sid)
        logger.info(f"Message received: {data}")