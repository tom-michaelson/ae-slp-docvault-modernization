class UnitTestRequest {
  react_code string
  acceptance_criteria string
}

function WriteUnitTests(request: UnitTestRequest) -> string {
  client "openai/gpt-4.1"
  prompt #"
    You are a React testing expert tasked with writing comprehensive unit tests.

    <react_code_to_test>
    {{ request.react_code }}
    </react_code_to_test>

    <acceptance_criteria>
    {{ request.acceptance_criteria }}
    </acceptance_criteria>

    Your task is to:
    1. Write comprehensive unit tests for the React components
    2. Use React Testing Library and Jest
    3. Cover all acceptance criteria with appropriate test cases
    4. Test user interactions, component rendering, and business logic
    5. Include proper TypeScript types for test files
    6. Follow testing best practices and ensure high code coverage

    Return ONLY the complete test file content for App.test.tsx. Do not include any explanations or markdown code blocks.
  "#
}
