---
outline: 2
---

# Temporal Conventions

The conventions below should apply to all core shared activities and workflows.

## Use constant values for workflow and activity names

Prefer the use of constant values for workflow and activity names, rather than hardcoded strings or implicitly relying on the name of the Python class or function.

### Bad

:::code-group

```python [my_workflow.py]
@workflow.defn(name="my_workflow")
class MyWorkflow:
    @workflow.run
    async def run(self, workflow_input: MyWorkflowInput | None = None) -> str:
        # ...
```

```python [my_workflow2.py]
@workflow.defn # Implicitly named "MyWorkflow2"
class MyWorkflow2:
    @workflow.run
    async def run(self, workflow_input: MyWorkflowInput | None = None) -> str:
        # ...
```

:::

### Good

:::code-group

```python [Good]
@workflow.defn(name=constants.MY_WORKFLOW)
class MyWorkflow:
    @workflow.run
    async def run(self, workflow_input: MyWorkflowInput | None = None) -> str:
        # ...
```

:::

## Use input and output models, rather than parameter lists

Prefer the use of input and output Pydantic models, rather than raw lists of discrete parameters. This allows for easier extension down the road when additional optional parameters may be needed to support additional functionality. It also simplifies the caller structure via Temporal, as strict parameter ordering is not required.

### Bad

:::code-group

```python [my_workflow.py]
@workflow.defn(name=constants.MY_WORKFLOW)
class MyWorkflow:
    @workflow.run
    async def run(self, prop_a: str | None = None, prop_b: int | None = None) -> str:
        # ...
```

:::

### Good

:::code-group

```python [my_workflow.py]
@workflow.defn(name=constants.MY_WORKFLOW)
class MyWorkflow:
    @workflow.run
    async def run(self, workflow_input: MyWorkflowInput | None = None) -> MyWorkflowResult:
        # ...
```

```python [models/my_workflow_input.py]

# models/my_workflow_input.py
class MyWorkflowInput(BaseModel):
    prop_a: str | None = None
    prop_b: int | None = None
```

```python [models/my_workflow_result.py]
class MyWorkflowResult(BaseModel):
    the_value: str
```

:::
