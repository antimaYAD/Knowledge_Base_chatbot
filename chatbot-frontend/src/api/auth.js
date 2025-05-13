import api from "./index";

// Register a new user
export const registerUser = async (userData) => {
  const response = await api.post("/api/v1/auth/register", userData);
  return response.data;
};

// Login user and get token
export const loginUser = async (username, password) => {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/api/v1/token", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
};

// Update user profile
export const updateProfile = async (userData) => {
  const response = await api.put("/api/v1/auth/update-profile", userData);
  return response.data;
};
