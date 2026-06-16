class ClarifyingQuestions {
  questions string[]
}

class StructuredRequirements {
  requirements string[]
  user_stories string[]
  acceptance_criteria string[]
  technical_notes string[]
}

class FollowUpContext {
  original_request string
  conversation_history string
  latest_user_response string
}

function GenerateClarifyingQuestions(initial_description: string) -> ClarifyingQuestions {
  client "openai/gpt-4o"
  prompt #"
    {{ _.role("system") }}
    You are an expert business analyst helping gather comprehensive requirements for software features.

    Given an initial feature description, generate 5-7 specific clarifying questions that will help you understand:
    - The core functionality and user needs
    - Success criteria and acceptance conditions
    - Technical constraints and integration requirements
    - Edge cases and error handling
    - User experience and interface considerations
    - Performance and scalability requirements

    Focus on questions that will lead to actionable, testable requirements.

    {{ _.role("user") }}
    Initial feature description: {{ initial_description }}

    Generate clarifying questions to better understand this feature request.

    {{ ctx.output_format }}
  "#
}

function GenerateContextualFollowUpQuestions(context: FollowUpContext) -> ClarifyingQuestions {
  client "openai/gpt-4o"
  prompt #"
    {{ _.role("system") }}
    You are an expert business analyst conducting an interactive requirements gathering session.

    Based on the conversation so far, generate 3-5 relevant follow-up questions that:
    - Build on what the user just shared
    - Address any ambiguities or gaps in their latest response
    - Dive deeper into specific aspects they mentioned
    - Uncover additional details needed for implementation
    - Clarify technical constraints or business rules

    Make questions specific and actionable. Avoid generic questions.
    If the user's response seems complete for a topic, explore related areas or edge cases.
    If they provided vague answers, ask for specific details or examples.

    {{ _.role("user") }}
    **Original Request**: {{ context.original_request }}

    **Conversation History**:
    {{ context.conversation_history }}

    **User's Latest Response**: {{ context.latest_user_response }}

    Based on this conversation, generate relevant follow-up questions to gather more detailed requirements.

    {{ ctx.output_format }}
  "#
}

function AnalyzeRequirements(conversation_text: string) -> StructuredRequirements {
  client "openai/gpt-4o"
  prompt #"
    {{ _.role("system") }}
    You are an expert business analyst.
    Analyze the conversation between a system and user to extract comprehensive, structured requirements.

    Extract and organize the information into:

    1. **Requirements**: Core functional and non-functional requirements (be specific and testable)
    2. **User Stories**: Well-formed user stories following "As a [user type],
    I want [functionality], so that [benefit]" format
    3. **Acceptance Criteria**: Specific, testable criteria for each requirement
    using "Given/When/Then" or bullet format
    4. **Technical Notes**: Implementation considerations, constraints, integrations, performance requirements

    Make requirements specific, measurable, and actionable. Avoid vague language.

    {{ _.role("user") }}
    Here's the conversation to analyze:

    {{ conversation_text }}

    Extract structured requirements from this conversation.

    {{ ctx.output_format }}
  "#
}
