const TOKEN_KEY = "chatbot_auth_token";

// Save token to localStorage
export const saveToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// Get token from localStorage
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

// Remove token from localStorage
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

// Check if token exists
export const hasToken = () => {
  return !!getToken();
};
