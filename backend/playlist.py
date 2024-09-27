from typing import List
from song import Song
import uuid 

class Playlist():
    def __init__(self, name: str = "My playlist", description: str = ""):
        self.id = uuid.uuid1()
        self.name = name
        self.description = description
        self.songs: List[Song] = []

    def add(self, song: Song):
        self.songs.append(song)
    
    def remove(self, song: Song):
        self.songs.remove(song)

    def show(self):
        return [f"{song.title} - {song.artist} - {song.album}" for song in self.songs]
    
    def clear(self):
        self.songs = []