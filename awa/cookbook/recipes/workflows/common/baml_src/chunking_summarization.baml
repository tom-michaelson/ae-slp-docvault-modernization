// Generic chunking and summarization BAML functions

class ChunkSummaryRequest {
    content_items string[]
    chunk_index int
    total_chunks int
    context_data map<string,string>?
}

class FinalSummaryRequest {
    chunk_summaries string[]
    context_data map<string,string>?
}

// Generic function to summarize a single chunk of content
function SummarizeChunk(request: ChunkSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at creating concise, informative summaries of content.
        You are processing chunk {{ request.chunk_index }} of {{ request.total_chunks }} total chunks.

        Your task is to create a summary that:
        1. Preserves the essential information and structure
        2. Maintains important details that would be needed for understanding the whole
        3. Is concise but complete enough to be combined with other chunk summaries

        {% if request.context_data %}
        <context>
        {{ request.context_data }}
        </context>
        {% endif %}

        {{ _.role("user") }}
        Please summarize the following content items:

        <items>
        {% for item in request.content_items %}
        <item>{{ item }}</item>
        {% endfor %}
        </items>

        Create a structured summary that preserves the key information.

        {{ ctx.output_format }}
    "#
}

// Generic function to create a final summary from multiple chunk summaries
function SummarizeFinal(request: FinalSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at combining multiple summaries into a coherent, comprehensive final summary.

        Your task is to:
        1. Combine the chunk summaries into a single, well-structured summary
        2. Remove any redundancy while preserving all unique information
        3. Maintain logical flow and organization
        4. Ensure the final summary is complete and self-contained

        {% if request.context_data %}
        <context>
        {{ request.context_data }}
        </context>
        {% endif %}

        {{ _.role("user") }}
        Please combine the following chunk summaries into a final, comprehensive summary:

        <chunk_summaries>
        {% for summary in request.chunk_summaries %}
        <chunk_summary index="{{ loop.index }}">
        {{ summary }}
        </chunk_summary>
        {% endfor %}
        </chunk_summaries>

        Create a unified, well-organized summary that captures all the important information.

        {{ ctx.output_format }}
    "#
}

// Specialized function for summarizing directory content chunks
function SummarizeDirectoryChunk(request: ChunkSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at summarizing directory structures and file organizations.
        You are processing chunk {{ request.chunk_index }} of {{ request.total_chunks }} total chunks.

        Your task is to create a summary of the files and subdirectories that:
        1. Groups related items together
        2. Identifies the purpose and relationships of files/directories
        3. Preserves technical details and naming patterns
        4. Is concise but retains essential structural information

        {% if request.context_data and request.context_data.directory_name %}
        <directory_context>
        <directory_name>{{ request.context_data.directory_name }}</directory_name>
        </directory_context>
        {% endif %}

        {{ _.role("user") }}
        Please summarize the following file and directory descriptions:

        <file_and_directory_descriptions>
        {% for item in request.content_items %}
        <description>{{ item }}</description>
        {% endfor %}
        </file_and_directory_descriptions>

        Create a structured summary that captures the organization and purpose of these items.

        {{ ctx.output_format }}
    "#
}

// Specialized function for combining directory summaries
function SummarizeDirectoryFinal(request: FinalSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at describing directory structures and codebases.

        Your task is to:
        1. Combine the chunk summaries into a clear, comprehensive directory description
        2. Identify the overall purpose and structure of the directory
        3. Highlight important files and subdirectories
        4. Maintain technical accuracy while being concise

        {% if request.context_data and request.context_data.directory_name %}
        <directory_context>
        <directory_name>{{ request.context_data.directory_name }}</directory_name>
        </directory_context>
        {% endif %}

        {{ _.role("user") }}
        Please combine the following summaries into a final directory description:

        <directory_summaries>
        {% for summary in request.chunk_summaries %}
        <summary>
        {{ summary }}
        </summary>
        {% endfor %}
        </directory_summaries>

        Create a clear, well-organized description of this directory's contents and purpose.

        {{ ctx.output_format }}
    "#
}

test TestSummarizeChunk {
  functions [SummarizeChunk]
  args {
    request {
        content_items [
            "file1.py: Main application entry point with Flask app initialization",
            "config.yaml: Configuration settings for database and API keys",
            "utils.py: Utility functions for data processing"
        ]
        chunk_index 1
        total_chunks 3
        context_data {
            "purpose" "Testing chunk summarization",
            "project_type" "Python web application"
        }
    }
  }
}

// Specialized function for summarizing application content chunks
function SummarizeApplicationChunk(request: ChunkSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at analyzing and summarizing application architecture and codebases.
        You are processing chunk {{ request.chunk_index }} of {{ request.total_chunks }} total chunks.

        Your task is to create a summary that:
        1. Identifies key architectural components and their relationships
        2. Captures important technical details and patterns
        3. Groups related functionality together
        4. Preserves business context and application purpose

        {% if request.context_data and request.context_data.tech_stack %}
        <application_context>
        <tech_stack>{{ request.context_data.tech_stack }}</tech_stack>
        </application_context>
        {% endif %}

        {{ _.role("user") }}
        Please summarize the following directory and file descriptions from the application:

        <descriptions>
        {% for item in request.content_items %}
        <description>{{ item }}</description>
        {% endfor %}
        </descriptions>

        Create a structured summary that captures the key components and their purposes.

        {{ ctx.output_format }}
    "#
}

// Specialized function for creating final application summary
function SummarizeApplicationFinal(request: FinalSummaryRequest) -> string {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert at creating comprehensive application architecture summaries.

        Your task is to:
        1. Combine the chunk summaries into a complete application overview
        2. Identify the business purpose and key features
        3. Describe the architecture and codebase structure
        4. Highlight important technical patterns and design decisions
        5. Ensure the summary is coherent and self-contained

        {% if request.context_data and request.context_data.tech_stack %}
        <application_context>
        <tech_stack>{{ request.context_data.tech_stack }}</tech_stack>
        </application_context>
        {% endif %}

        {{ _.role("user") }}
        Please combine the following summaries into a comprehensive application summary:

        <chunk_summaries>
        {% for summary in request.chunk_summaries %}
        <summary>
        {{ summary }}
        </summary>
        {% endfor %}
        </chunk_summaries>

        Create a high-level summary that includes:
        - Business purpose of the application
        - Summary of features and capabilities
        - Architecture and codebase structure overview
        - Key technical patterns and components
        - Any other relevant insights

        {{ ctx.output_format }}
    "#
}

test TestSummarizeFinal {
    functions [SummarizeFinal]
    args {
        request {
            chunk_summaries [
                "Core application files including main entry point and configuration",
                "Utility modules and helper functions for data processing"
            ]
            context_data {
                "project_type" "Web application",
                "tech_stack" "Python Flask"
            }
        }
    }
}
