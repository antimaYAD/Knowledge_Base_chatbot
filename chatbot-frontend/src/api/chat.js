import api from "./index";

// Send a single message to the chatbot
export const sendMessage = async (message, mode = "friendlymode") => {
  const response = await api.post("/api/v1/chat/chat", {
    message,
    mode,
  });
  return response.data;
};

// Send full conversation history (for context-aware responses)
export const sendConversation = async (messages, mode = "friendlymode") => {
  const response = await api.post("/api/v1/chat/smart-chat/query", {
    messages,
    mode,
  });
  return response.data;
};
