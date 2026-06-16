// authReducer.js — 5 of 12 reducers (REDUNDANT)
// This reducer duplicates user state that is already managed by userReducer.js
// It was created when the auth system was being added, but the developer
// didn't realize userReducer already handled the same state.

const initialState = {
  isAuthenticated: false,
  token: null,
  refreshToken: null,
  user: null,
  loginError: null,
  loginLoading: false,
};

const AUTH_LOGIN_START = 'AUTH_LOGIN_START';
const AUTH_LOGIN_SUCCESS = 'AUTH_LOGIN_SUCCESS';
const AUTH_LOGIN_FAILURE = 'AUTH_LOGIN_FAILURE';
const AUTH_LOGOUT = 'AUTH_LOGOUT';
const AUTH_SET_TOKEN = 'AUTH_SET_TOKEN';

function authReducer(state = initialState, action) {
  switch (action.type) {
    case AUTH_LOGIN_START:
      return { ...state, loginLoading: true, loginError: null };
    case AUTH_LOGIN_SUCCESS:
      return {
        ...state,
        isAuthenticated: true,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        user: action.payload.user,
        loginLoading: false,
        loginError: null,
      };
    case AUTH_LOGIN_FAILURE:
      return {
        ...state,
        isAuthenticated: false,
        loginLoading: false,
        loginError: action.payload,
      };
    case AUTH_LOGOUT:
      return { ...initialState };
    case AUTH_SET_TOKEN:
      return { ...state, token: action.payload };
    default:
      return state;
  }
}

export {
  AUTH_LOGIN_START,
  AUTH_LOGIN_SUCCESS,
  AUTH_LOGIN_FAILURE,
  AUTH_LOGOUT,
  AUTH_SET_TOKEN,
};
export default authReducer;
