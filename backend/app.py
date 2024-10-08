from dialoguekit.platforms import FlaskSocketPlatform
from agent import PlaylistAgent

platform = FlaskSocketPlatform(PlaylistAgent)

platform.start()
