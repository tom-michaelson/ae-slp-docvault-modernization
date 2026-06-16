// metadataReducer.js — 12 of 12 reducers (UNUSED)
// Manages document metadata that does not exist as a separate concept.
// Was intended for a "metadata editor" feature that was never built.
// Document metadata (name, type, tags) is already in documentsReducer.

const initialState = {
  schemas: {},
  customFields: [],
  categories: [],
  defaultMetadata: {},
};

const SET_METADATA_SCHEMA = 'SET_METADATA_SCHEMA';
const ADD_CUSTOM_FIELD = 'ADD_CUSTOM_FIELD';
const REMOVE_CUSTOM_FIELD = 'REMOVE_CUSTOM_FIELD';
const SET_CATEGORIES = 'SET_CATEGORIES';
const SET_DEFAULT_METADATA = 'SET_DEFAULT_METADATA';
const RESET_METADATA = 'RESET_METADATA';

function metadataReducer(state = initialState, action) {
  switch (action.type) {
    case SET_METADATA_SCHEMA:
      return {
        ...state,
        schemas: { ...state.schemas, [action.payload.type]: action.payload.schema },
      };
    case ADD_CUSTOM_FIELD:
      return {
        ...state,
        customFields: [...state.customFields, action.payload],
      };
    case REMOVE_CUSTOM_FIELD:
      return {
        ...state,
        customFields: state.customFields.filter((f) => f.id !== action.payload),
      };
    case SET_CATEGORIES:
      return { ...state, categories: action.payload };
    case SET_DEFAULT_METADATA:
      return { ...state, defaultMetadata: action.payload };
    case RESET_METADATA:
      return { ...initialState };
    default:
      return state;
  }
}

export default metadataReducer;
