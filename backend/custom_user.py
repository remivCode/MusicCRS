from dialoguekit.participant.user import User, UserType
from playlist import Playlist

class CustomUser(User):
    def __init__(self, id: str, user_type: UserType = UserType.HUMAN) -> None:
        super().__init__(id, user_type=user_type)
        self._playlist: Playlist = None

    def connect_playlist(self, playlist: Playlist) -> None:
        self._playlist = playlist

