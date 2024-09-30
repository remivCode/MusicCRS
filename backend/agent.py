from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from playlist import Playlist
from song import Song


class PlaylistAgent(Agent):
    def __init__(self, id: str):
        """Playlist agent.

        This agent manages a playlist depending on what the user utters.
        To end the conversation the user has to say `EXIT`.

        Args:
            id: Agent id.
        """
        super().__init__(id)
        self.playlist = Playlist()

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            "Hello, I'm here to assist you with making your personnalized music playlist.\n" + '\n' +
            "Commands:" + '\n'
            "add <artist> - <title>: add a song to the playlist" + '\n' +
            "remove <artist> - <title>: remove a song from the playlist" + '\n' +
            "clear: clear the playlist" + '\n' +
            "show: show the playlist" + '\n',
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def goodbye(self) -> None:
        """Sends the agent's goodbye message."""
        utterance = AnnotatedUtterance(
            "It was nice talking to you. Bye!",
            dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance.

        If the received message is "EXIT" it will close the conversation.

        Args:
            utterance: User utterance.
        """
        if utterance.text == "EXIT":
            self.goodbye()
            return
        try:
            if utterance.text.split()[0] == "add":
                artist = utterance.text.split()[1]
                title = utterance.text.split()[3]
                song = Song(title=title, artist=artist, album=None)
                self.playlist.add(song)
                response = AnnotatedUtterance(
                    utterance.text.split()[1] + " has been added to your playlist.",
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)
                return

            elif utterance.text.split()[0] == "remove":
                artist = utterance.text.split()[1]
                title = utterance.text.split()[3]
                song = Song(title=title, artist=artist or None, album=None)
                self.playlist.remove(song)
                response = AnnotatedUtterance(
                    utterance.text.split()[1] + " has been removed from your playlist.",
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)
                return
            
            elif utterance.text.split()[0] == "show":
                text = ""
                for el in self.playlist.show():
                    text += el 
                    text += "\n"
                
                if text == "":
                    text = "The playlist is empty, try adding new songs."
                    
                response = AnnotatedUtterance(
                    text,
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)

                return

            elif utterance.text.split()[0] == "clear":
                self.playlist.clear()
                response = AnnotatedUtterance(
                    "Your playlist has been cleared.",
                    participant=DialogueParticipant.AGENT,
                )
                self._dialogue_connector.register_agent_utterance(response)

                return
        
        except IndexError as e:
            print(f"Error while processing user utterance: {e}")
            response = AnnotatedUtterance(
                "I don't understand. Please make sure you have the correct format: {command} [title] [artist].",
                participant=DialogueParticipant.AGENT,
            )
            self._dialogue_connector.register_agent_utterance(response)

            return

        response = AnnotatedUtterance(
            "I don't understand. Please try again.",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)