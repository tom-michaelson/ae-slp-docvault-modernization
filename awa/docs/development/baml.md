# BAML

AWA uses [BAML](https://www.boundaryml.com/) for all LLM calls. BAML is a library and assiocated tooling that make it easy to create and iterate on prompts.

:::warning BAML Docs
This page is not a comprehensive guide to BAML. Rely on BAML's official docs for more information: https://docs.boundaryml.com/home.
:::

## Why BAML?

See [Architecture](/introduction/architecture#baml) for more information on why BAML is a good fit for AWA, and what high-level benefits it provides.

## BAML Files

Prompts are defined in BAML files (`my_prompt.baml`) within a special `baml_src` directory (or multiple directories). In these files, you use the BAML language to define your prompt, inputs, and outputs. You can also define tests (evals) for your prompts.

See the example below.

:::code-group

```baml [write_poem.baml]
class WritePoemRequest {
    noun string
    verb string
    adjective string
}

class WritePoemResult {
    poem string
}

function WritePoem(request: WritePoemRequest) -> WritePoemResult {
  client "openai/gpt-4.1"
    prompt #"
        Write a madlibs-style poem. The poem should contain 3 stanzas exactly.

        Noun: {{ request.noun }}
        Verb: {{ request.verb }}
        Adjective: {{ request.adjective }}

        ## Response Format
        {{ ctx.output_format }}
    "#
}


test TestWritePoemRequest {
    functions [WritePoem]
    args {
        request {
            noun "cat"
            verb "meow"
            adjective "cute"
        }
    }
}
```

:::

## BAML Playground

BAML comes with an [official VS Code extension](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension) (also works in Cursor and other VS Code forks). This extension provides a prompt "playground" that allows you to quickly execute your prompts and defined tests. This allows you to quickly iterate on your prompts without running the entire workflow.

<img src="/images/baml-playground.png" alt="BAML Playground" />

## AWA + BAML

AWA's core [Transform](/reference/activity/transform) activity is a wrapper around BAML prompt execution. It allows you to execute a BAML file + function, and return the result, without having to write any code in your client solution.

The way this works is that the content of your target BAML file is passed as input to the Transform activity. AWA then generates a BAML client app for the given function (this is only done once each time a novel BAML function is seen), executes, then returns the result to the caller of the activity.
