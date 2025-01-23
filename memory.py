import os
import json
import shutil
from anthropic import Anthropic
import datetime

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-3-5-sonnet-20241022"

def check_long_term_memory():
    if not os.path.exists("archive_status.txt"):
        return
    
    # Read entire archive
    with open("archive_status.txt", "r") as f:
        lines = f.readlines()
    
    # Find last MEMORY_PROCESSED block
    last_mem_idx = -1
    for i, line in enumerate(lines):
        if "[[MEMORY_PROCESSED]]" in line:
            last_mem_idx = i
    
    # Gather text after last processed block
    unprocessed_lines = lines[last_mem_idx + 1:] if last_mem_idx != -1 else lines
    unprocessed_text = "".join(unprocessed_lines).strip()
    
    # Check word count
    word_count = len(unprocessed_text.split())
    if word_count < 1000:
        return
    
    # Summarize chunk
    prompt = ("""
analyze these memories chronologically, focusing on:
1. concrete decisions and commitments made
2. evolving patterns in our work and thinking
3. key technical or strategic insights gained
4. outstanding questions or concerns

structure your response as a narrative that emphasizes connections between elements rather than just listing points. particularly note any shifts in approach or understanding.

limit response to 1500 words, prioritizing both depth and breadth.
"""
        + unprocessed_text
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        temperature=0.0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    summary_text = response.content[0].text
    
    # Overwrite lt_memory with the new summary
    with open("lt_memory.txt", "w") as f:  # Use 'w' mode to overwrite
        f.write(f"\n--- Long Term Memory Summary {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')} ---\n")
        f.write(summary_text)
        f.write("\n")
    
    # Mark block in archive
    with open("archive_status.txt", "a") as f:
        f.write(f"\n[[MEMORY_PROCESSED]]\n")


def manage_status_report():
    """Manage status report size by archiving old entries"""
    if not os.path.exists("status_report.txt"):
        return
        
    with open("status_report.txt", "r") as f:
        lines = f.readlines()
        
    if len(lines) > 100:
        # Archive first 10 lines
        with open("archive_status.txt", "a") as archive:
            archive.writelines(lines[:10])
            
        # Keep the rest in status_report
        with open("status_report.txt", "w") as f:
            f.writelines(lines[10:])
        
        # Check if we need to summarize the archive
        check_long_term_memory()

def process_chat_file(filepath):
    # Read chat content
    with open(filepath, 'r') as f:
        chat_data = json.load(f)
    
    # Construct chat history text
    chat_text = ""
    for turn in chat_data:
        role = turn["role"]
        content = turn["content"][0]["text"]
        chat_text += f"{role}: {content}\n"
    print(chat_text)

    # Get summary from Claude
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f""""
# extract important points from this conversation that future-me should remember:

- significant decisions or changes
- new insights or realizations
- relevant background information 
- open questions or uncertainties
- useful tools or concepts mentioned
- anything that gives helpful context for future conversations

# ignore routine tasks, pleasantries, or tangential discussions unless they reveal important context.

# format as clear, concise bullets using '-->' for direct implications or follow-ups.
write 3-5 points for shorter conversations, more for longer ones.

keep it simple - just capture what feels relevant for maintaining continuity.
write around 1-5 bullet points for shorter conversations, and more for longer ones. 

\n\n[[[{chat_text}]]]"""
        }]
    )
    summary = response.content[0].text

    # Manage status report size
    manage_status_report()

    # Append to status report
    with open("status_report.txt", "a") as f:
        f.write(f"\n--- Summary from {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')} ---\n")
        f.write(summary)
        f.write("\n")

    # Move file to archive
    archive_dir = "MEMORY_ARCHIVE"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    dest_path = os.path.join(archive_dir, os.path.basename(filepath))
    shutil.move(filepath, dest_path)

def initialize():
    """Process any existing chat files on startup"""
    if not os.path.exists("chats"):
        os.makedirs("chats")
        return

    for filename in os.listdir("chats"):
        if filename.endswith(".json"):
            filepath = os.path.join("chats", filename)
            try:
                process_chat_file(filepath)
            except Exception as e:
                print(f"Error processing {filename}: {e}")



def contextualize(archived_messages):
    """
    Process and summarize the archived messages.
    
    Args:
    archived_messages (list): A list of message dictionaries containing the archived conversation.
    
    Returns:
    None
    """
    print(f"Contextualizing {len(archived_messages)} archived messages")
    
    # Construct chat history text
    chat_text = ""
    for turn in archived_messages:
        role = turn["role"]
        content = turn["content"][0]["text"]
        chat_text += f"{role}: {content}\n"

    # Get summary from Claude
    prompt = f"""
# extract important points from this conversation that future-me should remember:

- significant decisions or changes
- new insights or realizations
- relevant background information 
- open questions or uncertainties
- useful tools or concepts mentioned
- anything that gives helpful context for future conversations

# ignore routine tasks, pleasantries, or tangential discussions unless they reveal important context.

# format as clear, concise bullets using '-->' for direct implications or follow-ups.
write 3-5 points for shorter conversations, more for longer ones.

keep it simple - just capture what feels relevant for maintaining continuity.
write around 3-5 points for shorter conversations, and more for longer ones. 

[[[{chat_text}]]]
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    summary = response.content[0].text

    # Append to status report
    with open("status_report.txt", "a") as f:
        f.write(f"\n--- Archived Summary from {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')} ---\n")
        f.write(summary)
        f.write("\n")

    # Append to total_archive.json
    if os.path.exists("total_archive.json"):
        with open("total_archive.json", "r") as f:
            total_archive = json.load(f)
    else:
        total_archive = []
    
    total_archive.extend(archived_messages)
    
    with open("total_archive.json", "w") as f:
        json.dump(total_archive, f, indent=2)

    # Clear conversation_archive.json
    if os.path.exists("conversation_archive.json"):
        os.remove("conversation_archive.json")

    print("Contextualization complete")