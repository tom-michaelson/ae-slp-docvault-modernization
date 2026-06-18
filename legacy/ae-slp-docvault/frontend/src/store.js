/**
 * Redux Store Configuration (Constitution Principle II — State Overengineering)
 * 
 * This file is 200+ lines long.
 * It combines 12 reducers for only 4 real state domains.
 * The majority of lines are commented-out dead code from an abandoned refactor.
 * 
 * Active reducers (4):  userReducer, documentsReducer, filtersReducer, uiReducer
 * Redundant reducers (4): authReducer, uploadReducer, searchReducer
 * Unused reducers (5): notificationsReducer, settingsReducer, paginationReducer,
 *                       cacheReducer, metadataReducer
 */

import { createStore, combineReducers, applyMiddleware, compose } from 'redux';

// All 12 reducers — overkill for 4 state domains
import userReducer from './reducers/userReducer';
import documentsReducer from './reducers/documentsReducer';
import filtersReducer from './reducers/filtersReducer';
import uiReducer from './reducers/uiReducer';
import authReducer from './reducers/authReducer';           // redundant with userReducer
import notificationsReducer from './reducers/notificationsReducer'; // unused
import settingsReducer from './reducers/settingsReducer';   // unused
import uploadReducer from './reducers/uploadReducer';       // redundant with documentsReducer
import searchReducer from './reducers/searchReducer';       // redundant with filtersReducer
import paginationReducer from './reducers/paginationReducer'; // unused
import cacheReducer from './reducers/cacheReducer';         // unused
import metadataReducer from './reducers/metadataReducer';   // unused

// Custom middleware layers
import { customLogger, errorBoundary, analyticsTracker } from './middleware/customMiddleware';

// ActionCreatorFactory (imported but only partially used)
import ActionCreatorFactory from './ActionCreatorFactory';

// ============================================================
// ROOT REDUCER
// 12 reducers for 4 state domains — peak overengineering
// ============================================================
const rootReducer = combineReducers({
  user: userReducer,
  documents: documentsReducer,
  filters: filtersReducer,
  ui: uiReducer,
  auth: authReducer,               // redundant
  notifications: notificationsReducer, // unused
  settings: settingsReducer,        // unused
  upload: uploadReducer,            // redundant
  search: searchReducer,            // redundant
  pagination: paginationReducer,    // unused
  cache: cacheReducer,              // unused
  metadata: metadataReducer,        // unused
});

// ============================================================
// COMMENTED-OUT DEAD CODE FROM ABANDONED REFACTOR
// Someone tried to simplify the store but gave up halfway through
// ============================================================

