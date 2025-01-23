# Claude Personal Assistant

Build persistent, coherent thinking partnerships with LLMs. This framework provides:
- Long-term memory and context maintenance
- Strategic alignment across conversations
- Automated task extraction and priority management

## Features

- **Chat Interface:** Engage in conversations with Claude through a user-friendly web interface.
- **Memory System:** The assistant remembers past conversations, summarizes them, and intelligently tracks tasks across interactions.
- **Task Management:**  It can automatically identify and manage tasks extracted from your conversations, helping you stay organized.

## Getting Started

Before you begin, you need to set up your API keys and understand the system prompt.

### 1. API Keys

You will need API keys for both Anthropic and (optionally) Groq.

- **Anthropic API Key:**
    - **REQUIRED.** You **MUST** set your Anthropic API key as an environment variable named `ANTHROPIC_API_KEY`.
    - **How to set environment variables:** The method depends on your operating system.
        - **Linux/macOS:** Open your terminal and run:
          ```bash
          export ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY
          ```
        - **Windows (Command Prompt):**
          ```cmd
          set ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY
          ```
        - **Windows (PowerShell):**
          ```powershell
          $env:ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"
          ```
    - **Replace `YOUR_ANTHROPIC_API_KEY` with your actual Anthropic API key.**

- **Groq API Key (Optional - for Transcription):**
    - **OPTIONAL.**  This is only required if you want to use the transcription feature. You can also easily switch to OpenAI's Whisper API for transcription if preferred.
    - **Setup:**
        1. Open the `templates/index.html` file.
        2. Locate the line that looks like `API_KEY=...` (it will be commented out or have a placeholder).
        3. Insert your actual Groq API key in place of the placeholder.

### 2. System Prompt (`system.txt`)

The `system.txt` file defines the system prompt that guides Claude's behavior and personality.

- **Customization:** You can customize this file to tailor the assistant's personality, goals, and how it interacts with you.
- **Variables:** The system prompt can utilize the following variables which are dynamically replaced by the application:
    - `{date}`:  The current date.
    - `{plan}`:  The content of the `plan.txt` file (create this file to give the assistant a specific plan or context).
    - `{status_report}`: Summaries of past conversations (managed automatically by the application).
    - `{memory}`: A list of currently active tasks (also managed automatically).

### 3. Memory and Tasks

This application automatically manages conversation history and tasks:

- **Conversation History:** Saved to `conversation.json`.
- **Archived Conversations:** Older conversations are summarized and archived into `status_report.txt`.
- **Tasks:** Extracted from conversations and stored in `memory.json`.

## Running the Application

Follow these steps to run your personal assistant:

1. **Open your terminal or command prompt.**
2. **Navigate to the directory where you saved the `app.py` file** using the `cd` command (e.g., `cd path/to/your/project`).
3. **Run the application using Python:**
   ```bash
   python app.py
   ```
4. **Access the web interface:** Open your web browser and go to the following address:
   ```
   http://127.0.0.1:5000/
   ```

You should now be able to start chatting with your Claude-powered personal assistant!

