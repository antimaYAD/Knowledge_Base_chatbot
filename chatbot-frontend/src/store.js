import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./features/auth/authSlice";
import chatReducer from "./features/chat/chatSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // Allows for non-serializable values in the store
    }),
});

export default store;
