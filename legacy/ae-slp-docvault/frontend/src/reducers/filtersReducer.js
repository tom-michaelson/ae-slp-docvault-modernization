// filtersReducer.js — 3 of 12 reducers (ACTIVE)
// Manages search/filter state
// Note: searchReducer.js redundantly duplicates search state

const initialState = {
  searchQuery: '',
  fileType: '',
  sortBy: 'date',
  dateRange: null,
  tags: [],
};

const SET_SEARCH_QUERY = 'SET_SEARCH_QUERY';
const SET_FILE_TYPE_FILTER = 'SET_FILE_TYPE_FILTER';
const SET_SORT_BY = 'SET_SORT_BY';
const SET_DATE_RANGE = 'SET_DATE_RANGE';
const SET_TAG_FILTER = 'SET_TAG_FILTER';
const CLEAR_FILTERS = 'CLEAR_FILTERS';

function filtersReducer(state = initialState, action) {
  switch (action.type) {
    case SET_SEARCH_QUERY:
      return { ...state, searchQuery: action.payload };
    case SET_FILE_TYPE_FILTER:
      return { ...state, fileType: action.payload };
    case SET_SORT_BY:
      return { ...state, sortBy: action.payload };
    case SET_DATE_RANGE:
      return { ...state, dateRange: action.payload };
    case SET_TAG_FILTER:
      return { ...state, tags: action.payload };
    case CLEAR_FILTERS:
      return { ...initialState };
    default:
      return state;
  }
}

export {
  SET_SEARCH_QUERY,
  SET_FILE_TYPE_FILTER,
  SET_SORT_BY,
  SET_DATE_RANGE,
  SET_TAG_FILTER,
  CLEAR_FILTERS,
};
export default filtersReducer;
