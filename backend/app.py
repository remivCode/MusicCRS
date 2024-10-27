from custom_platform import CustomPlatform
from agent import PlaylistAgent

import spacy
spacy.cli.download("en_core_web_sm")

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Ajouter chargement des messages frontend