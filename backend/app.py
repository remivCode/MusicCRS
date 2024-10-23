from custom_platform import CustomPlatform
from agent import PlaylistAgent

import logging

logging.basicConfig(
    level=logging.INFO,  # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format of log messages
)

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Ajouter un son plusieurs fois avec chaque album dans la playlist:
# Télécharger tous les sons