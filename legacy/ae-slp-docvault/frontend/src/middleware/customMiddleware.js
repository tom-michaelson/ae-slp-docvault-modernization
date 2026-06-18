/**
 * Custom Redux Middleware (Constitution Principle V — Dead Abstractions)
 * 
 * A custom middleware layer that:
 * 1. Logs every action to the console
 * 2. Adds a timestamp to every action
 * 3. Tracks action counts
 * 
 * This runs on EVERY dispatched action, adding console noise
 * and unnecessary processing overhead.
 */

let actionCount = 0;

const customLogger = (store) => (next) => (action) => {
  actionCount++;
  
  // Log every action with its count
  console.log(
    `[DocVault Redux] Action #${actionCount}:`,
    action.type,
    '| State keys:',
    Object.keys(store.getState()).length
  );
  
  // Add timestamp to every action (mutating the action — bad practice)
  action._timestamp = Date.now();
  action._sequence = actionCount;
  
  const result = next(action);
  
  // Log state after action
  console.log(
    `[DocVault Redux] After #${actionCount}:`,
    action.type,
    '| New state preview:',
    Object.keys(store.getState()).reduce((acc, key) => {
      const val = store.getState()[key];
      acc[key] = typeof val === 'object' ? `{${Object.keys(val).length} keys}` : val;
      return acc;
    }, {})
  );
  
  return result;
};

/**
 * Error boundary middleware — catches errors in reducers
 * (another layer that adds complexity without clear value)
 */
const errorBoundary = (store) => (next) => (action) => {
  try {
    return next(action);
  } catch (err) {
    console.error('[DocVault Redux] Error in reducer for action:', action.type, err);
    // Swallow the error — bad practice, but "it works"
    return undefined;
  }
};

/**
 * Analytics middleware — tracks action frequency
 * (yet another middleware that was never connected to any analytics service)
 */
const analyticsTracker = (store) => (next) => (action) => {
  // TODO: send to analytics service
  // Analytics was supposed to be integrated with Mixpanel but 
  // the account was never set up
  if (typeof window !== 'undefined') {
    window.__docvault_action_log = window.__docvault_action_log || [];
    window.__docvault_action_log.push({
      type: action.type,
      timestamp: Date.now(),
    });
    // Keep only last 100 actions
    if (window.__docvault_action_log.length > 100) {
      window.__docvault_action_log = window.__docvault_action_log.slice(-100);
    }
  }
  return next(action);
};

export { customLogger, errorBoundary, analyticsTracker };
export default customLogger;
