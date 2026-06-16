# Tutorial - AWA 101

These workflows demonstrate the core capabilities of AWA in small, easy to understand flows. These are designed to take you from zero to hero in a short amount of time. Starting with 102, these also demonstrate the use of the official [AWA SDK](/usage/sdk/).

:::warning TaskStream 101

<!--@include: /../../.shared/taskstream-101-intro.md -->

:::

## Prerequisites

Before starting down this path, be sure to read the following resources to get a high-level overview of AWA itself.

- [Introduction](/introduction/)
- [Quick Start](/introduction/quick-start)

:::info Cookbook Location
The code for this tutorial series is located in the `cookbook/recipes/workflows/awa_101/` directory in this repository. The cookbook also contains starter client projects for different development languages (e.g. C#) in the `cookbook/client-workers/` directory.
:::

## Tutorials

The following tutorials build on each other to build a "Hello World" code modernization workflow. They intentionally utilize more and more AWA features to introduce you to how they fit together. However, it should be noted that this is a simple workflow. A true code modernization workflow would be much more complex.

- [AWA-101: Simple Direct Transform](/cookbook/tutorials/awa-101/awa-101-simple-direct-transform)
- [AWA-102: Advanced Direct Transform](/cookbook/tutorials/awa-101/awa-102-advanced-direct-transform)
- [AWA-103: Transform Chain](/cookbook/tutorials/awa-101/awa-103-transform-chain)
- [AWA-104: Transform Files in a Directory](/cookbook/tutorials/awa-101/awa-104-transform-directory)

After completing these tutorials, you can move on to more advanced topics in [AWA 201](/cookbook/tutorials/awa-201/).

## Running

<!--@include: /../../../.shared/running-recipes.md -->

## Path Conventions

AWA does not dictate how code files, inputs or outputs should be organized. By convention, all our guides and tutorials will use the following directory structure:

```bash
recipes/
└── activities/ # Shared cross-project activities
    └── {activity_name}_activity.py # Activity class
└── models/ # Shared cross-project models
└── utils/ # Common utility functions
└── workflows/ # Workflows
    └── {project_name}/ # Arbitrary grouping of workflows
        ├── activities/ # Shared project-level activities
            └── {activity_name}_activity.py # Activity class
        ├── baml_src/ # Shared project-level BAML files
        ├── input/ # Input files
        ├── output/
            └── {workflow_name}/
                └── {workflow_id (timestamp)}/ # Output files organized by workflow run
        └── {workflow_name}_workflow.py # Workflow class
```
