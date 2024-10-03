import { useContext } from "react";
import "./App.css";
import { ConfigContext } from "./contexts/ConfigContext";
import { UserContext } from "./contexts/UserContext";
import ChatBox from "./components/ChatBox/ChatBox";
import LoginForm from "./components/LoginForm/LoginForm";
import ChatWidget from "./components/Widget/ChatWidget";
import ChatEmbedded from "./components/Embedded/ChatEmbedded";
import Playlist from "./components/Playlist/Playlist";

export default function App() {
  const { config } = useContext(ConfigContext);
  const { user } = useContext(UserContext);

  const content = !user && config.useLogin ? <LoginForm /> : <ChatBox />;
  return config.useWidget ? (
    <ChatWidget>{content}</ChatWidget>
  ) : (
  <div className="main-container">
    <ChatEmbedded>{content}</ChatEmbedded>
    <Playlist />
  </div>
  );
}
