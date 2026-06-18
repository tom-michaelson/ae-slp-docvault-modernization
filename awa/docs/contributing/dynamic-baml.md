# Dynamic BAML

Our `transform_activity` core activity supports dynamic BAML. The caller provides string BAML in the `baml_content` parameter.

## How it Works

To make this work, we have to do some fiddly stuff with BAML client generation. The logic for this can be read from the `transform_activity` code.

1. Compute the dynamic BAML client name by combining the workflow's task queue and the BAML function name, like: `my_task_queue/MyBamlFunction`.
2. Write BAML file to `awa/baml_dynamic/{queue_name}/{function_name}/baml_src/{function_name}.baml`.
3. Generate BAML client for the `awa/baml_dynamic/{queue_name}/{function_name}/baml_src` directory. This gives us a JIT BAML client containing only the given BAML code.
4. Provide the module name for this new BAML client to the LlmInvoker.
5. Execute the transform.

Note that we do check to see if the BAML client's content is already present in an existing generated client. If so, we skip re-generating the client. This means that client generation only has to happen the very first time our core worker sees a given BAML file.
