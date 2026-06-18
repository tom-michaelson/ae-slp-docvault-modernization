# `awa-hitl`

A reusable Human-in-the-Loop (HITL) child workflow that enables human interaction within parent workflows.

This workflow provides blocking, non-blocking, and chat interaction patterns for collecting human input during workflow execution. It's designed to be invoked as a child workflow for any scenario requiring human decision-making or input.

## Parameters

| Name         | Type        | Description                                                                                                                    |
| :----------- | :---------- | :----------------------------------------------------------------------------------------------------------------------------- |
| `input_data` | `HITLInput` | Configuration for the HITL interaction including title, description, markdown content, interaction mode settings, and timeout. |

### HITLInput Fields

| Field             | Type          | Default | Description                                                 |
| :---------------- | :------------ | :------ | :---------------------------------------------------------- |
| `title`           | `str`         |         | Title displayed to the human user                           |
| `description`     | `str \| None` | `None`  | Optional description providing context                      |
| `markdown`        | `str \| None` | `None`  | Optional markdown content for rich formatting               |
| `non_blocking`    | `bool`        | `False` | If true, returns immediately without waiting for response   |
| `timeout_seconds` | `int \| None` | `None`  | Optional timeout in seconds for waiting for response        |
| `chat_mode`       | `bool`        | `False` | If true, enables chat interaction mode with message history |

## Returns

| Type         | Description                                                                                                      |
| :----------- | :--------------------------------------------------------------------------------------------------------------- |
| `HITLOutput` | Contains the human response, approval status, rejection reason (if applicable), and chat history (in chat mode). |

## Signals

| Name               | Parameters        | Description                                         |
| :----------------- | :---------------- | :-------------------------------------------------- |
| `submit_response`  | `HITLResponse`    | Submits a human response to the workflow            |
| `add_chat_message` | `HITLChatMessage` | Adds a message to the chat history (chat mode only) |

## Queries

| Name                    | Return Type             | Description                                      |
| :---------------------- | :---------------------- | :----------------------------------------------- |
| `get_context`           | `HITLContext`           | Returns the current HITL context                 |
| `has_response`          | `bool`                  | Checks if a response has been received           |
| `get_response`          | `HITLResponse \| None`  | Returns the submitted response if available      |
| `get_chat_history`      | `list[HITLChatMessage]` | Returns the chat history (chat mode only)        |
| `get_pending_messages`  | `list[HITLChatMessage]` | Returns messages pending Socket.IO emission      |
| `get_user_input_status` | `bool`                  | Returns whether new user input has been received |

## Usage

### Blocking Mode (Default)

```python
# Start HITL child workflow and wait for response
hitl_input = HITLInput(
    title="Approval Required",
    description="Please review and approve the changes",
    markdown="## Changes\n- Updated configuration\n- Added new feature",
    timeout_seconds=300  # 5 minute timeout
)

hitl_handle = await workflow.start_child_workflow(
    "awa-hitl",
    hitl_input
)

result = await hitl_handle.result()
if result.approved:
    print(f"Approved by {result.response.user_response}")
else:
    print(f"Rejected: {result.rejection_reason}")
```

### Non-Blocking Mode

```python
# Start HITL without waiting
hitl_input = HITLInput(
    title="Review Request",
    description="Please review when you have time",
    non_blocking=True
)

hitl_handle = await workflow.start_child_workflow(
    "awa-hitl",
    hitl_input
)

# Continue with other work...
# Later, check for response via query
has_response = await hitl_handle.query("has_response")
if has_response:
    response = await hitl_handle.query("get_response")
```

### Chat Mode

```python
# Enable interactive chat
hitl_input = HITLInput(
    title="Requirements Discussion",
    description="Let's discuss your requirements",
    chat_mode=True
)

hitl_handle = await workflow.start_child_workflow(
    "awa-hitl",
    hitl_input
)

# Add system messages
await hitl_handle.signal("add_chat_message", HITLChatMessage(
    type="system",
    content="What features would you like to implement?"
))

# Get chat history
chat_history = await hitl_handle.query("get_chat_history")
```

## Integration with Parent Workflows

The HITL child workflow is commonly used in:

- **Requirements Gathering**: Interactive conversations to clarify user needs
- **Approval Workflows**: Getting human approval for automated actions
- **Decision Points**: Allowing human intervention at critical workflow stages
- **Error Handling**: Human review when automated processing fails

## See Also

- [Requirements Gathering Workflow](./requirements-gathering.md) - Example of HITL in chat mode
