class JudgeOutputResult {
  answer bool
  explanation string
}

class DefineCriteriaResult {
  criteria string
}

function Judge_Output(generated: string, criteria: string) -> JudgeOutputResult {
  client "BedrockClaude37"
  prompt #"
    You are a strict evaluator. Given the generated output and the criteria, return True if the output meets the criteria, otherwise False.
    Output: {{ generated }}
    Criteria: {{ criteria }}
    Answer: Does the output meet the criteria? Answer True or False as a boolean. Give a short explanation and prove the answer, whether it is True or False.

    ## Response Format
    {{ ctx.output_format }}
  "#
}

function Define_Criteria(prompt: string) -> DefineCriteriaResult {
  client "BedrockClaude37"
  prompt #"
    You are a strict evaluator. Given the prompt, return a criteria that is specific to the prompt. Another LLM will
    use this criteria to evaluate the output. The criteria should be a single sentence explaining the criteria of the prompt
    and a bulleted list of requirements that must be met.
    Prompt: {{ prompt }}

    ## Response Format
    {{ ctx.output_format }}
  "#
}

test TestJudgeOutput {
  functions [Judge_Output]
  args {
    generated "This is wrong."
    criteria "The output is correct."
  }
}
