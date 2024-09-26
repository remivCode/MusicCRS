from dialoguekit.platforms import FlaskSocketPlatform
from agent import ParrotAgent

platform = FlaskSocketPlatform(ParrotAgent)

platform.start()


