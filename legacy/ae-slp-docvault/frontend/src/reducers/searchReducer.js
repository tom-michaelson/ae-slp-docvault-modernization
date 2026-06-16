// searchReducer.js — 9 of 12 reducers (REDUNDANT)
// Duplicates search state that is already managed in filtersReducer
// and in DocumentGrid.jsx's local state.
// Three places track search state — this is one of them.

const initialState = {
  query: '',
  results: [],
  loading: false,
  error: null,
  totalResults: 0,
  lastSearchTime: null,
  searchHistory: [],
  suggestions: [],
};

const SEARCH_START = 'SEARCH_START';
const SEARCH_SUCCESS = 'SEARCH_SUCCESS';
const SEARCH_FAILURE = 'SEARCH_FAILURE';
const SEARCH_CLEAR = 'SEARCH_CLEAR';
const SEARCH_SET_QUERY = 'SEARCH_SET_QUERY';
const SEARCH_ADD_HISTORY = 'SEARCH_ADD_HISTORY';
const SEARCH_SET_SUGGESTIONS = 'SEARCH_SET_SUGGESTIONS';

function searchReducer(state = initialState, action) {
  switch (action.type) {
    case SEARCH_START:
      return { ...state, loading: true, error: null };
    case SEARCH_SUCCESS:
      return {
        ...state,
        results: action.payload.results,
        totalResults: action.payload.total,
        loading: false,
        lastSearchTime: new Date().toISOString(),
      };
    case SEARCH_FAILURE:
      return { ...state, loading: false, error: action.payload };
    case SEARCH_CLEAR:
      return { ...initialState };
    case SEARCH_SET_QUERY:
      return { ...state, query: action.payload };
    case SEARCH_ADD_HISTORY:
      return {
        ...state,
        searchHistory: [action.payload, ...state.searchHistory].slice(0, 20),
      };
    case SEARCH_SET_SUGGESTIONS:
      return { ...state, suggestions: action.payload };
    default:
      return state;
  }
}

export default searchReducer;
