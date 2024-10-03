from __future__ import annotations

from flask import request

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
        print("Converting message...")
        print(utterance.annotations)
        message = CustomMessage(utterance.text)
        if isinstance(utterance, AnnotatedUtterance):
            message.intent = str(utterance.intent)
            message.annotations = [
                        {"slot": annotation.slot, "value": annotation.value}
                        for annotation in utterance.annotations
                    ]
        print(message)
        return message

@dataclass
class CustomResponse:
    recipient: str
    message: CustomMessage

class CustomPlatform(FlaskSocketPlatform):

    def __init__(self, agent_class: Type[Agent]) -> None:
        super().__init__(agent_class=agent_class)
        self._active_users: Dict[str, CustomUser] = {}
        self._playlist: Playlist = Playlist()

    def connect(self, user_id: str) -> None:
        """Connects a user to an agent.

        Args:
            user_id: User ID.
        """
        print("Connecting...")
        self._active_users[user_id] = CustomUser(user_id)

        agent = self.get_new_agent()
        agent.connect_playlist(self._playlist)
        
        user = self._active_users[user_id]
        print(type(user))
        user.connect_playlist(self._playlist)

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
        print("Starting namespace...")
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
        self._playlist.remove(song)

    def add(self, user_id: str, add: dict) -> None:
        song = Song(add["title"], add["artist"], add["album"])
        self._playlist.add(song)

    def clear(self, user_id: str) -> None:
        self._playlist.clear()

class CustomNamespace(ChatNamespace):
    def __init__(self, namespace: str, platform: CustomPlatform) -> None:
        super().__init__(namespace, platform)

    def on_remove(self, data: dict) -> None:
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.remove(req.sid, data["remove"])
        logger.info(f"Message received: {data}")

    def on_add(self, data: dict) -> None:
        print("Adding song...")
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.add(req.sid, data["add"])
        logger.info(f"Message received: {data}")

    def on_clear(self, data: dict) -> None:
        req: SocketIORequest = cast(SocketIORequest, request)
        self._platform.clear(req.sid)
        logger.info(f"Message received: {data}")