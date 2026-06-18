// userReducer.js — 1 of 12 reducers (ACTIVE)
// Manages current user state
// Note: authReducer.js is a redundant duplicate of this

const initialState = {
  currentUser: null,
  isLoggedIn: false,
  profile: null,
  preferences: {},
};

const SET_USER = 'SET_USER';
const CLEAR_USER = 'CLEAR_USER';
const UPDATE_PROFILE = 'UPDATE_PROFILE';
const SET_PREFERENCES = 'SET_PREFERENCES';

function userReducer(state = initialState, action) {
  switch (action.type) {
    case SET_USER:
      return {
        ...state,
        currentUser: action.payload,
        isLoggedIn: true,
      };
    case CLEAR_USER:
      return {
        ...initialState,
      };
    case UPDATE_PROFILE:
      return {
        ...state,
        profile: { ...state.profile, ...action.payload },
      };
    case SET_PREFERENCES:
      return {
        ...state,
        preferences: { ...state.preferences, ...action.payload },
      };
    default:
      return state;
  }
}

export { SET_USER, CLEAR_USER, UPDATE_PROFILE, SET_PREFERENCES };
export default userReducer;
