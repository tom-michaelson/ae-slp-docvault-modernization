/**
 * ActionCreatorFactory (Constitution Principle V — Dead Abstractions)
 * 
 * A class that generates Redux action creators via method calls like:
 *   factory.create('SET_DOCUMENTS', 'documents')
 * 
 * This wraps a trivial pattern in unnecessary abstraction.
 * Instead of writing:
 *   const setDocuments = (docs) => ({ type: 'SET_DOCUMENTS', payload: docs })
 * 
 * You now have to write:
 *   const factory = new ActionCreatorFactory();
 *   const setDocuments = factory.create('SET_DOCUMENTS', 'documents');
 * 
 * This makes action creation harder to trace, harder to grep for,
 * and adds an indirection layer that provides zero value.
 */
class ActionCreatorFactory {
  constructor(prefix = '') {
    this.prefix = prefix;
    this.registry = {};
  }

  /**
   * Create an action creator for a given type.
   * @param {string} type - Action type constant
   * @param {string} payloadKey - Key name for the payload (defaults to 'payload')
   * @returns {Function} Action creator function
   */
  create(type, payloadKey = 'payload') {
    const fullType = this.prefix ? `${this.prefix}/${type}` : type;
    
    const actionCreator = (value) => ({
      type: fullType,
      [payloadKey]: value,
      _meta: {
        createdBy: 'ActionCreatorFactory',
        timestamp: Date.now(),
        payloadKey,
      },
    });

    // Store in registry for debugging
    this.registry[fullType] = {
      payloadKey,
      created: new Date().toISOString(),
    };

    return actionCreator;
  }

  /**
   * Create an action creator with multiple payload fields.
   * @param {string} type - Action type constant
   * @param {...string} keys - Payload field names
   * @returns {Function} Action creator function accepting an object
   */
  createMulti(type, ...keys) {
    const fullType = this.prefix ? `${this.prefix}/${type}` : type;

    const actionCreator = (values) => {
      const action = { type: fullType, _meta: { createdBy: 'ActionCreatorFactory' } };
      keys.forEach((key) => {
        if (values && values[key] !== undefined) {
          action[key] = values[key];
        }
      });
      return action;
    };

    this.registry[fullType] = { keys, created: new Date().toISOString() };
    return actionCreator;
  }

  /**
   * Get all registered action types.
   * @returns {Object} Registry of action types
   */
  getRegistry() {
    return { ...this.registry };
  }

  /**
   * Check if an action type is registered.
   * @param {string} type - Action type to check
   * @returns {boolean}
   */
  isRegistered(type) {
    const fullType = this.prefix ? `${this.prefix}/${type}` : type;
    return !!this.registry[fullType];
  }
}

// Pre-configured factory instances for different domains
// (more abstraction for the sake of abstraction)
export const documentActions = new ActionCreatorFactory('documents');
export const userActions = new ActionCreatorFactory('user');
export const uiActions = new ActionCreatorFactory('ui');
export const filterActions = new ActionCreatorFactory('filters');

export default ActionCreatorFactory;
