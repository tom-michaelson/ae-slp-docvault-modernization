// notificationsReducer.js — 6 of 12 reducers (UNUSED)
// This reducer manages a notification system that does not exist.
// No component dispatches to this reducer or reads from its state.
// It was created during a sprint planning session but the feature was never built.

const initialState = {
  items: [],
  unreadCount: 0,
  settings: {
    sound: true,
    desktop: false,
    email: false,
  },
};

const ADD_NOTIFICATION_ITEM = 'ADD_NOTIFICATION_ITEM';
const MARK_NOTIFICATION_READ = 'MARK_NOTIFICATION_READ';
const MARK_ALL_NOTIFICATIONS_READ = 'MARK_ALL_NOTIFICATIONS_READ';
const REMOVE_NOTIFICATION_ITEM = 'REMOVE_NOTIFICATION_ITEM';
const UPDATE_NOTIFICATION_SETTINGS = 'UPDATE_NOTIFICATION_SETTINGS';

function notificationsReducer(state = initialState, action) {
  switch (action.type) {
    case ADD_NOTIFICATION_ITEM:
      return {
        ...state,
        items: [action.payload, ...state.items],
        unreadCount: state.unreadCount + 1,
      };
    case MARK_NOTIFICATION_READ:
      return {
        ...state,
        items: state.items.map((n) =>
          n.id === action.payload ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      };
    case MARK_ALL_NOTIFICATIONS_READ:
      return {
        ...state,
        items: state.items.map((n) => ({ ...n, read: true })),
        unreadCount: 0,
      };
    case REMOVE_NOTIFICATION_ITEM:
      return {
        ...state,
        items: state.items.filter((n) => n.id !== action.payload),
      };
    case UPDATE_NOTIFICATION_SETTINGS:
      return {
        ...state,
        settings: { ...state.settings, ...action.payload },
      };
    default:
      return state;
  }
}

export default notificationsReducer;
