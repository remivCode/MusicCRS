class Album():
    def __init__(self, id_: str, name: str, popularity: int = 0, artist_id: str = None, artist_name: str = None, clean_album_title: str = None):
        self.id = id_
        self.name = name
        self.popularity = popularity
        self.artist_id = artist_id
        self.artist_name = artist_name
        self.clean_album_title = clean_album_title