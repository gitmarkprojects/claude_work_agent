This application is a personal assistant powered by Anthropic's Claude model. It features:

- **Chat Interface:**  Engage in conversations with Claude through a web interface.
- **Memory System:**  The assistant remembers past conversations, summarizes them, and tracks tasks.
- **Task Management:**  It can identify and manage tasks from your conversations.

**Before you start:**

1. **API Keys:**
   - **Anthropic API Key:**  You MUST set your Anthropic API key as an environment variable named `ANTHROPIC_API_KEY`.  How to set environment variables depends on your operating system (e.g., in your terminal before running the app: `export ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY`).
   - **Groq API Key:**  Open the `templates/index.html` file. Find the line that says `API_KEY=...` and insert your actual Groq API key. This is ONLY needed if you want to use the transcription feature and can also easily be changed to the OpenAI API.  

2. **System Prompt (`system.txt`):**
   - This file contains the system prompt that guides Claude's behavior.
   - It can use variables like:
     - `{date}`: Current date.
     - `{plan}`: Content of `plan.txt` (you can create this file to give the assistant a plan).
     - `{status_report}`: Summaries of past conversations (managed automatically).
     - `{memory}`:  List of current active tasks (managed automatically).
   - You can customize `system.txt` to define the assistant's personality and goals.

3. **Memory and Tasks:**
   - The assistant automatically saves conversation history to `conversation.json`.
   - Older conversations are archived and summarized to `status_report.txt`.
   - Tasks are extracted from conversations and stored in `memory.json`.

**To run the application:**

1. **Open your terminal or command prompt.**
2. **Navigate to the directory where you saved the `app.py` file.**
3. **Run the command:** `python app.py`
4. **Open your web browser and go to:** `http://127.0.0.1:5000/`

You should now be able to chat with your personal assistant!