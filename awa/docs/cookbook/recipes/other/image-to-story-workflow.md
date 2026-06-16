# Image to Story Workflow

Transform images into comprehensive user stories and create Jira tickets with automated review questions.

## Overview

The `image-to-story` workflow takes an image input (typically a Figma design or UI mockup) and uses AI to generate comprehensive user stories that are automatically posted to Jira with follow-up review questions. This workflow is particularly useful for product managers and development teams who need to quickly convert visual designs into actionable development tasks.

## Demo

<div style="max-width: 640px"><div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;"><iframe src="https://twodegrees1.sharepoint.com/teams/AWA/_layouts/15/embed.aspx?UniqueId=e7f78f1f-b65a-46aa-a7b6-6bdec144e8cc&embed=%7B%22hvm%22%3Atrue%2C%22ust%22%3Afalse%7D&referrer=StreamWebApp&referrerScenario=EmbedDialog.Create" width="640" height="360" frameborder="0" scrolling="no" allowfullscreen title="AWA Image to Story Walkthrough 20250711.mp4" style="border:none; position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; max-width: 100%;"></iframe></div></div>

## Key Features

- **AI-Powered Story Generation**: Uses a multi-modal LLM to analyze images and create detailed user stories
- **Automatic Jira Integration**: Creates tickets directly in your configured Jira project
- **Review Question Generation**: Automatically generates critical review questions to ensure story completeness

## How It Works

1. **Image Processing**: The workflow accepts an image path and reads the image file
2. **Story Generation**: Uses the `GenerateStory` BAML function to analyze the image and create a user story
3. **Jira Ticket Creation**: Automatically creates a Jira ticket with the generated story
4. **Review Enhancement**: Uses the `ReviewStory` BAML function to generate ~5 critical questions
5. **Comment Addition**: Adds the review questions as a comment to the Jira ticket
6. **Result Return**: Returns the Jira ticket URL for immediate access

## Usage

### Input

| Name | Type | Description |
|------|------|-------------|
| `image_path` | `str` | Path to the image file to analyze. If not provided, defaults to `login.png` |
| `jira_project_id` | `str` | Jira project ID to create the ticket in. If not provided, defaults to `TSKSTRM` |

### Output

**Direct Output**: Jira ticket URL string

**File Outputs**:
- `story.json` - Contains the generated user story with title and description
- `jira_key.txt` - Contains the Jira issue key for reference
- `questions.json` - Contains the generated review questions array

**Generated Assets**:
- Jira ticket with user story title and description
- Jira comment with review questions for story validation

## Configuration

### Application

This workflow requires Jira to be configured in AWA's `config.yaml` file with the following settings:

:::code-group
```yaml [config.yaml]
jira:
  url: "https://slalom.atlassian.net"
  api_user: "ryan.henderson@slalom.com"
```
:::

### Environment

Provide your Jira API key in the AWA `.env` file.

:::code-group
```sh [.env]
#------------------------------#
#             Jira             #
#------------------------------#
# JIRA_APY_KEY=your_key
```
:::

## Command Line Execution

```bash
# Basic usage with default image
uv run -m awa.main run -w image-to-story
```

```bash
# Usage with custom image path
uv run -m awa.main run -w image-to-story --input '{"image_path": "path/to/your/design.png"}'
```
