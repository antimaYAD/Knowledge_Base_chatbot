import React from "react";

const MessageBubble = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-md px-4 py-2 rounded-lg ${
          isUser ? "bg-indigo-500 text-white" : "bg-gray-200 text-gray-800"
        }`}
      >
        <div
          className="whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ __html: message.content }}
        />
      </div>
    </div>
  );
};

export default MessageBubble;
