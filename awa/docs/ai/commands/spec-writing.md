# Specification Writing Guide

## Configuration

```yaml
cursor:
  description: "JIRA ticket specification writing and development planning"
  globs:
  include_in_index: true

copilot:
  output_type: "prompts"
  description: "Specification writing for JIRA tickets and development planning"
  include_in_index: true

claude:
  command_name: "spec-writing"
  description: "JIRA ticket specification writing and development planning guide"
  include_in_index: true

opencode:
  command_name: "spec-writing"
  description: "JIRA ticket specification writing and development planning guide"
  include_in_index: true
```

Your job is to write a specification for development of a new feature or bug fix.

You will be given a JIRA ticket with details in it. IMPORTANT: If you are not given a JIRA ticket, you should ask me for one before proceeding.

You are to:

1. Analyze the JIRA story. Read it thoroughly.
2. Create a high-level summary for your plan of attack for implementing the feature or bug fix. Put this plan in planning/spec-&lt;jira ticket number&gt;.md.
3. Iteratively refine the plan to create detailed implementation steps. Ensure you consider testing and documentation updates as well.
4. Ask me for feedback on your plan, and iterate as needed.
