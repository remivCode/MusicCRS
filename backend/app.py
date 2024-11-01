from custom_platform import CustomPlatform
from agent import PlaylistAgent

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Ajouter chargement des messages frontend