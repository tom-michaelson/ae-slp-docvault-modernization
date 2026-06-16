:::warning Transform Activity vs. Transform Workflow
AWA has both a ["Transform" activity](/reference/activity/transform) and a ["Transform" workflow](/reference/workflow/transform). Which one should I use, and why?

**Short Answer**: You should always use the "Transform" workflow.

**Longer Answer**

The workflow wraps the activity, which allows us to provide more default functionality around the core BAML call (like response streaming, specialized retries, etc.).

From the perspective of the calling workflow, there is no functional difference between using the activity or the workflow &mdash; both can be awaited, and return the same structured result based on the BAML function definition.

The only difference is in Temporal semantics, a child workflow does not count towards the parent workflow's history limit, which is a slight advantage.
:::
