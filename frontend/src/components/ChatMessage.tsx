import { MDBIcon } from "mdb-react-ui-kit";
import Feedback from "./Feedback";

function UserChatMessage({ message }: { message: string }): JSX.Element {
  return (
    <div className="d-flex flex-row justify-content-end mb-4">
      <div
        className="p-3 ms-3 border"
        style={{ borderRadius: "15px", backgroundColor: "#fbfbfb" }}
      >
        <p className="small mb-0">{message}</p>
      </div>
      <img
        src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-chat/ava2-bg.webp"
        alt="User"
        style={{ width: "45px", height: "100%" }}
      />
    </div>
  );
}

function AgentChatMessage({
  message,
  image_url,
  feedback,
}: {
  message: string;
  image_url?: string;
  feedback: ((message: string, event: string) => void) | null;
}): JSX.Element {
  return (
    <div className="d-flex flex-row justify-content-start mb-4">
      <div className="text-center">
        <MDBIcon fas size="2x" className="text-muted" icon="robot" />
        {feedback && <Feedback message={message} on_feedback={feedback} />}
      </div>
      <div
        className="p-3 ms-3"
        style={{
          borderRadius: "15px",
          backgroundColor: "rgba(57, 192, 237,.2)",
        }}
      >
        {!!image_url && (
          <div className="d-flex flex-row justify-content-center">
            <img
              src={image_url}
              alt=""
              style={{ width: "200px", height: "100%" }}
            />
          </div>
        )}
        <p className="small mb-0" style={{ whiteSpace: "pre-wrap" }}>{message}</p>
      </div>
    </div>
  );
}

export { UserChatMessage, AgentChatMessage };
