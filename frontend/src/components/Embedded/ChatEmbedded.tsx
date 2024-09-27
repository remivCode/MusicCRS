import "./ChatEmbedded.css";
import { ReactNode } from "react";

export default function ChatEmbedded({ children }: { children: ReactNode }) {
  return (
    <div className="col-md-6 col-sm-12" style={{ height: "fit-container"}}>{children}</div>
  );
}
