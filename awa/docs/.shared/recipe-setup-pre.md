1. Complete the [Quick Start](/introduction/quick-start) guide to ensure you've got AWA up and running locally.

2. Ensure recipes are enabled in your `config.yaml`:

   ```yaml
   recipes: true
   ```

3. From the AWA repo root directory, start all the AWA services:

   ```bash
   make start
   ```

   With recipes enabled, the unified AWA worker will automatically load both core and recipe workflows.
