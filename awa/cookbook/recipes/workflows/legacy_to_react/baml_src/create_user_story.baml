class CreateUserStoryRequest {
    requirements ExtractedRequirementsForUserStory
}

class ExtractedRequirementsForUserStory {
    business_logic string[]
    data_structures string[]
    validations string[]
    user_interface_requirements string[]
    integration_points string[]
    summary string
}

class UserStory {
    title string @description("A concise, descriptive title for the user story")
    description string @description("The detailed description of the user story, in well-structured markdown format")
}

function CreateUserStory(request: CreateUserStoryRequest) -> UserStory {
    client "openai/gpt-4o"
    prompt #"
        You are an expert Agile product manager. Create a comprehensive user story based on the extracted COBOL requirements.

        <requirements>
        {{request.requirements}}
        </requirements>

        Create a user story that includes:

        1. **Title**: A concise, descriptive title for the story

        2. **Description**: Follow the standard format:
           - As a [type of user]
           - I want [goal/desire]
           - So that [benefit/value]

        3. **Acceptance Criteria**: Specific, testable criteria that must be met. Include:
           - Functional requirements
           - Data validation rules
           - UI/UX requirements
           - Performance expectations

        4. **Technical Notes**: Important technical details for developers including:
           - Data structure requirements
           - Business logic implementation notes
           - Integration considerations

        5. **Implementation Considerations**: Key points to consider during React implementation:
           - Component structure suggestions
           - State management needs
           - API requirements
           - Testing priorities

        The user story should be comprehensive enough for a developer to implement the React application without referring back to the COBOL code.

        ## Response format
        {{ ctx.output_format}}
    "#
}

test CreateUserStoryTest {
    functions [CreateUserStory]
    args {
        request {
            requirements {
                business_logic ["Display high value customers", "Read customer records sequentially"]
                data_structures ["Customer record with ID, Name, and Balance fields"]
                validations ["Balance threshold check > 1000"]
                user_interface_requirements ["Display customer names with high value indicator"]
                integration_points ["Read from customer file"]
                summary "Customer report program that identifies high value customers"
            }
        }
    }
}
