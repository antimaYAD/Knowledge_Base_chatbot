import React from "react";
import { Outlet, Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { logout } from "../features/auth/authSlice";
import { selectChatMode } from "../features/chat/chatSelectors";
import { setMode } from "../features/chat/chatSlice";

const MainLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const currentMode = useSelector(selectChatMode);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  const handleModeChange = (mode) => {
    dispatch(setMode(mode));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-indigo-600">AI Chatbot</h1>

          <div className="flex items-center space-x-4">
            {/* Mode Switcher */}
            <div className="relative">
              <select
                value={currentMode}
                onChange={(e) => handleModeChange(e.target.value)}
                className="pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
              >
                <option value="friendlymode">Friendly Mode</option>
                <option value="krishna">Krishna Mode</option>
              </select>
            </div>

            {/* Navigation Links */}
            <nav className="flex space-x-4">
              <Link
                to="/"
                className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Chat
              </Link>
              <Link
                to="/profile"
                className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
