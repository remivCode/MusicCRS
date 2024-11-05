class Song():
    def __init__(self, id_: str, title: str, artist_name: str = None, album_name: str = None, popularity: int = 0, artist_id: str = None, album_id: str = None):
        self.id = id_
        self.title = title
        self.artist_name = artist_name
        self.album_name = album_name
        self.popularity = popularity
        self.artist_id = artist_id
        self.album_id = album_id

        def __repr__(self):
            return f"Song(id={self.id}, title='{self.title}', artist_name='{self.artist_name}', album_name='{self.album_name}', popularity={self.popularity}, artist_id={self.artist_id}, album_id={self.album_id})"