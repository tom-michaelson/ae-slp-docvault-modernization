class WritePoemRequest {
    noun string
    verb string
    adjective string
}

class WritePoemResult {
    poem string
}

function WritePoem(request: WritePoemRequest) -> WritePoemResult {
  client GithubCopilotSonnet4
    prompt #"
        {{ _.role("system") }}
        You are a poet. Write a madlibs-style poem. The poem should contain 3 stanzas exactly.

        {{ _.role("user") }}

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
