import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendMessage, sendConversation } from "../../api/chat";

// Send a message to the chatbot
export const sendChatMessage = createAsyncThunk(
  "chat/sendMessage",
  async ({ message, mode }, { rejectWithValue }) => {
    try {
      const response = await sendMessage(message, mode);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to send message"
      );
    }
  }
);

// Send conversation history for context-aware responses
export const sendChatConversation = createAsyncThunk(
  "chat/sendConversation",
  async ({ messages, mode }, { rejectWithValue }) => {
    try {
      const response = await sendConversation(messages, mode);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to send message"
      );
    }
  }
);

const initialState = {
  messages: [],
  loading: false,
  error: null,
  mode: "friendlymode", // Default mode
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    setMode: (state, action) => {
      state.mode = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Handle single message
      .addCase(sendChatMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.loading = false;
        // Add bot response to messages
        state.messages.push({
          role: "assistant",
          content: action.payload.response,
        });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Handle conversation history
      .addCase(sendChatConversation.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendChatConversation.fulfilled, (state, action) => {
        state.loading = false;
        // Add bot response to messages
        state.messages.push({
          role: "assistant",
          content: action.payload.response,
        });
      })
      .addCase(sendChatConversation.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setMode, clearMessages, addMessage, clearError } =
  chatSlice.actions;
export default chatSlice.reducer;
