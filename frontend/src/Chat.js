import "./App.css";
import { useEffect } from "react";

function Chat() {
  useEffect(() => {
    // Create a script element
    const script = document.createElement("script");

    // Set the script attributes
    script.type = "text/javascript";
    script.src =
      "https://cdn.jsdelivr.net/npm/iaigroup-chatwidget@latest/build/bundle.min.js";

    // Append the script to the document body (or head)
    document.body.appendChild(script);
  }, []);
  return (
    <div
      id="chatWidgetContainer"
      data-name="Chatbot"
      data-server-url="http://127.0.0.1:5000"
      data-use-feedback
      data-use-login
    ></div>
  );
}

export default Chat;
