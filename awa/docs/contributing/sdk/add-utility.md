# Add Utility to SDK

Each reusable child workflow and activity must initially be manually added as a Python utility so that it is included in the SDK generation process.

## Adding a Utility

1. Create a constant value for your child workflow or activity in the `awa/sdk/constants.py` file.
2. Add any models that are used by your utility to the `awa/sdk/models/` folder.
3. Add a new utility function in a self-contained file (on function per file) to the `awa/sdk/utils/` folder in the appropriate subfolder (`workflow`, `activity`, or `general`).
4. Run the generation workflow and merge your PR to `main` to publish the new version of the SDK. See [SDK Generation](/contributing/sdk/generation.md) for more details.
