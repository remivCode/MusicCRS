from custom_platform import CustomPlatform
from agent import PlaylistAgent

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Afficher le nom de l'album frontend
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Toujours afficher la suggestion après la réponse
# Télécharger tous les sons
# Ajouter le genre