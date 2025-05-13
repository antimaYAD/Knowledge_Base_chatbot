import React from "react";

const ModeSelector = ({ currentMode, onModeChange }) => {
  return (
    <div className="flex items-center space-x-4 mb-4">
      <span className="text-sm font-medium text-gray-700">Chatbot Mode:</span>
      <select
        value={currentMode}
        onChange={(e) => onModeChange(e.target.value)}
        className="pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
      >
        <option value="friendlymode">Friendly Mode</option>
        <option value="krishna">Krishna Mode</option>
      </select>
    </div>
  );
};

export default ModeSelector;
