# Continuous Integration

This project uses [Dagger](https://dagger.io/) and Bitbucket Pipelines to run CI.

Using Dagger means that we can run CI locally, and it will run the same tests and build steps as the CI pipeline.

## Prerequisites

The following prerequisites are required to run CI locally (above and beyond what is required to run AWA itself).

- [Dagger](https://docs.dagger.io/install)

## Run CI

Run the following command from the root of the repo:

```bash
make ci
```

OR

```bash
dagger run uv run pipelines/ci.py
```
