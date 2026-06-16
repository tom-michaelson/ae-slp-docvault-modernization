class ReviewStoryRequest {
  summary string
  description string
}

class ReviewStoryResponse {
  questions string[]
}

function ReviewStory(request: ReviewStoryRequest) -> ReviewStoryResponse {
  client "openai/gpt-4.1"
  prompt #"""
    You are a senior product manager tasked with reviewing a user story for a new web page based on a Figma design.

    Analyze the provided user story.

    Based on your analysis, generate a list of questions that need to be answered before the work can be started.

    Guidelines:
    - Focus on functional and non-functional requirements.
    - Think about testing and test case identification.
    - IMPORTANT: Limit your questions to the most critical ones. Do not ask more than ~5 questions unless ABSOLUTELY NECESSARY.
    - Do not worry about access to assets mentioned in the story.
    - Do not worry about timelines or deadlines.
    - Do not worry about cross-cutting concerns like basic logging, configuration storage, etc. Focus on what is likely unique to this story.

    <summary>
    {{ request.summary }}
    </summary>

    <description>
    {{ request.description }}
    </description>

    # Response
    {{ ctx.output_format }}
  """#
}

test TestReviewStory {
  functions [ReviewStory]
  args {
    request {
      summary "Build 'Refer a Friend' Rewards Landing Page"
      description #"
        <p>This user story covers the creation of a 'Refer a Friend' rewards landing page, as depicted in the provided Figma screenshot. The page is designed to encourage users to refer friends in exchange for rewards, and to clearly communicate the referral process and benefits. The main sections include a prominent header with a call-to-action, a step-by-step guide to the referral process, a rewards summary, and a referral link sharing component.</p>

        <p>Implementation Plan:<br/>
        1. Set up the page skeleton and layout structure.<br/>
        2. Build the header section with the main title, subtitle, and call-to-action button.<br/>
        3. Implement the step-by-step referral process section, including icons and descriptive text for each step.<br/>
        4. Create the rewards summary area, highlighting the reward amount and conditions.<br/>
        5. Develop the referral link sharing component, including the copy button and input field.<br/>
        6. Ensure responsive design for desktop and mobile views.<br/>
        7. Apply styles to match the Figma design, including colors, fonts, and spacing.<br/>
        8. Add accessibility features (e.g., alt text for icons, keyboard navigation).</p>

        <p>Acceptance Criteria:</p>
        <ul class="alternate" type="square">
            <li>The page displays a clear header with the title 'Refer a Friend' and a visible call-to-action button.</li>
            <li>The referral process is broken down into three visually distinct steps, each with an icon and explanatory text.</li>
            <li>The rewards summary clearly states the reward amount and any relevant conditions.</li>
            <li>Users can view and copy their unique referral link using a dedicated input and copy button.</li>
            <li>The design matches the Figma screenshot in terms of layout, colors, fonts, and spacing.</li>
            <li>The page is fully responsive and accessible.</li>
        </ul>
      "#
    }
  }
}
