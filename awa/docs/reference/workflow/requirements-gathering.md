# `awa-gather-requirements`

An interactive requirements gathering workflow that uses chat-based conversation to collect and structure project requirements.

This workflow demonstrates AWA's chat capabilities by engaging users in multi-turn conversations to clarify requirements, ask follow-up questions, and generate structured outputs from natural language discussions.

## Parameters

| Name         | Type                         | Description                                                                   |
| :----------- | :--------------------------- | :---------------------------------------------------------------------------- |
| `input_data` | `RequirementsGatheringInput` | Initial configuration including the feature description and timeout settings. |

### RequirementsGatheringInput Fields

| Field                 | Type          | Default | Description                                                 |
| :-------------------- | :------------ | :------ | :---------------------------------------------------------- |
| `initial_description` | `str`         |         | Initial feature or project description provided by the user |
| `timeout_seconds`     | `int \| None` | `None`  | Optional timeout for the entire conversation                |

## Returns

| Type                          | Description                                                                                                         |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| `RequirementsGatheringOutput` | Structured requirements including feature specifications, user stories, acceptance criteria, and technical details. |

### RequirementsGatheringOutput Fields

| Field                  | Type                     | Description                                             |
| :--------------------- | :----------------------- | :------------------------------------------------------ |
| `requirements`         | `StructuredRequirements` | Complete structured requirements document               |
| `conversation_summary` | `str`                    | Summary of the conversation and key decisions           |
| `confidence_score`     | `float`                  | Confidence level in the gathered requirements (0.0-1.0) |

## Activities Used

| Activity                        | Purpose                                                               |
| :------------------------------ | :-------------------------------------------------------------------- |
| `generate_clarifying_questions` | Creates initial clarifying questions based on the feature description |
| `generate_contextual_follow_up` | Generates follow-up questions based on conversation history           |
| `structure_requirements`        | Transforms conversation into structured requirements document         |
| `emit_hitl_chat_message`        | Sends chat messages to the user interface                             |

## Workflow Behavior

1. **Initialization**: Starts HITL child workflow in chat mode with initial description
2. **Question Generation**: Uses LLM to generate clarifying questions about the feature
3. **Interactive Conversation**:
   - Presents questions to the user
   - Collects responses
   - Generates contextual follow-up questions
   - Continues for up to 5 rounds or until sufficient information is gathered
4. **Requirements Structuring**: Transforms the conversation into structured requirements
5. **Output Generation**: Returns formatted requirements with confidence scoring

## Usage

### Basic Requirements Gathering

```python
from awa.core.models.requirements import RequirementsGatheringInput

# Start requirements gathering
input_data = RequirementsGatheringInput(
    initial_description="I need a user authentication system with OAuth support",
    timeout_seconds=600  # 10 minute timeout
)

handle = await workflow.start_child_workflow(
    "awa-gather-requirements",
    input_data
)

result = await handle.result()
print(f"Confidence: {result.confidence_score}")
print(f"Requirements: {result.requirements}")
print(f"Summary: {result.conversation_summary}")
```

### With Parent Workflow Integration

```python
# In a parent workflow
async def design_system_workflow(description: str):
    # First, gather detailed requirements
    requirements_result = await workflow.execute_child_workflow(
        "awa-gather-requirements",
        RequirementsGatheringInput(
            initial_description=description,
            timeout_seconds=900
        )
    )

    # Use structured requirements for next steps
    if requirements_result.confidence_score > 0.8:
        # Proceed with high-confidence requirements
        await create_technical_design(requirements_result.requirements)
    else:
        # Request human review for low-confidence requirements
        await request_requirements_review(requirements_result)
```

## Structured Requirements Output

The workflow produces a `StructuredRequirements` object containing:

- **Feature Overview**: High-level description and objectives
- **User Stories**: Formatted user stories with acceptance criteria
- **Functional Requirements**: Detailed functional specifications
- **Non-Functional Requirements**: Performance, security, and other constraints
- **Technical Specifications**: Implementation details and technology choices
- **Acceptance Criteria**: Measurable success criteria
- **Out of Scope**: Explicitly excluded items
- **Dependencies**: External requirements and integrations
- **Priority**: Feature prioritization (High/Medium/Low)
- **Estimated Complexity**: Development effort estimation

## Conversation Flow Example

1. **User**: "I need a notification system"
2. **System**: "What types of notifications do you need to support? (email, SMS, push, in-app)"
3. **User**: "Email and in-app notifications"
4. **System**: "What events should trigger notifications?"
5. **User**: "User mentions, task assignments, and deadline reminders"
6. **System**: "Should users be able to customize their notification preferences?"
7. **User**: "Yes, they should control frequency and channel per notification type"
8. **System**: _(Generates structured requirements based on conversation)_

## Best Practices

- Provide detailed initial descriptions for better question generation
- Set appropriate timeouts based on complexity
- Review confidence scores to determine if additional clarification is needed
- Use the conversation summary for audit trails and documentation

## See Also

- [HITL Child Workflow](./hitl-child.md) - Core human interaction workflow
