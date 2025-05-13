import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  sendChatMessage,
  addMessage,
  clearMessages,
  setMode,
} from "../features/chat/chatSlice";
import {
  selectMessages,
  selectChatLoading,
  selectChatError,
  selectChatMode,
} from "../features/chat/chatSelectors";
import ChatInput from "../components/chat/ChatInput";
import MessageBubble from "../components/chat/MessageBubble";
import ModeSelector from "../components/chat/ModeSelector";

const Chat = () => {
  const dispatch = useDispatch();
  const messages = useSelector(selectMessages);
  const isLoading = useSelector(selectChatLoading);
  const error = useSelector(selectChatError);
  const currentMode = useSelector(selectChatMode);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const chatContainer = document.getElementById("chat-messages");
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = (content) => {
    // Add user message to state
    dispatch(addMessage({ role: "user", content }));

    // Send message to API
    dispatch(
      sendChatMessage({
        message: content,
        mode: currentMode,
      })
    );
  };

  const handleModeChange = (mode) => {
    dispatch(setMode(mode));
  };

  const handleClearChat = () => {
    dispatch(clearMessages());
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">
          {currentMode === "krishna" ? "Krishna Wisdom" : "Health Assistant"}
        </h1>

        <div className="flex space-x-4">
          <ModeSelector
            currentMode={currentMode}
            onModeChange={handleModeChange}
          />

          <button
            onClick={handleClearChat}
            className="px-3 py-1 text-sm text-gray-600 hover:text-red-600 border border-gray-300 rounded-md"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 p-4 rounded-md mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Chat Messages Container */}
      <div
        id="chat-messages"
        className="flex-1 bg-white rounded-lg shadow-inner p-4 overflow-y-auto mb-4"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>
              {currentMode === "krishna"
                ? "Ask for wisdom from the Bhagavad Gita..."
                : "Ask me anything about health..."}
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              isUser={message.role === "user"}
            />
          ))
        )}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="mt-auto">
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default Chat;
