class DescribeTechStackRequest {
    tech_stack string
    file_name string
    file_content string
}

function DescribeTechStack(request: DescribeTechStackRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        You are an expert technical writer and software architect. Your task is to update or create a comprehensive, well-formatted Markdown description of a software project's technical stack.

        You will be provided with two pieces of information:
        1.  `tech_stack`: (Optional) The current Markdown description of the project's technical stack. This might be empty, partially complete, or outdated.
        2.  `dependency_manifest`: A string containing the content of a dependency manifest file from the project (e.g., `package.json`, `requirements.txt`, `pom.xml`, `build.gradle`, `Gemfile`, `Cargo.toml`, etc.).

        Your goal is to produce a new, updated Markdown description of the technical stack by:
        1.  Carefully analyzing the `dependency_manifest` to identify key technologies, programming languages, frameworks, significant libraries, databases, platforms, and other relevant components.
        2.  Comparing the information extracted from `dependency_manifest` with the existing `tech_stack` (if provided).
        3.  Integrating new information gleaned from the `dependency_manifest` into the tech stack description.
        4.  Ensuring the final output is a single, coherent, and well-formatted Markdown document.

        The output Markdown should be organized logically. Consider using the following sections, if applicable based on the information found:

        *   **`## Backend`**: Describe the backend language(s), framework(s) (e.g., FastAPI, Spring Boot, Node.js/Express), and any other significant backend technologies.
        *   **`## Frontend`**: If a frontend is indicated by the dependencies (e.g., React, Angular, Vue, Svelte, or template engines if a monolithic backend), describe the framework(s), primary languages (JavaScript, TypeScript), and key UI libraries (e.g., Material UI, Bootstrap).
        *   **`## Database`**: Identify and describe the database systems used (e.g., PostgreSQL, MongoDB, MySQL, Redis). Mention if it's an ORM or specific database clients.
        *   **`## Key Libraries & Dependencies`**: List and briefly describe other important libraries or dependencies that define the architecture or provide critical functionality but may not fit neatly into the above categories (e.g., state management libraries like Redux, authentication libraries like Auth0, messaging queues like RabbitMQ, containerization tech like Docker if evident from build files, CI/CD tools, testing frameworks).
        *   **`## Platforms & Infrastructure`**: Mention any cloud platforms (AWS, Azure, GCP), hosting environments, or other infrastructure-related details if they can be inferred.
        *   **`## Other Notable Technologies`**: Catch-all for anything else significant.

        **Guidelines for your output:**

        *   **Accuracy:** Ensure the information accurately reflects the dependencies provided.
        *   **Completeness:** Aim to be comprehensive but focus on the most impactful technologies. Avoid listing every minor utility unless it's highly relevant.
        *   **Clarity:** Use clear and concise language.
        *   **Formatting:** Use Markdown effectively (headings, bullet points, bold text for emphasis) to create a readable and organized document.
        *   **Handling Empty Inputs:**
            *   If the initial `tech_stack` is empty or not provided, generate the entire description based on the `dependency_manifest`.
            *   If the `dependency_manifest` is empty or does not provide enough information, state that and, if a `tech_stack` was provided, return it with a note that no new information could be added.
        *   **No Redundancy:** If information is already present and correct in the `tech_stack`, maintain it unless the `dependency_manifest` provides contradictory or more specific details.
        *   **Infer, Don't Assume:** Only include technologies that are explicitly mentioned or can be reasonably inferred from the `dependency_manifest`. Do not add technologies not supported by the evidence.
        *   **Structure:** If certain sections (like Frontend) are not applicable based on the `dependency_manifest`, omit them or explicitly state "Not applicable" or "No dedicated frontend dependencies identified."
        *   **Version Table:** Include a Markdown table summarizing key technologies and their versions. This table should be placed after the relevant descriptive sections or at the end of the document. Focus on major frameworks, languages, and platforms (e.g., Python 3.12, FastAPI 0.100.0, React 18.2.0). Only include versions if they are explicitly available in the `dependency_manifest` or `tech_stack`.

        **Example Input `dependency_manifest` (for a Python project - `requirements.txt`):**
        ```
        fastapi==0.100.0
        uvicorn[standard]==0.22.0
        pydantic==2.0.3
        sqlalchemy==1.4.47
        psycopg2-binary==2.9.6
        alembic==1.11.1
        redis==4.5.5
        celery==5.2.7
        python_version>=3.10
        ```

        **Example Output based on the above `dependency_manifest` (assuming `tech_stack` was empty):**
        ```markdown
        ## Backend
        The backend is built using Python (version 3.10 or newer) with the **FastAPI** framework. It utilizes **Uvicorn** as an ASGI server. Data validation is handled by **Pydantic**.

        ## Database
        The primary relational database is likely PostgreSQL, as indicated by the `psycopg2-binary` driver. **SQLAlchemy** is used as the ORM, and **Alembic** is employed for database migrations. **Redis** is also used, likely for caching or as a message broker.

        ## Key Libraries & Dependencies
        - **Celery**: For distributed task queues.

        ## Technology Versions

        | Technology | Version         |
        |------------|-----------------|
        | Python     | >=3.10          |
        | FastAPI    | 0.100.0         |
        | Uvicorn    | 0.22.0          |
        | Pydantic   | 2.0.3           |
        | SQLAlchemy | 1.4.47          |
        | Redis      | 4.5.5           |
        | Celery     | 5.2.7           |

        ```

        Produce the updated and well-formatted Markdown documentation of the tech_stack below.


        {{ _.role("user") }}

        <tech_stack description="The current Markdown description of the project's technical stack. This might be empty, partially complete, or outdated. Your output should represent the new version of this file.">
        {{request.tech_stack}}
        </tech_stack>

        <dependency_manifest name="{{request.file_name}}">
        {{request.file_content}}
        </dependency_manifest>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestDescribeTechStack {
  functions [DescribeTechStack]
  args {
    request {
        tech_stack #"
        ## Backend
        The backend is built using Python (version 3.10 or newer) with the **FastAPI** framework. It utilizes **Uvicorn** as an ASGI server. Data validation is handled by **Pydantic**.

        ## Database
        The primary relational database is likely PostgreSQL, as indicated by the `psycopg2-binary` driver. **SQLAlchemy** is used as the ORM, and **Alembic** is employed for database migrations. **Redis** is also used, likely for caching or as a message broker.
        "#
        file_name "requirements.txt"
        file_content #"
        fastapi==0.100.0
        uvicorn[standard]==0.22.0
        pydantic==2.0.3
        sqlalchemy==1.4.47
        psycopg2-binary==2.9.6
        alembic==1.11.1
        redis==4.5.5
        celery==5.2.7
        python_version>=3.10
        "#
    }
  }
}
