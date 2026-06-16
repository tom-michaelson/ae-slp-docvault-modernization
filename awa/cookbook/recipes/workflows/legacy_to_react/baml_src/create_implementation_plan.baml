class CreateImplementationPlanRequest {
    user_story UserStoryForImplementationPlan
    requirements ExtractedRequirementsForImplementationPlan
}

class UserStoryForImplementationPlan {
    title string
    description string
}

class ExtractedRequirementsForImplementationPlan {
    business_logic string[]
    data_structures string[]
    validations string[]
    user_interface_requirements string[]
    integration_points string[]
    summary string
}

class ImplementationPlan {
    overview string
    component_structure ComponentStructure
    state_management StateManagement
    api_integration ApiIntegration
    styling_approach string
    testing_strategy TestingStrategy
    step_by_step_plan string[]
}

class ComponentStructure {
    page_component string
    navigation_integration string
    minimal_dependencies string[]
}

class StateManagement {
    approach string
    simple_state_structure string
}

class ApiIntegration {
    data_source string
    simple_data_model string
}

class TestingStrategy {
    unit_tests string[]
    integration_tests string[]
    test_data_approach string
}

function CreateImplementationPlan(request: CreateImplementationPlanRequest) -> ImplementationPlan {
    client "openai/gpt-4o"
    prompt #"
        You are an expert React developer. Create a detailed implementation plan based on the user story and requirements.

        <user_story>
        {{request.user_story}}
        </user_story>

        <requirements>
        {{request.requirements}}
        </requirements>

        Create a comprehensive implementation plan that includes:

        1. **Overview**: Brief summary of the implementation approach

        2. **Component Structure**:
           - Single page component design
           - Navigation integration approach
           - Minimal dependencies needed

        3. **State Management**:
           - Simple state approach (useState/useEffect preferred)
           - Minimal state structure for single page

        4. **Data Integration**:
           - Data source (mock data, API, or file)
           - Simple data model structure

        5. **Styling Approach**: Simple CSS approach that matches existing site styles

        6. **Testing Strategy**:
           - Unit test requirements
           - Integration test scenarios
           - Test data approach

        7. **Step-by-Step Plan**: Ordered list of implementation steps that a developer should follow

        Focus on SIMPLICITY and SPEED of implementation. Prioritize a single working page that integrates cleanly with existing navigation over complex architecture. Use React hooks for state management and keep dependencies minimal.

        ## Response format
        {{ ctx.output_format}}
    "#
}

test CreateImplementationPlanTest {
    functions [CreateImplementationPlan]
    args {
        request {
            user_story {
                title "High Value Customer Report Display"
                description "As a business analyst, I want to view a report of high value customers, so that I can identify key accounts"
                acceptance_criteria ["Display customers with balance > $1000", "Show customer name and balance"]
                technical_notes "Customer data structure includes ID, Name, and Balance"
                implementation_considerations ["Use React hooks", "Implement data filtering"]
            }
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
