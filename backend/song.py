from dataclasses import dataclass

@dataclass
class Song():
    def __init__(self, title: str, artist: str, album: str):
        self.title = title
        self.artist = artist
        self.album = album