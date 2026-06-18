class ReactImplementationRequest {
  existing_app_tsx string
  implementation_plan string
  user_story string
  requirements string
}

function ImplementReactComponent(request: ReactImplementationRequest) -> string {
  client "openai/gpt-4.1"
  prompt #"
    You are a React developer tasked with implementing a new component based on legacy COBOL requirements.

    ## Existing App.tsx
    {{ request.existing_app_tsx }}

    ## Implementation Plan
    {{ request.implementation_plan }}

    ## User Story
    {{ request.user_story }}

    ## Requirements
    {{ request.requirements }}

    Your task is to:
    1. Modify the existing App.tsx to implement the functionality described in the requirements
    2. Create a modern, user-friendly React interface
    3. Ensure the component follows React best practices
    4. Maintain clean, readable code with proper TypeScript types
    5. Implement all the business logic from the COBOL requirements

    Return ONLY the complete new App.tsx file content. Do not include any explanations or markdown code blocks.
  "#
}
