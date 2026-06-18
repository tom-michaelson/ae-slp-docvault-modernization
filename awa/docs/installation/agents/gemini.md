# Agent - Gemini CLI

This document provides instructions on how to install and configure the Gemini CLI for use with AWA.

Gemini CLI is Google's command-line interface for interacting with Gemini models. For detailed information, refer to the official [Gemini CLI Documentation](https://ai.google.dev/gemini-api/docs/cli).

## Installation

See the [official docs](https://ai.google.dev/gemini-api/docs/cli) for information about how to install Gemini CLI on your system.

## Configuration

To use Gemini CLI with AWA, you'll need to:

1. **Set up API Key**: Obtain a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Configure Authentication**: Set your API key in your environment:

   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```

3. **For AWA Integration**: Add the `GEMINI_API_KEY` variable to your `.env` file. You can use `.env.example` as a template.

Refer to the official [Gemini API documentation](https://ai.google.dev/gemini-api/docs) for more details on authentication and configuration options.
