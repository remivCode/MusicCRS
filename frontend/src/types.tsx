export type ChatMessageButton = {
  title: string;
  payload: string;
  button_type: string;
};

export type ChatMessageAttachment = {
  type: string;
  payload: {
    images?: string[];
    buttons?: ChatMessageButton[];
  };
};

export type ChatMessage = {
  attachments?: ChatMessageAttachment[];
  text?: string;
  intent?: string;
  annotations: Annotation[];
};

export type Annotation = {
  slot: string;
  value: string;
};

export type Song = {
  title?: string;
  artist?: string;
  album?: string;
};

export type Command = {
  key: string;
  desc: string;
  syntax: string;
};

export type AgentMessage = {
  recipient: string;
  message: ChatMessage;
  info?: string;
};

export type UserMessage = {
  message: string;
};
