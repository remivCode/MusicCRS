import re
from typing import Any, List
import spacy
from spacy.training import Example, offsets_to_biluo_tags
from spacy.util import filter_spans
from spacy.tokens import DocBin
from tqdm import tqdm
import random
from rapidfuzz import process, fuzz
import random
import json
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex
from song import Song
from artist import Artist
from album import Album
import os
import subprocess
import zipfile
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='spacy')

class EntityLinker:
    def __init__(self, db, spacy_model='en_core_web_lg', train=False):
        """
        Initialize the recognizer with a knowledge base and the SpaCy model.
        :param knowledge_base: A dictionary of song titles with associated metadata.
        :param spacy_model: Name of the SpaCy model to use for mention detection.
        """
        print("Initializing EntityLinker...")
        self.db = db

        if train:
            #spacy.cli.download(spacy_model)
            self.nlp = spacy.blank("en")

            ner_dataset_path = os.path.join("data", "elmd2.zip")
            if not os.path.exists(ner_dataset_path):
                print("Downloading data...")
                curl_command = ["curl", "-L", "-o", ner_dataset_path,"http://mtg.upf.edu/system/files/projectsweb/elmd2.zip", "--ssl-no-revoke"]
                result = subprocess.run(curl_command, check=True)

            if not os.path.exists(os.path.join("data", "elmd2")):
                zip_path = os.path.expanduser(ner_dataset_path)
                print("Extracting data...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("data")

            TRAINING_DATA = self.get_training_data()
            self.train_model(TRAINING_DATA)

        print("Loading model...")
        self.nlp = spacy.load(os.path.join("data", "models", "ner_model", "model-best"))

        print("Loading knowledge base...")
        self.knowledge_base = {
            "songs": self.db.read(table="songs", data=["id", "name", "artist_id", "album_id", "popularity"]),
            "artists": self.db.read(table="artists", data=["id", "name", "popularity"]),
            "albums": self.db.read(table="albums", data=["id", "name", "artist_id", "popularity"]),
        }

    def train_model(self, training_data):
        print("Training model...")
        # Add a new entity label if it’s not already there
        if "ner" in self.nlp.pipe_names:
            ner = self.nlp.get_pipe("ner")
        else:
            # If no NER pipeline, create one
            ner = self.nlp.add_pipe("ner")

        # Add the "SONG_TITLE" label to the NER pipeline
        ner.add_label("O")
        ner.add_label("SONG_TITLE")
        ner.add_label("ARTIST_NAME")
        ner.add_label("ALBUM_NAME")

        os.makedirs(os.path.join("data", "models", "ner_model"), exist_ok=True)
        train, dev = train_test_split(training_data, test_size=0.2)
        self.convert_data_to_spacy(self.nlp, os.path.join("data", "models", "ner_model", "training_data.spacy"), train)
        self.convert_data_to_spacy(self.nlp, os.path.join("data", "models", "ner_model", "dev_data.spacy"), dev)
        
        """ other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            optimizer = self.nlp.create_optimizer()
            for itn in range(10):
                losses = {}
                for text, annotations in train:
                    doc = self.nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    print(example)
                    self.nlp.update([example], losses=losses, sgd=optimizer)
                print(f"Loss history: {losses}") """

        self.nlp.to_disk(os.path.join("data", "models", "ner_model", "model-best"))
        ret = subprocess.run(['python', '-m', 'spacy', 'init', 'config', os.path.join("data", "models", "ner_model", "config.cfg"), '--lang', 'en', '--pipeline', 'ner'], shell=True)
        if ret.returncode != 0:
            print("Failed to create config file")
        ret = subprocess.run(['python', '-m', 'spacy', 'train', os.path.join("data", "models", "ner_model", "config.cfg"), '--output', os.path.join("data", "models", "ner_model"), '--paths.train', os.path.join("data", "models", "ner_model", "training_data.spacy"), '--paths.dev', os.path.join("data", "models", "ner_model", "dev_data.spacy"), "--training.optimizer.learn_rate", "0.0001", "--training.optimizer.grad_clip", "0.5", "--training.max_epochs", "10"], shell=True)
        if ret.returncode != 0:
            print("Failed to train model")

        nlp_ner = spacy.load(os.path.join("data", "models", "ner_model", "model-best"))

        # Quick Test
        test_text = "Have you listened to Blinding Lights by The Weeknd?"
        doc = nlp_ner(test_text)

        # Print detected entities
        for ent in doc.ents:
            print(f"Entity: {ent.text}, Label: {ent.label_}")

    def convert_data_to_spacy(self, nlp, path, data):
        doc_bin = DocBin()
        
        # Training the model
        for example in tqdm(data):
            text = example[0]
            entities = example[1]["entities"]

            doc = nlp.make_doc(text)
            ents = []

            for start, end, label in entities:
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is not None:
                    ents.append(span)

            if len(ents) == 0:
                continue
            filtered_ents = filter_spans(ents)
            doc.ents = filtered_ents
            doc_bin.add(doc)

        doc_bin.to_disk(path)

    def get_training_data(self):
        """
        Get the training data from the knowledge base.
        :return: A list of training data.
        """
        print("Getting training data...")
        output = []
        json_files = os.listdir(os.path.join("data", "elmd2"))
        for i, file in tqdm(enumerate(json_files)):
            with open(os.path.join("data", "elmd2", file), "r") as f:
                data = json.load(f)

                entities = []

                for sentence in data:
                    text = sentence["text"]
                    for ent in sentence["entities"]:
                        category = ent["category"]
                        if category == "Artist":
                            entity = "ARTIST_NAME"
                        elif category == "Album":
                            entity = "ALBUM_NAME"
                        elif category == "Track":
                            entity = "SONG_TITLE"
                        else:
                            continue
                        start = ent["startChar"]
                        end = ent["endChar"]

                        overlap = False
                        for existing_ent in entities:
                            if (start < existing_ent[1] and end > existing_ent[0]) or (start > existing_ent[0] and end < existing_ent[1]):
                                overlap = True
                                break

                        if not overlap:
                            entities.append((start, end, entity))
                    
                # Append the reformatted entry to output
                output.append((text, {"entities": entities}))

        with open(os.path.join("data", "training_data_500_sentences.json"), "r") as f:
            data = json.load(f)
            for entry in data:
                text = entry[0]
                entities = entry[1]["entities"]
                output.append((text, {"entities": entities}))
        
        return output

    def mention_detection(self, text, n=3, labels=['SONG_TITLE', 'ARTIST_NAME', 'ALBUM_NAME']):
        """
        Detect mentions of potential song titles in the text.
        :param text: Input text.
        :return: List of detected song title mentions.
        """
        """ doc = self.nlp(text)
        mentions = defaultdict(list)
        for i, ent in enumerate(doc.ents):
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
            mentions[ent.label_].append(ent.text)
        print(f"mentions: {mentions}")
        return mentions """
        mentions = []
        words = re.findall(r'\w+', text)
        print(f"words: {words}")
        for i in range(len(words)):
            for j in range(1, n + 1):
                if i + j > len(words):
                    break
                ngram = ' '.join(words[i:i+j])
                mentions.append(ngram)
        print(f"mentions: {mentions}")
        return mentions
    
    def clean_text(self, text):
        # Convert to lower case and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def song_candidate_selection(self, mentions, limit=3):
        """
        Select candidate songs from the knowledge base based on the mention using fuzzy matching.
        :param mention: The detected song title mention.
        :param limit: Number of candidates to return.
        :return: List of (song, score) tuples.
        """
        total_song_candidates = []
           
        print("Reading from knowledge base...")
        records = self.knowledge_base["songs"]

        songs = [Song(title=row[1], id_=row[0], artist_id=row[2], album_id=row[3], popularity=row[4]) for row in records]

        song_titles_cleaned = [self.clean_text(title) for title in [song.title for song in songs]] # Le faire au début une fois pour toute quand on définit la knowledge base

        for mention in mentions:
            mention = self.clean_text(mention)
            song_candidates = process.extract(mention, song_titles_cleaned, limit=limit, scorer=fuzz.ratio)
            song_candidates = [(songs[idx], score + len(mention) * 5) for _, score, idx in song_candidates]
            total_song_candidates += song_candidates

        print(f"Song candidates: {total_song_candidates}")

        return total_song_candidates
    

    def album_candidate_selection(self, mentions, limit=3):
        """
        Select candidate albums from the knowledge base based on the mention using fuzzy matching.
        :param mention: The detected album title mention.
        :param limit: Number of candidates to return.
        :return: List of (song, score) tuples.
        """
        total_album_candidates = []
           
        print("Reading from knowledge base...")
        records = self.knowledge_base["albums"]

        albums = [Album(name=row[1], id_=row[0], artist_id=row[2], popularity=row[3]) for row in records]

        album_titles_cleaned = [self.clean_text(name) for name in [album.name for album in albums]] # Le faire au début une fois pour toute quand on définit la knowledge base

        for mention in mentions:
            mention = self.clean_text(mention)
            album_candidates = process.extract(mention, album_titles_cleaned, limit=limit, scorer=fuzz.ratio)
            album_candidates = [(albums[idx], score + len(mention) * 5) for _, score, idx in album_candidates]
            total_album_candidates += album_candidates

        print(f"Album candidates: {total_album_candidates}")

        return total_album_candidates

    
    def artist_candidate_selection(self, mentions, limit=10):
        """
        Select candidate artists from the knowledge base based on the mention using fuzzy matching.
        :param mention: The detected artist name mention.
        :param limit: Number of candidates to return.
        :return: List of (artist, score) tuples.
        """
        total_artist_candidates = []
           
        print("Reading from knowledge base...")
        records = self.knowledge_base["artists"]

        artists = [Artist(name=row[1], id_=row[0], popularity=row[2]) for row in records]

        artist_titles_cleaned = [self.clean_text(name) for name in [artist.name for artist in artists]] # Le faire au début une fois pour toute quand on définit la knowledge base

        for mention in mentions:
            mention = self.clean_text(mention)
            artist_candidates = process.extract(mention, artist_titles_cleaned, limit=limit, scorer=fuzz.ratio)
            artist_candidates = [(artists[idx], score + len(mention) * 5) for _, score, idx in artist_candidates]
            total_artist_candidates += artist_candidates

        print(f"Artist candidates: {total_artist_candidates}")

        return total_artist_candidates

    def song_disambiguation(self, mention, candidates, context: dict[str, Any] = None):
        """
        Disambiguate the correct song from the candidates, using context if available.
        :param mention: The song title mention.
        :param candidates: List of (song, score) tuples.
        :param context: Optional context (e.g., artist, album) to improve disambiguation.
        :return: The final selected song (most likely match).
        """       
        # Use context (artist, album) to boost candidates with matching metadata
        print("Song disambiguation...")
        for i, (song, score) in enumerate(candidates):    
            candidates[i] = (song, score + song.popularity )

        for i, (song, score) in enumerate(candidates): 
            if context:           
                if context.get("artists"):
                    for j, artist in enumerate(context["artists"]):
                        if artist.id == song.artist_id:
                            print(f"artist.name: {artist.name}, position: {j}, old score: {score}, new score: {score + (len(context['artists']) - j) * 10}")
                            candidates[i] = (song, score + (len(context["artists"]) - j) * 10)  # Boost score if artist matches
                
                if context.get("album"):
                    for j, album in enumerate(context["albums"]):
                        if album.id == song.album_id:
                            candidates[i] = (song, score + (len(context["albums"]) - j) * 5)  # Boost score if artist matches

        print([(candidate[0].title, candidate[0].artist_name, candidate[1]) for candidate in sorted(candidates, key=lambda x: x[1], reverse=True)[:10]])
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:10]  # Return the songs with the highest scores
    

    def album_disambiguation(self, mention, candidates, context: dict[str, Any] = None):
        """
        Disambiguate the correct album from the candidates, using context if available.
        :param mention: The song title mention.
        :param candidates: List of (album, score) tuples.
        :param context: Optional context (e.g., artist, album) to improve disambiguation.
        :return: The final selected song (most likely match).
        """       
        # Use context (artist, album) to boost candidates with matching metadata
        print("Album disambiguation...")
        for i, (album, score) in enumerate(candidates):    
            candidates[i] = (album, score + album.popularity) 

        for i, (album, score) in enumerate(candidates):
            if context:           
                if context.get("artists"):
                    for j, artist in enumerate(context["artists"]):
                        if artist.id == album.artist_id:
                            print(f"artist.name: {artist.name}, position: {j}, old score: {score}, new score: {score + (len(context['artists']) - j) * 10}")
                            candidates[i] = (album, score + album.popularity + (len(context["artists"]) - j) * 10)  # Boost score if artist matches

        print([(candidate[0].name, candidate[1]) for candidate in sorted(candidates, key=lambda x: x[1], reverse=True)[:10]])
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:10]  # Return the songs with the highest scores
    



    def artist_disambiguation(self, mention, candidates):
        """
        Disambiguate the correct artist from the candidates, using context if available.
        :param mention: The artist name mention.
        :param candidates: List of (artist, score) tuples.
        :param context: Optional context (album) to improve disambiguation.
        :return: The final selected artist (most likely match).
        """
        print("Artist disambiguation...")
        for i, (artist, score) in enumerate(candidates):
            candidates[i] = (artist, score + artist.popularity)
        
        print([(candidate[0].name, candidate[1]) for candidate in sorted(candidates, key=lambda x: x[1], reverse=True)[:10]])
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:10]  # Return the songs with the highest scores



    def recognize_song(self, text, context: dict[str, Any] = None):
        """
        The complete pipeline: Mention detection, candidate selection, and disambiguation.
        :param text: Input text to process.
        :param context: Optional context (artist, album).
        :return: The recognized song title or None if not found.
        """
        mentions = self.mention_detection(text=text)
        if not mentions:
            return None

        candidates = self.song_candidate_selection(mentions)
        if candidates:
            best_match = self.song_disambiguation(mentions, candidates, context)
            for song, score in best_match:
                artist = [artist[1] for artist in self.knowledge_base["artists"] if artist[0] == song.artist_id][0] #Tuple index out of range
                album = [album[1] for album in self.knowledge_base["albums"] if album[0] == song.album_id][0]
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
        mentions = self.mention_detection(text=text, labels="ARTIST_NAME")
        if not mentions:
            return None

        candidates = self.artist_candidate_selection(mentions)
        if candidates:
            best_match = self.artist_disambiguation(mentions, candidates)
            print(f"best_match: {best_match}")
            return best_match
        return None
    
    def recognize_album(self, text, context: dict[str, Any] = None):
        """
        The complete pipeline: Mention detection, candidate selection, and disambiguation.
        :param text: Input text to process.
        :param context: Optional context (artist, album).
        :return: The recognized song title or None if not found.
        """
        mentions = self.mention_detection(text=text, labels="ALBUM_NAME")
        if not mentions:
            return None

        candidates = self.album_candidate_selection(mentions)
        if candidates:
            best_match = self.album_disambiguation(mentions, candidates, context=context)
            print(f"best_match: {best_match}")
            return best_match
        return None

    def recognize_song_in_playlist(self, text: str, playlist: List[Song]) -> List[Song]:
        mentions = self.mention_detection(text=text)
        if not mentions:
            return None

        total_song_candidates = []

        song_titles_cleaned = [self.clean_text(title) for title in [song.title for song in playlist]] # Le faire au début une fois pour toute quand on définit la knowledge base

        for mention in mentions:
            mention = self.clean_text(mention)
            song_candidates = process.extract(mention, song_titles_cleaned, limit=3, scorer=fuzz.ratio)
            song_candidates = [(playlist[idx], score) for _, score, idx in song_candidates]
            total_song_candidates += song_candidates

        print(f"Song candidates: {total_song_candidates}")

        if song_candidates:
            best_match = self.song_disambiguation(mentions, song_candidates)
            return best_match
