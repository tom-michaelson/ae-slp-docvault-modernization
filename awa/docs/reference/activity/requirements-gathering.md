# Requirements Gathering Activities

A collection of activities for gathering and analyzing requirements through interactive conversation and structured extraction.

## `generate_clarifying_questions`

Generate clarifying questions based on an initial feature description.

This activity analyzes an initial feature description and generates relevant clarifying questions to gather more comprehensive requirements from users.

### Parameters

| Name                   | Type  | Description                                                    |
| :--------------------- | :---- | :------------------------------------------------------------- |
| `initial_description`  | `str` | The initial feature or requirement description from the user. |

### Returns

| Type                   | Description                                                           |
| :--------------------- | :-------------------------------------------------------------------- |
| `ClarifyingQuestions`  | A structured set of clarifying questions to ask the user.            |

### Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk import constants

@workflow.defn
class RequirementsWorkflow:
    @workflow.run
    async def run(self, description: str):
        questions = await workflow.execute_activity(
            constants.ACTIVITY_GENERATE_CLARIFYING_QUESTIONS,
            args=[description],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
        return questions
```

```typescript [TypeScript]
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { generate_clarifying_questions } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 minute',
  taskQueue: 'awa_default'
});

export async function requirementsWorkflow(description: string) {
  const questions = await generate_clarifying_questions(description);
  return questions;
}
```

:::

## `generate_contextual_follow_up`

Generate contextual follow-up questions based on conversation history.

This activity analyzes the ongoing conversation context and generates appropriate follow-up questions to deepen understanding of requirements.

### Parameters

| Name       | Type   | Description                                                                                           |
| :--------- | :----- | :---------------------------------------------------------------------------------------------------- |
| `context`  | `dict` | A dictionary containing conversation context with keys: `original_request`, `conversation_history`, and `latest_user_response`. |

### Returns

| Type                   | Description                                                          |
| :--------------------- | :------------------------------------------------------------------- |
| `ClarifyingQuestions`  | A structured set of follow-up questions based on the conversation.  |

### Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk import constants

@workflow.defn
class RequirementsWorkflow:
    @workflow.run
    async def run(self, context: dict):
        follow_up = await workflow.execute_activity(
            constants.ACTIVITY_GENERATE_CONTEXTUAL_FOLLOW_UP,
            args=[context],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
        return follow_up
```

```typescript [TypeScript]
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { generate_contextual_follow_up } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 minute',
  taskQueue: 'awa_default'
});

export async function requirementsWorkflow(context: Record<string, any>) {
  const followUp = await generate_contextual_follow_up(context);
  return followUp;
}
```

:::

## `analyze_requirements`

Analyze chat conversation to extract structured requirements.

This activity processes the complete conversation text and extracts structured requirements, including functional requirements, technical details, and acceptance criteria.

### Parameters

| Name                 | Type  | Description                                               |
| :------------------- | :---- | :-------------------------------------------------------- |
| `conversation_text`  | `str` | The complete conversation text to analyze for requirements. |

### Returns

| Type                      | Description                                                    |
| :------------------------ | :------------------------------------------------------------- |
| `StructuredRequirements`  | A structured representation of the extracted requirements.     |

### Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk import constants

@workflow.defn
class RequirementsWorkflow:
    @workflow.run
    async def run(self, conversation: str):
        requirements = await workflow.execute_activity(
            constants.ACTIVITY_ANALYZE_REQUIREMENTS,
            args=[conversation],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=90)
        )
        return requirements
```

```typescript [TypeScript]
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { analyze_requirements } = proxyActivities<typeof activities>({
  startToCloseTimeout: '90 seconds',
  taskQueue: 'awa_default'
});

export async function requirementsWorkflow(conversation: string) {
  const requirements = await analyze_requirements(conversation);
  return requirements;
}
```

:::

## Related Models

These activities use the following data models:

- `ClarifyingQuestions`: Contains a list of questions to clarify requirements
- `StructuredRequirements`: Contains extracted functional requirements, technical specifications, and acceptance criteria

## Example Workflow

Here's an example of using these activities together in a requirements gathering workflow:

```python
from temporalio import workflow
from datetime import timedelta
from awa.sdk import constants

@workflow.defn
class CompleteRequirementsGatheringWorkflow:
    @workflow.run
    async def run(self, initial_description: str):
        # Generate initial questions
        questions = await workflow.execute_activity(
            constants.ACTIVITY_GENERATE_CLARIFYING_QUESTIONS,
            args=[initial_description],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )

        # Simulate conversation (in real workflow, this would involve user interaction)
        conversation_history = []

        # Generate follow-up questions based on responses
        context = {
            "original_request": initial_description,
            "conversation_history": conversation_history,
            "latest_user_response": "User's response here"
        }

        follow_up = await workflow.execute_activity(
            constants.ACTIVITY_GENERATE_CONTEXTUAL_FOLLOW_UP,
            args=[context],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )

        # Analyze complete conversation
        full_conversation = f"{initial_description}\n" + "\n".join(conversation_history)

        requirements = await workflow.execute_activity(
            constants.ACTIVITY_ANALYZE_REQUIREMENTS,
            args=[full_conversation],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=90)
        )

        return requirements
```
