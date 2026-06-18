# Documentation

This page contains information about how to contribute to the documentation.

## Editing

Run `make docs` in the root of this repo (agentic-workflow-accelerator) to launch the docs site locally. This will launch in dev mode, and will automatically hot-reload as you make changes.

:::warning Use `make docs`
Do not attempt to run `pnpm run docs` or similar commands directly. There are a few helper scripts that are part of `make docs` that must be run for the full docs site to be built. If for any reason `make` doesn't work for you, you should manually execute the commands defined in the `Makefile`.

:::code-group
<<< ./../../Makefile#make-docs{make}
:::

## Audience

AWA docs should be written with the following audiences in mind: Slalom engineers and architects who are familiar with programming in general, but new to agentic engineering and AWA.

## Tech Stack

AWA docs are built using [Vitepress](https://vitepress.dev/), a static site generator.

## Organization

AWA docs are located in the `docs/` directory. The primary Vitepress configuration is located in `docs/.vitepress/config.mts`.

- `docs/configuration`- Guides to configuring AWA and related components.
- `docs/contributing`- Guides to contributing to AWA.
- `docs/cookbook`- Recipes for common use cases, demos, and examples. These docs can be edited directly in this repository.
- `docs/deployment`- Guides to deploying AWA in local and client environments.
- `docs/development`- Guides to developing with AWA.
- `docs/guides`- Guides and tutorials for using AWA effectively.
- `docs/installation`- Guides to installing AWA.
- `docs/introduction`- Introduction to AWA.
- `docs/public`- Public files like images. Used by Vitepress.
- `docs/reference` - Reference documentation for all AWA components and interfaces.
- `docs/usage` - Guides to using AWA effectively.
- `docs/index.md` - Home page.

### Reference vs. Guides

Reference docs should be comprehensive and detailed inventories of all AWA components and interfaces. Other "guide" sections (Configuration, Development, Usage, Deployment, Guides) should not duplicate this reference-level material. They should instead contain higher-level guides for using sets of features and concepts. They should link to the reference docs when appropriate.

## Cookbook

The cookbook documentation is located in `docs/cookbook/` and can be edited directly in this repository. The cookbook includes:

- Tutorials (AWA 101, AWA 201, etc.)
- Recipes and examples
- Starter projects for different languages

### Editing Cookbook Content

To edit cookbook content:

1. **Navigate to the appropriate directory**:
   - Documentation: `docs/cookbook/`
   - Source code: `cookbook/` (at repository root)

2. **Make your changes** to the relevant markdown or code files

3. **Test your changes** by running `make docs` in the root of this repository:

   ```bash
   make docs
   ```

4. **Submit your changes** via pull request

### Cookbook Source Code

The cookbook source code (Python workflows, BAML files, etc.) is located in the `cookbook/` directory at the root of this repository:

```
cookbook/
├── client-workers/       # Starter projects for different languages
│   ├── dotnet/
│   └── java/
└── recipes/              # Recipe source code
    ├── models/
    ├── utilities/
    └── workflows/
```

### Testing Cookbook Changes

When making changes to cookbook code or documentation:

1. **Code changes**: Test by enabling recipes in `config.yaml` (`recipes: true`) and running the affected workflows
2. **Documentation changes**: Run `make docs` and verify the changes render correctly
3. **Both**: Ensure code examples in documentation match the actual implementation

### Linking to Cookbook Code

When referencing cookbook code in documentation, use relative paths from the repository root:

```markdown
See the implementation at `cookbook/recipes/workflows/awa_101/awa101_simple_direct_transform_workflow.py`
```

## TypeScript API Model Generation

The project uses an automated script to generate TypeScript types for API request/response models from Pydantic models defined in the backend. This ensures the UI always has up-to-date type definitions matching the backend API models.

### How it Works

- The script (`scripts/generate_typescript_models.py`) scans specified Python modules (initially `awa/core/models/api.py`) for Pydantic models.
- For each model, it generates a JSON Schema using `.model_json_schema()`.
- It then uses the `json-schema-to-typescript` npm package to convert each schema to a TypeScript type.
- All generated types are written to `ui/src/types/api_models.ts`.

### When the Script Runs

- **Pre-commit:** A pre-commit hook runs the script and checks for changes in the generated file. If the file changes, you must add it to your commit.
- **Manual:** Run `make generate-typescript-models` to manually regenerate types when needed.

### Adding New Model Sources

- To generate types from additional Pydantic model files, add the module path to the `MODEL_SOURCES` list in `generate_typescript_models.py`.
- Example: `MODEL_SOURCES = ["awa.core.models.api", "awa.core.models.other"]`

### Dependencies & Setup

- The script requires `json-schema-to-typescript` as a dev dependency in the UI package. Install it with:
  ```sh
  pnpm add -D json-schema-to-typescript
  ```
- The script is run using the project’s Python environment and expects all dependencies to be installed (use `make install`).

### Troubleshooting

- If you see errors about missing TypeScript types, run `make generate-typescript-models` manually (which calls `generate_typescript_models.py`).
- If you add or change Pydantic models, always check that `ui/src/types/api_models.ts` is updated and committed.

## API Reference Documentation Generation

AWA automatically generates comprehensive API reference documentation from the FastAPI OpenAPI specification. This ensures the documentation is always up-to-date with the actual API implementation.

### How it Works

- The script (`scripts/generate_api_reference_docs.py`) creates a FastAPI app instance and extracts the OpenAPI specification.
- It parses the OpenAPI spec to extract endpoint information, including parameters, request bodies, responses, and data models.
- The script generates markdown documentation with formatted sections for each endpoint and data model.
- Documentation is written to `docs/reference/api.md` and the raw OpenAPI spec is saved as `docs/reference/openapi.json`.

### When the Script Runs

- **Documentation builds:** The script runs automatically as part of `make docs`, `make docs-build`, and `make docs-prep`.
- **Pre-commit hooks:** A pre-commit hook runs the script whenever API-related files are modified (routes, models, or the script itself).
- **CI/CD:** The script runs during documentation builds in the CI pipeline, ensuring production docs are always current.

### What Gets Generated

- **API endpoint documentation:** Complete documentation for all API endpoints including HTTP methods, parameters, request/response schemas, and descriptions.
- **Data model documentation:** Detailed schemas for all API data models including field types, required/optional indicators, and descriptions.
- **OpenAPI specification:** Raw JSON specification file for use with API tools like Swagger UI.

### API Documentation Standards

When adding new API endpoints, ensure they follow documentation best practices:

- **Use descriptive docstrings:** FastAPI uses function docstrings as endpoint descriptions.
- **Add parameter descriptions:** Use Pydantic model field descriptions for comprehensive documentation.
- **Specify response models:** Always define response models using FastAPI's `response_model` parameter.
- **Include proper HTTP status codes:** Define all possible response status codes with appropriate response models.
- **Use tags:** Group related endpoints using FastAPI tags for better organization.

Example of well-documented endpoint:
```python
@router.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(
    user_id: int = Path(..., description="The unique identifier for the user")
) -> UserResponse:
    """Retrieve a specific user by their ID.

    Returns detailed information about a user including their profile data,
    preferences, and current status.
    """
    # Implementation here
    pass
```

### Troubleshooting

- **Missing API documentation:** Run `uv run -m scripts.generate_api_reference_docs` manually to regenerate.
- **Outdated documentation:** The script runs automatically, but manual execution may be needed during development.
- **Generation errors:** Check that all API routes can be imported and that the FastAPI app starts correctly.
- **Missing endpoint details:** Ensure endpoints have proper docstrings and response models defined.
