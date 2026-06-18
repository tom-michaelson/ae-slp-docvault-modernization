// documentsReducer.js — 2 of 12 reducers (ACTIVE)
// Manages document list state
// Note: uploadReducer.js redundantly duplicates upload status

const initialState = {
  items: [],
  loading: false,
  error: null,
  selectedId: null,
  lastFetched: null,
};

const SET_DOCUMENTS = 'SET_DOCUMENTS';
const ADD_DOCUMENT = 'ADD_DOCUMENT';
const REMOVE_DOCUMENT = 'REMOVE_DOCUMENT';
const UPDATE_DOCUMENT = 'UPDATE_DOCUMENT';
const SET_DOCUMENTS_LOADING = 'SET_DOCUMENTS_LOADING';
const SET_DOCUMENTS_ERROR = 'SET_DOCUMENTS_ERROR';
const SELECT_DOCUMENT = 'SELECT_DOCUMENT';

function documentsReducer(state = initialState, action) {
  switch (action.type) {
    case SET_DOCUMENTS:
      return {
        ...state,
        items: action.payload,
        loading: false,
        error: null,
        lastFetched: new Date().toISOString(),
      };
    case ADD_DOCUMENT:
      return {
        ...state,
        items: [action.payload, ...state.items],
      };
    case REMOVE_DOCUMENT:
      return {
        ...state,
        items: state.items.filter((d) => d.id !== action.payload),
      };
    case UPDATE_DOCUMENT:
      return {
        ...state,
        items: state.items.map((d) =>
          d.id === action.payload.id ? { ...d, ...action.payload } : d
        ),
      };
    case SET_DOCUMENTS_LOADING:
      return {
        ...state,
        loading: action.payload,
      };
    case SET_DOCUMENTS_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case SELECT_DOCUMENT:
      return {
        ...state,
        selectedId: action.payload,
      };
    default:
      return state;
  }
}

export {
  SET_DOCUMENTS,
  ADD_DOCUMENT,
  REMOVE_DOCUMENT,
  UPDATE_DOCUMENT,
  SET_DOCUMENTS_LOADING,
  SET_DOCUMENTS_ERROR,
  SELECT_DOCUMENT,
};
export default documentsReducer;