// --- START ABANDONED REFACTOR ---
//
// const simplifiedReducer = combineReducers({
//   user: userReducer,
//   documents: documentsReducer,
//   filters: filtersReducer,
//   ui: uiReducer,
// });
//
// The plan was to merge authReducer into userReducer, but we weren't
// sure if anything depended on state.auth vs state.user.
//
// TODO: check which components read from state.auth
// TODO: check which components read from state.user
// TODO: merge them (sprint 14, maybe?)
//
// const mergedUserReducer = (state, action) => {
//   // Combined user + auth reducer
//   const userState = userReducer(state?.user, action);
//   const authState = authReducer(state?.auth, action);
//   return {
//     ...userState,
//     isAuthenticated: authState.isAuthenticated,
//     token: authState.token,
//   };
// };
//
// Similarly, uploadReducer should be merged into documentsReducer:
//
// const mergedDocumentsReducer = (state, action) => {
//   const docsState = documentsReducer(state?.documents, action);
//   const uploadState = uploadReducer(state?.upload, action);
//   return {
//     ...docsState,
//     uploadProgress: uploadState.progress,
//     uploading: uploadState.uploading,
//   };
// };
//
// And searchReducer should be merged into filtersReducer:
//
// const mergedFiltersReducer = (state, action) => {
//   const filterState = filtersReducer(state?.filters, action);
//   const searchState = searchReducer(state?.search, action);
//   return {
//     ...filterState,
//     searchResults: searchState.results,
//     searchLoading: searchState.loading,
//   };
// };
//
// We also talked about using Redux Toolkit (RTK) slices:
//
// import { configureStore, createSlice } from '@reduxjs/toolkit';
//
// const documentsSlice = createSlice({
//   name: 'documents',
//   initialState: { items: [], loading: false, error: null },
//   reducers: {
//     setDocuments: (state, action) => { state.items = action.payload; },
//     addDocument: (state, action) => { state.items.unshift(action.payload); },
//     setLoading: (state, action) => { state.loading = action.payload; },
//   },
// });
//
// const userSlice = createSlice({
//   name: 'user',
//   initialState: { current: null, isLoggedIn: false },
//   reducers: {
//     setUser: (state, action) => {
//       state.current = action.payload;
//       state.isLoggedIn = true;
//     },
//     clearUser: (state) => {
//       state.current = null;
//       state.isLoggedIn = false;
//     },
//   },
// });
//
// const filtersSlice = createSlice({
//   name: 'filters',
//   initialState: { searchQuery: '', fileType: '', sortBy: 'date' },
//   reducers: {
//     setSearchQuery: (state, action) => { state.searchQuery = action.payload; },
//     setFileType: (state, action) => { state.fileType = action.payload; },
//     setSortBy: (state, action) => { state.sortBy = action.payload; },
//     clearFilters: () => ({ searchQuery: '', fileType: '', sortBy: 'date' }),
//   },
// });
//
// const uiSlice = createSlice({
//   name: 'ui',
//   initialState: { sidebarOpen: true, modalOpen: false },
//   reducers: {
//     toggleSidebar: (state) => { state.sidebarOpen = !state.sidebarOpen; },
//     openModal: (state, action) => { 
//       state.modalOpen = true;
//       state.modalType = action.payload.type;
//     },
//     closeModal: (state) => { state.modalOpen = false; },
//   },
// });
//
// const simplifiedStore = configureStore({
//   reducer: {
//     documents: documentsSlice.reducer,
//     user: userSlice.reducer,
//     filters: filtersSlice.reducer,
//     ui: uiSlice.reducer,
//   },
// });
//
// But we decided against RTK because "we don't want to add another dependency"
// (even though Redux Toolkit is the official recommended way to use Redux)
//
// --- END ABANDONED REFACTOR ---

// ============================================================
// MIDDLEWARE CONFIGURATION
// Three custom middleware layers for a simple CRUD app
// ============================================================
const middlewares = [customLogger, errorBoundary, analyticsTracker];

// ============================================================
// DEV TOOLS CONFIGURATION
// ============================================================
const composeEnhancers =
  (typeof window !== 'undefined' && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) ||
  compose;

// ============================================================
// STORE CREATION
// ============================================================
const store = createStore(
  rootReducer,
  composeEnhancers(applyMiddleware(...middlewares))
);

// ============================================================
// MORE COMMENTED-OUT CODE
// Someone was experimenting with store subscriptions
// ============================================================

// store.subscribe(() => {
//   const state = store.getState();
//   console.log('[Store] State updated:', {
//     userLoggedIn: state.user.isLoggedIn,
//     documentCount: state.documents.items.length,
//     activeFilters: state.filters,
//     sidebarOpen: state.ui.sidebarOpen,
//   });
// });

// Hot module replacement for reducers (copy-pasted from a tutorial)
// if (module.hot) {
//   module.hot.accept('./reducers', () => {
//     store.replaceReducer(rootReducer);
//   });
// }

// Pre-configured action creators via factory
// (imported but mostly unused — components dispatch raw action objects instead)
const factory = new ActionCreatorFactory();
export const setDocuments = factory.create('SET_DOCUMENTS', 'payload');
export const setUser = factory.create('SET_USER', 'payload');
export const toggleSidebar = factory.create('TOGGLE_SIDEBAR');
export const setSearchQuery = factory.create('SET_SEARCH_QUERY', 'payload');

export default store;
