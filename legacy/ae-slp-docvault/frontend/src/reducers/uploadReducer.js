// uploadReducer.js — 8 of 12 reducers (REDUNDANT)
// Duplicates upload status that is already managed in documentsReducer
// and in DocumentGrid.jsx's local state.
// Three places track uploads — this is one of them.

const initialState = {
  uploading: false,
  progress: 0,
  currentFile: null,
  error: null,
  recentUploads: [],
  queuedFiles: [],
};

const UPLOAD_START = 'UPLOAD_START';
const UPLOAD_PROGRESS = 'UPLOAD_PROGRESS';
const UPLOAD_SUCCESS = 'UPLOAD_SUCCESS';
const UPLOAD_FAILURE = 'UPLOAD_FAILURE';
const UPLOAD_RESET = 'UPLOAD_RESET';
const QUEUE_FILE = 'QUEUE_FILE';
const DEQUEUE_FILE = 'DEQUEUE_FILE';

function uploadReducer(state = initialState, action) {
  switch (action.type) {
    case UPLOAD_START:
      return {
        ...state,
        uploading: true,
        progress: 0,
        currentFile: action.payload,
        error: null,
      };
    case UPLOAD_PROGRESS:
      return { ...state, progress: action.payload };
    case UPLOAD_SUCCESS:
      return {
        ...state,
        uploading: false,
        progress: 100,
        currentFile: null,
        recentUploads: [action.payload, ...state.recentUploads].slice(0, 10),
      };
    case UPLOAD_FAILURE:
      return {
        ...state,
        uploading: false,
        error: action.payload,
        currentFile: null,
      };
    case UPLOAD_RESET:
      return { ...initialState };
    case QUEUE_FILE:
      return {
        ...state,
        queuedFiles: [...state.queuedFiles, action.payload],
      };
    case DEQUEUE_FILE:
      return {
        ...state,
        queuedFiles: state.queuedFiles.slice(1),
      };
    default:
      return state;
  }
}

export default uploadReducer;
