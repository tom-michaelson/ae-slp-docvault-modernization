To run any of these workflows, you will need to have AWA as well as the Recipe Temporal worker up and running.

<!--@include: ./recipe-setup-pre.md -->

4. From the AWA repo root directory, run your target workflow (for example, `awa-101-simple-direct-transform`):

   ```bash
   # /agentic-workflow-accelerator/
   uv run -m awa.main run -w "awa-101-simple-direct-transform" -q "awa_client_recipes"
   ```

<!--@include: ./recipe-setup-post.md -->
