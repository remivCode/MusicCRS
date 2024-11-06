import "./ChatBox.css";

import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useContext,
} from "react";
import QuickReplyButton from "../QuickReply";
import { useSocket } from "../../contexts/SocketContext";
import { UserContext } from "../../contexts/UserContext";
import {
  MDBCard,
  MDBCardHeader,
  MDBCardBody,
  MDBIcon,
  MDBCardFooter,
  MDBBtn
} from "mdb-react-ui-kit";
import { AgentChatMessage, UserChatMessage } from "../ChatMessage";
import { ChatMessage, Command, Song, Annotation } from "../../types";
import { ConfigContext } from "../../contexts/ConfigContext";

export default function ChatBox() {
  const { config } = useContext(ConfigContext);
  const { user } = useContext(UserContext);
  const {
    startConversation,
    sendMessage,
    quickReply,
    onMessage,
    onRestart,
    giveFeedback,
    socket
  } = useSocket();
  const [chatMessages, setChatMessages] = useState<JSX.Element[]>([]);
  const [chatButtons, setChatButtons] = useState<JSX.Element[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const chatMessagesRef = useRef(chatMessages);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [commands, setCommands] = useState([
    {key: "EXIT", desc: "End the conversation", syntax: "EXIT"},
  ]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    startConversation();
  }, [startConversation]);

  const updateMessages = (message: JSX.Element) => {
    chatMessagesRef.current = [...chatMessagesRef.current, message];
    setChatMessages(chatMessagesRef.current);
  };

  const handleInput = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (inputValue.trim() === "") return;
    updateMessages(
      <UserChatMessage
        key={chatMessagesRef.current.length}
        message={inputValue}
      />
    );
    sendMessage({ message: inputValue });
    setIsLoading(true);
    setInputValue("");
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleQuickReply = useCallback(
    (message: string) => {
      updateMessages(
        <UserChatMessage
          key={chatMessagesRef.current.length}
          message={message}
        />
      );
      quickReply({ message: message });
    },
    [chatMessagesRef, quickReply]
  );

  const handelMessage = useCallback(
    (message: ChatMessage) => {
      if (!!message.text) {
        const image_url = message.attachments?.find(
          (attachment) => attachment.type === "images"
        )?.payload.images?.[0];
        const updatedMessages = chatMessagesRef.current.map((chatMessage, index) => {
          if (index === chatMessagesRef.current.length - 1) return chatMessage;
          return React.cloneElement(chatMessage, { last_message: false });
        });
        chatMessagesRef.current = updatedMessages;

        const choices: Song[] = []
        
        const intent = message.intent
        if (intent === "add") {
          const annotations: Annotation[] = message.annotations
          annotations.map((annotation) => {
            const song: Song = annotation.value
            choices.push(song)
            }
          )
        }

        updateMessages(
          <AgentChatMessage
            key={chatMessagesRef.current.length}
            feedback={config.useFeedback ? giveFeedback : null}
            message={message.text}
            image_url={image_url}
            last_message={true}
            choices={choices}
          />
        );
      }
    },
    [giveFeedback, chatMessagesRef, config]
  );

  const handleButtons = useCallback(
    (message: ChatMessage) => {
      const buttons = message.attachments?.find(
        (attachment) => attachment.type === "buttons"
      )?.payload.buttons;
      if (!!buttons && buttons.length > 0) {
        setChatButtons(
          buttons.map((button, index) => {
            return (
              <QuickReplyButton
                key={index}
                text={button.title}
                message={button.payload}
                click={handleQuickReply}
              />
            );
          })
        );
      } else {
        setChatButtons([]);
      }
    },
    [handleQuickReply]
  );

  useEffect(() => {
    onMessage((message: ChatMessage) => {
      handelMessage(message);
      setIsLoading(false);
      handleButtons(message);
    });
  }, [onMessage, handleButtons, handelMessage]);

  useEffect(() => {
    onRestart(() => {
      setChatMessages([]);
      setChatButtons([]);
    });
  }, [onRestart]);

  const handleToggleHelp = () => {
    setShowHelp(!showHelp);
  };

  useEffect(() => {
    socket?.on("commands", (data: Command[]) => { // Errors here
      setCommands((prevCommands) => [...prevCommands, ...data]);
    });
  }, [socket]);

  return (
    <div className="chat-widget-content">
      <MDBCard
        id="chatBox"
        className="chat-widget-card"
        style={{ borderRadius: "15px" }}
      >
        <MDBCardHeader
          className="d-flex justify-content-between align-items-center p-3 bg-info text-white border-bottom-0"
          style={{
            borderTopLeftRadius: "15px",
            borderTopRightRadius: "15px",
          }}
        >
          <p className="mb-0 fw-bold">{config.name}</p>
          <p className="mb-0 fw-bold">{user?.username}</p>
        </MDBCardHeader>

        <MDBCardBody>
          <div className="card-body-messages">
            {chatMessages}
            {isLoading && 
              <div className="loading-message-box">
                <div className="spinner-grow text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <div className="spinner-grow text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <div className="spinner-grow text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            }
            <div className="d-flex flex-wrap justify-content-between">
              {chatButtons}
            </div>
          </div>
        </MDBCardBody>
        <MDBCardFooter className="text-muted d-flex justify-content-start align-items-center p-2">
          <form className="d-flex flex-grow-1" onSubmit={handleInput}>
            <input
              type="text"
              className="form-control form-control-lg"
              id="ChatInput"
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type message"
              ref={inputRef}
            ></input>
            <button type="submit" className="btn btn-link text-muted">
              <MDBIcon fas size="2x" icon="paper-plane" />
            </button>
          </form>
        </MDBCardFooter>
      </MDBCard>
      
      <MDBBtn color='info' onClick={handleToggleHelp} style={{ width: '150px' }}>
        {showHelp ? 'Hide Help' : 'Show Help'}
      </MDBBtn>

      {showHelp && (
        <div className='mt-3'>
          <h4>Available Commands:</h4>
          <ul>
          {commands.map((command, index) => (
            <li key={index}>
              <strong>{command.desc}</strong>
            </li>
          ))}
          </ul>
        </div>
      )}
    </div>
  );
}
