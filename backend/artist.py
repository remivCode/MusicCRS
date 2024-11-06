class Artist():
    def __init__(self, id_: str, name: str, popularity: int = 0, clean_artist_name: str = None):
        self.id = id_
        self.name = name
        self.popularity = popularity
        self.clean_artist_name = clean_artist_name