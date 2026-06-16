# Combine OpenAPI Specifications

Combine multiple OpenAPI specification documents into a single unified specification file.

## Arguments

- `specs`: $ARGUMENTS (comma-separated list of paths to OpenAPI spec files)
- `output`: The output file path for the combined specification

## Usage

```
/combine-open-api-specs specs: [path1.yaml, path2.yaml, path3.json] output: [output-path.yaml]
```

## Instructions

You are tasked with combining multiple OpenAPI specification documents into a single cohesive specification file. Follow these steps carefully:

### 1. Parse Input Arguments

Extract from the arguments:
- **specs**: A list of file paths to OpenAPI specification documents (YAML or JSON format)
- **output**: The destination path for the combined specification

### 2. Read and Validate Each Specification

For each specification file:
1. Read the file contents
2. Parse as YAML or JSON based on file extension
3. Validate that it contains required OpenAPI fields (`openapi`, `info`, `paths`)
4. Note the OpenAPI version (should be compatible, preferably all 3.x)

### 3. Merge Strategy

Combine the specifications using this merge strategy:

#### Base Document Structure
- Use the **first specification** as the base for `openapi` version and `info` section
- If specs have different versions, prefer the highest 3.x version
- Merge `info.title` as "Combined API - [list of original titles]" or use a sensible combined name
- Set `info.version` to "1.0.0-combined" or aggregate versions

#### Paths Merging
- Combine all `paths` objects from each specification
- **Conflict Resolution**: If the same path exists in multiple specs:
  - If methods differ, merge the methods under the same path
  - If same path AND same method exist, prefix the operationId and add a tag indicating source spec
  - Log/note any conflicts for user awareness

#### Components Merging
Merge all `components` subsections:
- `schemas`: Combine all schemas; prefix duplicates with source spec identifier
- `responses`: Merge response definitions
- `parameters`: Merge parameter definitions
- `requestBodies`: Merge request body definitions
- `headers`: Merge header definitions
- `securitySchemes`: Merge security schemes; note conflicts
- `links`: Merge link definitions
- `callbacks`: Merge callback definitions

#### Tags Merging
- Combine all `tags` arrays
- Remove duplicates (by tag name)
- Preserve tag descriptions

#### Servers Merging
- Combine all `servers` arrays
- Remove exact duplicates
- Optionally group by source specification

#### Security Merging
- Merge global `security` requirements
- Preserve all unique security requirement objects

#### Other Top-Level Fields
- `externalDocs`: Keep from first spec or merge into array
- `webhooks` (OpenAPI 3.1): Merge following paths strategy

### 4. Handle Naming Conflicts

When encountering naming conflicts:
1. **Schemas**: Rename duplicates using pattern `{OriginalName}_{SourceSpecIdentifier}`
2. **OperationIds**: Ensure uniqueness by prefixing with source identifier if needed
3. **Update all $ref references** to point to renamed components
4. Document all renames in a comment or separate manifest

### 5. Output Format

- Determine output format from the `output` file extension:
  - `.yaml` or `.yml`: Output as YAML
  - `.json`: Output as JSON with 2-space indentation
- Ensure proper formatting and valid syntax

### 6. Validation

After combining:
1. Validate the combined spec has no broken `$ref` references
2. Ensure all operationIds are unique
3. Verify required fields are present
4. Check for circular references in schemas

### 7. Write Output

Write the combined specification to the specified output path.

### 8. Report Results

Provide a summary including:
- Number of specifications combined
- Total number of paths in combined spec
- Total number of schemas in combined spec
- Any conflicts encountered and how they were resolved
- Any warnings or issues to be aware of
- Confirmation of output file location

## Example

```
/combine-open-api-specs specs: [./specs/auth-api.yaml, ./specs/users-api.yaml, ./specs/products-api.json] output: ./combined/full-api.yaml
```

## Notes

- This command handles both YAML and JSON OpenAPI specifications
- OpenAPI 3.0.x and 3.1.x specifications are supported
- The command will attempt to preserve as much information as possible from all source specifications
- Review the combined output for any manual adjustments needed, especially for complex conflict resolutions
