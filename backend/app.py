from custom_platform import CustomPlatform
from agent import PlaylistAgent

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Ajouter un son plusieurs fois avec chaque album dans la playlist:
# Télécharger tous les sons