import spacy
from fuzzywuzzy import process

class EntityLinker:
    def __init__(self, db, spacy_model='en_core_web_sm'):
        """
        Initialize the recognizer with a knowledge base and the SpaCy model.
        :param knowledge_base: A dictionary of song titles with associated metadata.
        :param spacy_model: Name of the SpaCy model to use for mention detection.
        """
        self.db = db
        self.nlp = spacy.load(spacy_model)

        # Add custom label for song titles if it's not already there
        if 'ner' in self.nlp.pipe_names:
            self.ner = self.nlp.get_pipe("ner")
            if 'SONG_TITLE' not in self.ner.labels:
                self.ner.add_label("SONG_TITLE")
        
        # Optionally train SpaCy's NER here if needed with labeled data.

    def mention_detection(self, text, label="SONG_TITLE"):
        """
        Detect mentions of potential song titles in the text.
        :param text: Input text.
        :return: List of detected song title mentions.
        """
        doc = self.nlp(text)
        for i, ent in enumerate(doc.ents):
            if i > 10:
                break
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
        mentions = [ent.text for ent in doc.ents if ent.label_ == label]
        print(f"mentions: {mentions}")
        return mentions
    
    def candidate_selection(self, mentions, limit=10):
        """
        Select candidate songs from the knowledge base based on the mention using fuzzy matching.
        :param mention: The detected song title mention.
        :param limit: Number of candidates to return.
        :return: List of (song, score) tuples.
        """
        artist_candidates = None
        album_candidates = None
        if mentions["artist"]:
            artist_names = self.db.read(table='artists', data=['name', 'id'], limit=10)
            artist_candidates = process.extract(mentions["artist"], [name for name, _ in artist_names], limit=limit)
            artist_candidates = [(id, name, score) for name, score in artist_candidates for artist_name, id in artist_names if name == artist_name]
            print(f"Artist candidates: {artist_candidates}")

            if mentions["album"]:
                if artist_candidates:
                    where = f'artist_id IN ({", ".join([artist_id for artist_id, _, _ in artist_candidates])})'
                else:
                    where = None
                album_names = self.db.read(table='albums', data=['name', 'id'], where=where, limit=10)
                album_candidates = process.extract(mentions["album"], [name for name, _ in album_names], limit=limit)
                album_candidates = [(id, name, score) for name, score in album_candidates for album_name, id in album_names if name == album_name]
                print(f"Album candidates: {album_candidates}")

        if artist_candidates:
            where = f'artist_id IN ({", ".join(["?"] * len(artist_candidates))})'
        else:
            where = None
        song_titles = self.db.read(table='songs', data=['name'], where=where, limit=10)
        candidates = process.extract(mentions["song"], song_titles, limit=limit)
        return candidates

    def disambiguation(self, mention, candidates, context=None):
        """
        Disambiguate the correct song from the candidates, using context if available.
        :param mention: The song title mention.
        :param candidates: List of (song, score) tuples.
        :param context: Optional context (e.g., artist, album) to improve disambiguation.
        :return: The final selected song (most likely match).
        """
        ranked_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        
        # Use context (artist, album) to boost candidates with matching metadata
        if context:
            for i, (candidate, score) in enumerate(ranked_candidates):
                song_metadata = self.knowledge_base.get(candidate)
                
                if context.get("artist") and context["artist"] == song_metadata.get("artist"):
                    ranked_candidates[i] = (candidate, score + 10)  # Boost score if artist matches
                
                if context.get("album") and context["album"] == song_metadata.get("album"):
                    ranked_candidates[i] = (candidate, score + 5)  # Boost score if album matches

        return ranked_candidates[0][0]  # Return the song with the highest score

    def recognize_song(self, text, context=None):
        """
        The complete pipeline: Mention detection, candidate selection, and disambiguation.
        :param text: Input text to process.
        :param context: Optional context (artist, album).
        :return: The recognized song title or None if not found.
        """
        mentions = self.mention_detection(text)
        if not mentions:
            return None

        candidates = self.candidate_selection(mentions)
        if candidates:
            best_match = self.disambiguation(mentions, candidates, context)
            return best_match
        return None
    
    def recognize_artist(self, text):
        """
        The complete pipeline: Mention detection, candidate selection, and disambiguation.
        :param text: Input text to process.
        :param context: Optional context (artist, album).
        :return: The recognized song title or None if not found.
        """
        mentions = self.mention_detection(text, "ARTIST_NAME")
        if not mentions:
            return None

        candidates = self.candidate_selection(mentions)
        if candidates:
            best_match = self.disambiguation(mentions, candidates)
            return best_match
        return None