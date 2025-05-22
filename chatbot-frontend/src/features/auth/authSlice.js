import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { loginUser, registerUser, updateProfile } from "../../api/auth";
import { saveToken, getToken, removeToken, hasToken } from "../../utils/token";

// Check if user is already authenticated
export const checkAuth = createAsyncThunk(
  "auth/checkAuth",
  async (_, { rejectWithValue }) => {
    if (!hasToken()) {
      return rejectWithValue("No token found");
    }
    return { isAuthenticated: true };
  }
);

// Login action
export const login = createAsyncThunk(
  "auth/login",
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const response = await loginUser(username, password);
      saveToken(response.access_token);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || "Failed to login");
    }
  }
);

// Register action
export const register = createAsyncThunk(
  "auth/register",
  async (userData, { rejectWithValue }) => {
    try {
      const response = await registerUser(userData);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Registration failed"
      );
    }
  }
);

// Update profile action
export const update = createAsyncThunk(
  "auth/update",
  async (profileData, { rejectWithValue }) => {
    try {
      const response = await updateProfile(profileData);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Profile update failed"
      );
    }
  }
);

// Logout action
export const logout = createAsyncThunk("auth/logout", async () => {
  removeToken();
  return { success: true };
});

const initialState = {
  isAuthenticated: false,
  user: null,
  token: getToken() || null,
  loading: false,
  error: null,
  registrationSuccess: false,
  updateSuccess: false,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSuccessFlags: (state) => {
      state.registrationSuccess = false;
      state.updateSuccess = false;
    },
  },
  extraReducers: (builder) => {
    builder
      // Check auth
      .addCase(checkAuth.fulfilled, (state) => {
        state.isAuthenticated = true;
      })
      .addCase(checkAuth.rejected, (state) => {
        state.isAuthenticated = false;
        state.token = null;
      })

      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.access_token;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
        state.registrationSuccess = true;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Update profile
      .addCase(update.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(update.fulfilled, (state) => {
        state.loading = false;
        state.updateSuccess = true;
        state.error = null;
      })
      .addCase(update.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
      });
  },
});

export const { clearError, clearSuccessFlags } = authSlice.actions;
export default authSlice.reducer;
