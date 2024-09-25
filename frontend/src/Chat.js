import "./App.css";

function Chat() {
  return (
    <div
      id="chatWidgetContainer"
      data-name="Chatbot"
      data-server-url="http://127.0.0.1:5000"
      data-use-feedback
      data-use-login
      data-socketio-path="/socket.io"
    ></div>
  );
}

export default Chat;
