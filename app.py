import time
import json
from anthropic import Anthropic
import os
from flask import Flask, render_template, request, jsonify
import datetime
import memory
import task_agent


app = Flask(__name__)
current_chat_file = None
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))






class ConversationHistory:
    def __init__(self):
        self.turns = []

    def add_turn_assistant(self, content):
        self.turns.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })

    def add_turn_user(self, content):
        self.turns.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })

    def get_turns(self):
        result = []
        user_turns_processed = 0
        for turn in reversed(self.turns):
            if turn["role"] == "user" and user_turns_processed < 2:
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": turn["content"][0]["text"],
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                })
                user_turns_processed += 1
            else:
                result.append(turn)
        return list(reversed(result))

    def get_full_history(self):
        return self.turns

    def save_to_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.turns, f, indent=2)



conversation_history = ConversationHistory()
# KISS: Load existing conversation.json if present
if os.path.exists('conversation.json'):
    with open('conversation.json', 'r') as f:
        turns = json.load(f)
        conversation_history.turns = turns

        
try:
    with open("system.txt", "r", encoding="utf-8") as f:
        sys_message = f.read()
except FileNotFoundError:
    print("Error: system.txt not found. Please create a file named system.txt with the system prompt and book content.")
    exit()

# Dictionary to hold the variable values
variables = {}

# Get the current date
variables['date'] = datetime.datetime.now().strftime("%Y-%m-%d")

# Read the content of plan.txt
try:
    with open("plan.txt", "r", encoding="utf-8") as f:
        variables['plan'] = f.read()
except FileNotFoundError:
    print("Warning: plan.txt not found. Using empty string for plan.")
    variables['plan'] = ""

# Read the content of status_report.txt
try:
    with open("status_report.txt", "r", encoding="utf-8") as f:
        variables['status_report'] = f.read()
except FileNotFoundError:
    print("Warning: status_report.txt not found. Using empty string for status_report.")
    variables['status_report'] = ""

try:
    with open("memory.json", "r", encoding="utf-8") as f:
        data = json.load(f)  # Load the entire JSON content into a Python dictionary

        if "active_tasks" in data:
            variables['memory'] = data["active_tasks"]  # Extract only the 'active_tasks' list and store in 'memory'
        else:
            print("Warning: 'active_tasks' key not found in memory.json. Using empty list for memory.")
            variables['memory'] = [] # Initialize as empty list if key is missing
except FileNotFoundError:
    print("Warning: memory.json not found. Using empty list for memory.")
    variables['memory'] = [] # Initialize as empty list if file not found
except json.JSONDecodeError:
    print("Warning: memory.json is not valid JSON. Using empty list for memory.")
    variables['memory'] = [] # Initialize as empty list if JSON is invalid
except KeyError as e: # Catch any other unexpected KeyErrors during JSON processing
    print(f"Warning: KeyError accessing JSON data: {e}. Using empty list for memory.")
    variables['memory'] = [] # Initialize as empty list if KeyError


# Format the system message with the variables
system_message = sys_message.format(**variables)
system_message = f"<file_contents> {system_message} </file_contents>"

MODEL_NAME = "claude-3-5-sonnet-20241022"  

def chat():
    turn_count = 1
    while True:
        print(f"\nTurn {turn_count}:")
        user_input = input("User: ")
    
        if user_input.lower() == 'exit':
            break
        
        conversation_history.add_turn_user(user_input)
        
        start_time = time.time()
        


        response = client.messages.create(
            model=MODEL_NAME,
            temperature=0.0,
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31"
            },
            max_tokens=8000,
            system=[
                {
                    "type": "text",
                    "text": system_message,
                    "cache_control": {"type": "ephemeral"}
                },
            ],
            messages=conversation_history.get_turns(),
        )
        
        end_time = time.time()
        
        assistant_reply = response.content[0].text
        print(f"Assistant: {assistant_reply}")
        
        conversation_history.add_turn_assistant(assistant_reply)
        
        
        # Display full conversation history
        print("\nConversation History:")
        for turn in conversation_history.get_full_history():
            role = turn["role"].capitalize()
            content = turn["content"][0]["text"]
            print(f"{role}: {content}")


        conversation_history.save_to_json('conversation.json')

        turn_count += 1



