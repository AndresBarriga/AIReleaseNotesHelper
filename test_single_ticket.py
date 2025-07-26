from dotenv import load_dotenv
import os
import json
from langchain_openai import ChatOpenAI
from loadJira import load_single_ticket
from main import summarize_ticket, categorize_ticket, format_release_notes_md, format_release_notes_docx

# === Load credentials
load_dotenv()
email = os.getenv("JIRA_EMAIL")
api_token = os.getenv("JIRA_API_TOKEN")
base_url = os.getenv("JIRA_BASE_URL")

# === Ticket to fetch
ticket_key = "TNG4-12559"
version = "test-single"

# === Load and summarize
tickets = load_single_ticket(ticket_key, email, api_token, base_url)

categorized_notes = {
    "Features": [],
    "Bug Fixes": [],
    "Improvements": [],
    "Other": []
}

for t in tickets:
    summary = t.get("Summary", "")
    description = t.get("Description", "")
    issue_type = t.get("Issue Type", "")
    key = t.get("Key", "UNKNOWN")

    note_dict = summarize_ticket(summary, description, key)
    category = categorize_ticket(issue_type)
    categorized_notes[category].append(note_dict)

# === Output
print(format_release_notes_md(categorized_notes, version))
format_release_notes_docx(categorized_notes, version, f"release_notes_{version}.docx")
