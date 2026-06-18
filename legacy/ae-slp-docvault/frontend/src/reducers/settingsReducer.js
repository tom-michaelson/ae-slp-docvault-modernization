// settingsReducer.js — 7 of 12 reducers (UNUSED)
// This reducer manages settings for a settings page that does not exist.
// No component reads from or writes to this state.

const initialState = {
  general: {
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
  },
  display: {
    theme: 'light',
    density: 'comfortable',
    showThumbnails: true,
  },
  upload: {
    maxFileSize: 10485760, // 10MB
    allowedTypes: ['application/pdf', 'image/jpeg', 'image/png'],
    autoTag: false,
  },
  notifications: {
    email: false,
    browser: false,
    uploadComplete: true,
    shareNotification: true,
  },
};

const UPDATE_GENERAL_SETTINGS = 'UPDATE_GENERAL_SETTINGS';
const UPDATE_DISPLAY_SETTINGS = 'UPDATE_DISPLAY_SETTINGS';
const UPDATE_UPLOAD_SETTINGS = 'UPDATE_UPLOAD_SETTINGS';
const UPDATE_NOTIFICATION_SETTINGS_V2 = 'UPDATE_NOTIFICATION_SETTINGS_V2';
const RESET_SETTINGS = 'RESET_SETTINGS';

function settingsReducer(state = initialState, action) {
  switch (action.type) {
    case UPDATE_GENERAL_SETTINGS:
      return { ...state, general: { ...state.general, ...action.payload } };
    case UPDATE_DISPLAY_SETTINGS:
      return { ...state, display: { ...state.display, ...action.payload } };
    case UPDATE_UPLOAD_SETTINGS:
      return { ...state, upload: { ...state.upload, ...action.payload } };
    case UPDATE_NOTIFICATION_SETTINGS_V2:
      return {
        ...state,
        notifications: { ...state.notifications, ...action.payload },
      };
    case RESET_SETTINGS:
      return { ...initialState };
    default:
      return state;
  }
}

export default settingsReducer;
