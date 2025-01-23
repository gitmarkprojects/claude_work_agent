import json
import datetime
import uuid
from typing import List, Optional
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-3-5-sonnet-20241022"



class Task:
    def __init__(self, description: str, priority: int, 
                 note: str = "", next_date: Optional[datetime.date] = None,
                 created: Optional[datetime.date] = None,
                 last_interaction: Optional[datetime.date] = None,
                 task_id: Optional[str] = None,
                 status: str = "active"):
        self.id = task_id or str(uuid.uuid4())
        self.description = description
        self.priority = max(1, min(5, priority))
        self.note = note
        self.next_date = next_date or (datetime.date.today() + datetime.timedelta(days=7))
        self.created = created or datetime.date.today()
        self.last_interaction = last_interaction or datetime.date.today()
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "note": self.note,
            "next_date": self.next_date.isoformat(),
            "created": self.created.isoformat(),
            "last_interaction": self.last_interaction.isoformat(),
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            task_id=data['id'],
            description=data['description'],
            priority=data['priority'],
            note=data['note'],
            next_date=datetime.date.fromisoformat(data['next_date']),
            created=datetime.date.fromisoformat(data['created']),
            last_interaction=datetime.date.fromisoformat(data['last_interaction']),
            status=data['status']
        )

class TaskManager:
    def __init__(self, filename: str = "memory.json"):
        self.filename = filename
        self.active_tasks: List[Task] = []
        self.archived_tasks: List[Task] = []
        self._load()

    def _load(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.active_tasks = [Task.from_dict(t) for t in data.get('active_tasks', [])]
                self.archived_tasks = [Task.from_dict(t) for t in data.get('archived_tasks', [])]
        except FileNotFoundError:
            pass

    def save(self):
        data = {
            'active_tasks': [t.to_dict() for t in self.active_tasks],
            'archived_tasks': [t.to_dict() for t in self.archived_tasks]
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def process_conversation(self, messages: List[str]):
        prompt = self._create_prompt(messages)
        
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        self._process_commands(response.content[0].text.splitlines())
        self._check_decay()
        self.save()

    def _create_prompt(self, messages: List[str]) -> str:
        existing_tasks = []
        for task in self.active_tasks:
            task_str = f"[{task.id}] {task.description} (P{task.priority})"
            if task.note:
                task_str += f" - {task.note}"
            if task.next_date:
                task_str += f" @{task.next_date.isoformat()}"
            existing_tasks.append(task_str)

        return f"""You are the task management module. Analyze this conversation and output commands:

EXISTING TASKS:
{"\n".join(existing_tasks) or "No existing tasks"}

COMMAND SYNTAX:
1. NEW TASKS:
   NEW|priority|description|note|next_date
   - priority: 1-5 (1 = highest)
   - description: clear task description
   - note: brief context/reason
   - next_date: YYYY-MM-DD (today+7 if missing)

2. UPDATE TASKS:
   PRIORITY|id|new_priority
   DATE|id|YYYY-MM-DD
   NOTE|id|new_note
   BOOST|id (refresh last interaction)
   DONE|id

RULES:
- One command per line
- No pipes in text fields
- Use BOOST for mentions without changes
- Empty fields use "none"
- ASCII only
- Default next_date: today+7 days
- Maximum 50 active tasks; oldest low-priority tasks auto-archived when exceeded

EXAMPLE CONVERSATION:
"I need to finish my thesis chapter today. Also, cancel the dentist appointment."

EXAMPLE OUTPUT:
PRIORITY|thesis_ch3|1
DATE|thesis_ch3|{datetime.date.today().isoformat()}
DONE|dentist_apt

CONVERSATION:
{"\n".join(messages)}

OUTPUT COMMANDS:"""

    def _process_commands(self, commands: List[str]):
        today = datetime.date.today()
        for cmd in filter(None, map(str.strip, commands)):
            parts = cmd.split('|')
            action = parts[0].upper()

            try:
                if action == "NEW" and len(parts) >= 5:
                    self._create_task(parts[1:], today)
                elif len(parts) >= 2:
                    self._update_task(action, parts[1], parts[2] if len(parts)>=3 else None, today)
            except:
                continue

    def _create_task(self, parts: List[str], today: datetime.date):
        try:
            priority = max(1, min(5, int(parts[0])))
            description = parts[1].strip().replace('|', ' ')
            note = parts[2].strip().replace('|', ' ') if parts[2] != "none" else ""
            
            next_date = (today + datetime.timedelta(days=7))
            if parts[3] != "none":
                next_date = datetime.date.fromisoformat(parts[3])
            
            self.active_tasks.append(Task(
                description=description,
                priority=priority,
                note=note,
                next_date=next_date
            ))

            while len(self.active_tasks) > 50:
                sorted_tasks = sorted(self.active_tasks, key=...)
                task_to_archive = sorted_tasks[-1]  
                self.active_tasks.remove(task_to_archive)
                task_to_archive.status = "archived"
                self.archived_tasks.append(task_to_archive)
        except:
            pass

    def _update_task(self, action: str, task_id: str, value: Optional[str], today: datetime.date):
        task = next((t for t in self.active_tasks + self.archived_tasks if t.id == task_id), None)
        if not task:
            return

        try:
            if action == "PRIORITY" and value:
                task.priority = max(1, min(5, int(value)))
                task.last_interaction = today
            elif action == "DATE" and value:
                task.next_date = datetime.date.fromisoformat(value)
                task.last_interaction = today
            elif action == "NOTE" and value:
                task.note = value.replace('|', ' ')
                task.last_interaction = today
            elif action == "BOOST":
                task.last_interaction = today
            elif action == "DONE":
                task.status = "completed"
                if task in self.active_tasks:
                    self.active_tasks.remove(task)
                    self.archived_tasks.append(task)
        except:
            pass

    def _check_decay(self, threshold: float = 1.0):
        today = datetime.date.today()
        for task in self.active_tasks.copy():
            days_since = (today - task.last_interaction).days
            base_decay = days_since / (6 - task.priority)
            
            days_until = (task.next_date - today).days if task.next_date else 0
            urgency = 1 + (1 / max(days_until, 1)) if days_until >= 0 else 1
            
            decay_factor = base_decay / urgency if urgency != 0 else float('inf')
            
            if decay_factor > threshold:
                task.status = "archived"
                self.active_tasks.remove(task)
                self.archived_tasks.append(task)

    def generate_morning_briefing(self) -> str:
        today = datetime.date.today()
        briefing = []
        
        for task in self.active_tasks:
            briefing.append(
                f"[P{task.priority}] {task.description} @{task.created.isoformat()} #{task.status}\n"
                f"> last: {task.last_interaction.isoformat()}\n"
                f"> next: {task.next_date.isoformat()}\n"
                f"> {task.note or 'No additional context'}\n"
            )
        
        return "\n".join(briefing) if briefing else "No active tasks for today."

def process_archived_messages(messages):
    # Extract the content from the messages
    conversation = [turn["content"][0]["text"] for turn in messages]
    
    # Process the conversation using the TaskManager
    manager = TaskManager()
    manager.process_conversation(conversation)
    
    # Generate and print a morning briefing (optional)
    print("Updated Morning Briefing after processing archived messages:\n")
    print(manager.generate_morning_briefing())