from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from loadCSV import load_tickets_from_csv
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

# === Core logic functions (not tools) ===

def summarize_ticket(summary, description, key=None):
    prompt = f"""You are helping write release notes. 
Given the Jira ticket summary and description, write a clear, user-facing sentence describing the change.

Summary: {summary}
Description: {description}"""
    response = llm.invoke(prompt)
    return response.content.strip()


def categorize_ticket(issue_type):
    if issue_type.lower() == "story":
        return "Features"
    elif issue_type.lower() == "bug":
        return "Bug Fixes"
    elif issue_type.lower() == "task":
        return "Improvements"
    else:
        return "Other"


def generate_release_notes(csv_path, version):
    tickets = load_tickets_from_csv(csv_path, version)

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

        note = summarize_ticket(summary, description)
        category = categorize_ticket(issue_type)
        categorized_notes[category].append(note)

    return categorized_notes


def format_release_notes_md(notes_dict, version):
    lines = [f"# Release Notes - Version {version}", ""]

    for category, items in notes_dict.items():
        if not items:
            continue
        lines.append(f"## {category}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)

# === Tool-wrapped functions for LangChain ===

@tool
def summarize_ticket_tool(prompt: str) -> str:
    """
    Summarize a Jira ticket.
    Input format: 'summary=...; description=...'
    """
    try:
        parts = dict(item.strip().split("=", 1) for item in prompt.split(";"))
        summary = parts.get("summary", "")
        description = parts.get("description", "")
    except Exception as e:
        return f"Invalid input format. Use: summary=...; description=...\nError: {str(e)}"

    return summarize_ticket(summary, description)


@tool
def categorize_ticket_tool(issue_type_str: str) -> str:
    """
    Categorize Jira ticket by type. Input: 'story', 'bug', etc.
    """
    return categorize_ticket(issue_type_str.strip())


@tool
def generate_release_notes_wrapper(query: str) -> str:
    """
    Generate formatted release notes.
    Input format: 'csv=...; version=...'
    """
    try:
        parts = dict(item.strip().split("=", 1) for item in query.split(";"))
        csv_path = parts.get("csv", "tickets.csv")
        version = parts.get("version", "v1.0.0")
    except Exception as e:
        return f"Failed to parse input. Use: 'csv=...; version=...'\nError: {str(e)}"

    notes_dict = generate_release_notes(csv_path, version)
    return format_release_notes_md(notes_dict, version)

# === Register tools and initialize agent ===

tools = [
    summarize_ticket_tool,
    categorize_ticket_tool,
    generate_release_notes_wrapper
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# === Manual execution for testing ===

if __name__ == "__main__":
    print("Manual test:\n")
    response = generate_release_notes_wrapper.invoke("csv=tickets.csv; version=v1.0.0")
    print(response)

    print("\nAgent test:\n")
    agent_response = agent.invoke("Generate release notes from tickets.csv for version v1.0.0")
    print(agent_response)
