from custom_platform import CustomPlatform
from agent import PlaylistAgent

platform = CustomPlatform(PlaylistAgent)

platform.start()

# TODO
# Empecher d'ajouter avec le frontend
# Empecher d'ajouter 2 fois le même son
# Ajouter un son plusieurs fois avec chaque album dans la playlist:
# Tester toutes les options
# Ajouter chargement des messages frontend
# Passer le genre sur les artistes et pas sur les sons