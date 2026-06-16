// uiReducer.js — 4 of 12 reducers (ACTIVE)
// Manages sidebar open/close and modal state

const initialState = {
  sidebarOpen: true,
  modalOpen: false,
  modalType: null,
  modalData: null,
  viewMode: 'grid',
  theme: 'light',
  notifications: [],
};

const TOGGLE_SIDEBAR = 'TOGGLE_SIDEBAR';
const OPEN_MODAL = 'OPEN_MODAL';
const CLOSE_MODAL = 'CLOSE_MODAL';
const SET_VIEW_MODE = 'SET_VIEW_MODE';
const SET_THEME = 'SET_THEME';
const ADD_NOTIFICATION = 'ADD_NOTIFICATION';
const DISMISS_NOTIFICATION = 'DISMISS_NOTIFICATION';

function uiReducer(state = initialState, action) {
  switch (action.type) {
    case TOGGLE_SIDEBAR:
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case OPEN_MODAL:
      return {
        ...state,
        modalOpen: true,
        modalType: action.payload.type,
        modalData: action.payload.data,
      };
    case CLOSE_MODAL:
      return {
        ...state,
        modalOpen: false,
        modalType: null,
        modalData: null,
      };
    case SET_VIEW_MODE:
      return { ...state, viewMode: action.payload };
    case SET_THEME:
      return { ...state, theme: action.payload };
    case ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };
    case DISMISS_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter((n) => n.id !== action.payload),
      };
    default:
      return state;
  }
}

export {
  TOGGLE_SIDEBAR,
  OPEN_MODAL,
  CLOSE_MODAL,
  SET_VIEW_MODE,
  SET_THEME,
  ADD_NOTIFICATION,
  DISMISS_NOTIFICATION,
};
export default uiReducer;
