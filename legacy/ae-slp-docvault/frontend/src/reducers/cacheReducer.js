// cacheReducer.js — 11 of 12 reducers (UNUSED)
// Manages a cache layer that does not exist.
// Was intended to cache API responses to reduce server load,
// but the cache was never actually consulted by any component.

const initialState = {
  entries: {},
  maxAge: 300000, // 5 minutes in ms
  hits: 0,
  misses: 0,
};

const CACHE_SET = 'CACHE_SET';
const CACHE_INVALIDATE = 'CACHE_INVALIDATE';
const CACHE_CLEAR = 'CACHE_CLEAR';
const CACHE_HIT = 'CACHE_HIT';
const CACHE_MISS = 'CACHE_MISS';

function cacheReducer(state = initialState, action) {
  switch (action.type) {
    case CACHE_SET:
      return {
        ...state,
        entries: {
          ...state.entries,
          [action.payload.key]: {
            data: action.payload.data,
            timestamp: Date.now(),
          },
        },
      };
    case CACHE_INVALIDATE:
      const { [action.payload]: removed, ...remaining } = state.entries;
      return { ...state, entries: remaining };
    case CACHE_CLEAR:
      return { ...state, entries: {}, hits: 0, misses: 0 };
    case CACHE_HIT:
      return { ...state, hits: state.hits + 1 };
    case CACHE_MISS:
      return { ...state, misses: state.misses + 1 };
    default:
      return state;
  }
}

export default cacheReducer;
