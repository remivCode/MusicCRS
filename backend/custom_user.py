from dialoguekit.participant.user import User, UserType
from playlist import Playlist
import logging

class CustomUser(User):
    def __init__(self, id: str, user_type: UserType = UserType.HUMAN) -> None:
        super().__init__(id, user_type=user_type)
        self._playlist: int = None
        self._db: Playlist = None

    def connect_playlist(self, playlist_id: int, db: Playlist) -> None:
        self._playlist = playlist_id
        self._db = db

        logging.debug(f"user playlist id {self._playlist}")

