export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthLoading = (state) => state.auth.loading;
export const selectAuthError = (state) => state.auth.error;
export const selectRegistrationSuccess = (state) =>
  state.auth.registrationSuccess;
export const selectUpdateSuccess = (state) => state.auth.updateSuccess;
