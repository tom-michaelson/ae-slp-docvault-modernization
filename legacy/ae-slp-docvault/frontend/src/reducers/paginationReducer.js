// paginationReducer.js — 10 of 12 reducers (UNUSED)
// Manages pagination state for a pagination feature that does not exist.
// DocumentGrid loads all documents at once — no pagination was ever implemented.

const initialState = {
  currentPage: 1,
  pageSize: 20,
  totalItems: 0,
  totalPages: 0,
};

const SET_PAGE = 'SET_PAGE';
const SET_PAGE_SIZE = 'SET_PAGE_SIZE';
const SET_TOTAL_ITEMS = 'SET_TOTAL_ITEMS';
const RESET_PAGINATION = 'RESET_PAGINATION';

function paginationReducer(state = initialState, action) {
  switch (action.type) {
    case SET_PAGE:
      return { ...state, currentPage: action.payload };
    case SET_PAGE_SIZE:
      return {
        ...state,
        pageSize: action.payload,
        currentPage: 1,
        totalPages: Math.ceil(state.totalItems / action.payload),
      };
    case SET_TOTAL_ITEMS:
      return {
        ...state,
        totalItems: action.payload,
        totalPages: Math.ceil(action.payload / state.pageSize),
      };
    case RESET_PAGINATION:
      return { ...initialState };
    default:
      return state;
  }
}

export default paginationReducer;
