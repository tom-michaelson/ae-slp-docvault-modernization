# TODO: Connect Analytics Middleware to Service

## Description

The `analyticsTracker` Redux middleware writes every dispatched action to `window.__docvault_action_log` (capped at 100 entries) but never sends this data to any analytics service. A comment indicates Mixpanel was the intended target, but the account was never set up.

## Original Comment

```
// TODO: send to analytics service
// Analytics was supposed to be integrated with Mixpanel but 
// the account was never set up
```

## Location

- **File**: `frontend/src/middleware/customMiddleware.js`
- **Line**: 66

## Priority

Low

## Estimated Effort

Medium (1–4 hours)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The middleware adds processing overhead on every Redux dispatch. If no analytics integration is planned, the `analyticsTracker` middleware should be removed rather than left running silently.
- `window.__docvault_action_log` is a global that can be inspected in browser devtools — this is not a security vulnerability but it does expose internal action type names to anyone who opens the console.