def manage_conversation_history():
    global conversation_history
    turns = conversation_history.get_full_history()
    
    # Check if we have more than 75 messages
    if len(turns) > 75:
        # Load or create conversation_archive.json
        archive_path = 'conversation_archive.json'
        if os.path.exists(archive_path):
            with open(archive_path, 'r') as f:
                archive = json.load(f)
        else:
            archive = []
        
        # Move excess messages to archive (keeping the last 50 in the main conversation)
        messages_to_archive = turns[:len(turns) - 50]
        archive.extend(messages_to_archive)
        
        # Update conversation history
        conversation_history.turns = turns[len(turns) - 50:]
        
        # Save updated archive
        with open(archive_path, 'w') as f:
            json.dump(archive, f, indent=2)
        

        # Trigger contextualization
        try:
            task_agent.process_archived_messages(messages_to_archive)
            memory.contextualize(archive)
        except Exception as e:
            print(f"Warning: Failed to contextualize archive: {e}")
        


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    global current_chat_file
    user_input = request.json['message']
    conversation_history.add_turn_user(user_input)
    
    start_time = time.time()
    
    response = client.messages.create(
        model=MODEL_NAME,
        extra_headers={
            "anthropic-beta": "prompt-caching-2024-07-31"
        },
        max_tokens=8000,
        system=[
            {
                "type": "text",
                "text": system_message,
                "cache_control": {"type": "ephemeral"}
            },
        ],
        messages=conversation_history.get_turns(),
    )
    
    end_time = time.time()
    
    assistant_reply = response.content[0].text
    conversation_history.add_turn_assistant(assistant_reply)

    # Manage conversation history
    manage_conversation_history()

    conversation_history.save_to_json('conversation.json')
    # Update the saved chat file if it exists
    if current_chat_file:
        conversation_history.save_to_json(current_chat_file)
    
    return jsonify({
        'reply': assistant_reply,
        'history': conversation_history.get_full_history()
    })
    

@app.route('/api/history', methods=['GET'])
def api_history():
    return jsonify(conversation_history.get_full_history())



@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    global conversation_history, current_chat_file
    conversation_history = ConversationHistory()
    current_chat_file = None
    
    # Add the new function calls
    try:
        memory.on_new_chat()
    except Exception as e:
        print(f"Warning: Failed to process new chat in memory/executive modules: {e}")
    
    return jsonify({"status": "success"})

@app.route('/api/save_chat', methods=['POST'])
def save_chat():
    global current_chat_file
    chat_name = request.json.get('chat_name', f"Chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    if not os.path.exists('chats'):
        os.makedirs('chats')
    filename = f"chats/{chat_name}.json"
    conversation_history.save_to_json(filename)
    current_chat_file = filename
    return jsonify({"status": "success", "filename": filename})

@app.route('/api/load_chat', methods=['POST'])
def load_chat():
    global conversation_history
    filename = request.json['filename']
    with open(filename, 'r') as f:
        turns = json.load(f)
    conversation_history = ConversationHistory()
    conversation_history.turns = turns
    return jsonify({"status": "success", "history": conversation_history.get_full_history()})

@app.route('/api/list_chats', methods=['GET'])
def list_chats():
    if not os.path.exists('chats'):
        return jsonify([])
    chats = [f for f in os.listdir('chats') if f.endswith('.json')]
    return jsonify(chats)






if __name__ == '__main__':
    try:
        memory.initialize()
    except Exception as e:
        print(f"Warning: Failed to initialize memory/executive modules: {e}")
    app.run(debug=True)