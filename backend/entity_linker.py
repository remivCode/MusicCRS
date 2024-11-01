import re
from typing import List
import spacy
from spacy.training import Example
from spacy.util import minibatch
import random
from rapidfuzz import process, fuzz
import random
import json
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex
from song import Song
import os

class EntityLinker:
    def __init__(self, db, spacy_model='en_core_web_sm', train=False):
        """
        Initialize the recognizer with a knowledge base and the SpaCy model.
        :param knowledge_base: A dictionary of song titles with associated metadata.
        :param spacy_model: Name of the SpaCy model to use for mention detection.
        """
        self.db = db

        if train:
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load(spacy_model)
            TRAINING_DATA = self.get_training_data()
            self.train_model(nlp, TRAINING_DATA)
            os.makedirs(os.path.join("data", "models", "ner_model"), exist_ok=True)
            nlp.to_disk(os.path.join("data", "models", "ner_model"))

        self.nlp = spacy.load(os.path.join("data", "models", "ner_model"))

        self.knowledge_base = {
            "song": self.db.read(table="songs", data=["id", "name", "artist_id", "album_id", "popularity"]),
            "artist": self.db.read(table="artists", data=["id", "name", "popularity"]),
            "album": self.db.read(table="albums", data=["id", "name", "artist_id", "popularity"]),
        }

    def train_model(self, nlp, training_data):
        # Add a new entity label if it’s not already there
        if "ner" in nlp.pipe_names:
            ner = nlp.get_pipe("ner")
        else:
            # If no NER pipeline, create one
            ner = nlp.add_pipe("ner")

        # Add the "SONG_TITLE" label to the NER pipeline
        ner.add_label("SONG_TITLE")
        ner.add_label("ARTIST_NAME")
        ner.add_label("ALBUM_NAME")
        
        # Training the model
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
        with nlp.disable_pipes(*other_pipes):  # Only train NER

            # Initialize training loop
            optimizer = nlp.create_optimizer()
            
            # Number of iterations (can increase for better accuracy)
            n_iter = 10
            
            for itn in range(n_iter):
                random.shuffle(training_data)
                losses = {}

                # Batch examples using minibatch
                batches = minibatch(training_data, size=8)
                for batch in batches:
                    examples = []
                    for text, annotations in batch:
                        doc = nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)

                    # Update the model with examples
                    nlp.update(examples, drop=0.35, losses=losses, sgd=optimizer)
                
                print(f"Iteration {itn + 1}, Loss: {losses['ner']}")

        # Quick Test
        test_text = "Have you listened to Blinding Lights by The Weeknd?"
        doc = nlp(test_text)

        # Print detected entities
        for ent in doc.ents:
            print(f"Entity: {ent.text}, Label: {ent.label_}")

    def get_training_data(self):
        """
        Get the training data from the knowledge base.
        :return: A list of training data.
        """
        output = []
        with open("data/training_data_500_sentences.json", "r") as f:
            data = json.load(f)

        for sentence in data:
            for i in range(0, len(sentence), 2):
                text = sentence[i]
                entities = sentence[i + 1]["entities"]
                
                # Reformatting entities
                formatted_entities = []
                for start, end, label in entities:
                    if label == "SONG_TITLE":
                        formatted_entities.append((start, end, "SONG_TITLE"))
                    elif label == "ARTIST_NAME":
                        formatted_entities.append((start, end, "ARTIST_NAME"))
                    elif label == "ALBUM_NAME":
                        continue  # You can choose to include/exclude based on your needs
                
                # Append the reformatted entry to output
                output.append((text, {"entities": formatted_entities}))
        
        return output

    def mention_detection(self, text, labels=['SONG_TITLE', 'ARTIST_NAME', 'ALBUM_NAME']):
        """
        Detect mentions of potential song titles in the text.
        :param text: Input text.
        :return: List of detected song title mentions.
        """
        doc = self.nlp(text)
        mentions = defaultdict(list)
        for i, ent in enumerate(doc.ents):
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
            mentions[ent.label_].append(ent.text)
        print(f"mentions: {mentions}")
        return mentions
    
    def clean_text(self, text):
        # Convert to lower case and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def song_candidate_selection(self, mentions, limit=10):
        """
        Select candidate songs from the knowledge base based on the mention using fuzzy matching.
        :param mention: The detected song title mention.
        :param limit: Number of candidates to return.
        :return: List of (song, score) tuples.
        """
        song_candidates = None

        if "SONG_TITLE" in mentions.keys():            
            print("Reading from knowledge base...")
            records = self.knowledge_base["song"]

            song_titles = [row[1] for row in records]
            songs = [Song(title=row[1], id_=row[0], artist_id=row[2], album_id=row[3], popularity=row[4]) for row in records]

            song_titles_cleaned = [self.clean_text(title) for title in [song.title for song in songs]] # Le faire au début une fois pour toute quand on définit la knowledge base

            mention = self.clean_text(mentions["SONG_TITLE"][0])

            song_candidates = process.extract(mention, song_titles_cleaned, limit=limit, scorer=fuzz.ratio)
            song_candidates = [(songs[idx], score) for _, score, idx in song_candidates]
            print(f"Song candidates: {song_candidates}")

        return song_candidates

    def disambiguation(self, mention, candidates, context=None):
        """
        Disambiguate the correct song from the candidates, using context if available.
        :param mention: The song title mention.
        :param candidates: List of (song, score) tuples.
        :param context: Optional context (e.g., artist, album) to improve disambiguation.
        :return: The final selected song (most likely match).
        """       
        # Use context (artist, album) to boost candidates with matching metadata
        print("Disambiguation...")
        for i, (song, score) in enumerate(candidates):     
            if context:           
                if context.get("artist") and context["artist"]["id"] == song.artist_id:
                    candidates[i] = (song, score + 30)  # Boost score if artist matches
                
                if context.get("album") and context["album"][id] == song.album_id:
                    candidates[i] = (song, score + 20)  # Boost score if album matches

            candidates[i] = (song, score + song.popularity)

        print(sorted(candidates, key=lambda x: x[1], reverse=True)[:10])
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:10]  # Return the songs with the highest scores

    def recognize_song(self, text, context=None) -> List[Song]:
        """
        The complete pipeline: Mention detection, candidate selection, and disambiguation.
        :param text: Input text to process.
        :param context: Optional context (artist, album).
        :return: The recognized song title or None if not found.
        """
        mentions = self.mention_detection(text)
        if not mentions:
            return None

        candidates = self.song_candidate_selection(mentions)
        if candidates:
            best_match = self.disambiguation(mentions, candidates, context)
            for song, score in best_match:
                artist = [artist[1] for artist in self.knowledge_base["artist"] if artist[0] == song.artist_id][0] #Tuple index out of range
                album = [album[1] for album in self.knowledge_base["album"] if album[0] == song.album_id][0]
                song.artist_name = artist
                song.album_name = album
            print(f"best_match: {best_match}")
            return best_match
        # Créer les objets sons à partir de la liste de candidats

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