import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from loadCSV import load_tickets_from_csv
from loadJira import load_tickets_by_project_and_fix_version
from main import summarize_ticket, categorize_ticket

# Load env vars
load_dotenv()

# Init LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

st.set_page_config(page_title="AI Release Notes Generator", layout="centered")

st.title("🧠 AI Release Notes Generator")

source = st.radio("Choose ticket source:", ["CSV", "Jira"])

tickets = []
version = ""

if source == "CSV":
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    version = st.text_input("Release version (e.g. v1.2.3)")

    if uploaded_file and version:
        tickets = load_tickets_from_csv(uploaded_file, version)
        st.success(f"✅ {len(tickets)} tickets loaded from CSV.")

elif source == "Jira":
    project_key = st.text_input("Enter Jira project key (e.g. TNG4)")
    fix_versions_raw = st.text_input("Enter fix versions (comma-separated)")
    version = fix_versions_raw

    if project_key and fix_versions_raw:
        fix_versions = [v.strip() for v in fix_versions_raw.split(",") if v.strip()]
        st.info(f"🔍 Running JQL: project = {project_key} AND (fixVersion = {fix_versions_raw})")

        if st.button("Load tickets from Jira"):
            email = os.getenv("JIRA_EMAIL")
            api_token = os.getenv("JIRA_API_TOKEN")
            base_url = os.getenv("JIRA_BASE_URL")

            tickets = load_tickets_by_project_and_fix_version(
                project_key, fix_versions, email, api_token, base_url
            )
            st.success(f"✅ {len(tickets)} issues loaded from Jira.")

if tickets:
    with st.spinner("✍️ Generating release notes..."):
        categorized_notes = {
            "Features": [],
            "Bug Fixes": [],
            "Improvements": [],
            "Other": []
        }

        for t in tickets:
            summary = t.get("Summary", "") or t.get("summary", "")
            description = t.get("Description", "") or t.get("description", "")
            issue_type = t.get("Issue Type", "") or t.get("issue_type", "")
            key = t.get("Key", "") or t.get("key", "UNKNOWN")
            title = summary.strip()  # Use summary as title

            note_dict = summarize_ticket(summary, description, key)
            note_dict["title"] = title  # Add title for frontend display

            category = categorize_ticket(issue_type)
            categorized_notes[category].append(note_dict)

    # === Display Notes ===
    st.markdown(f"# 📝 Release Notes - Version {version}")

    for category, items in categorized_notes.items():
        if not items:
            continue

        st.markdown(f"## {category}")
        for entry in items:
            key = entry.get("key", "UNKNOWN")
            title = entry.get("title", "Untitled")
            release_note = entry.get("release_note", "No release note provided.")
            key_features = entry.get("key_features", [])

            st.markdown(f"**{key}**")
            st.markdown(f"**Title:** {title}")
            st.markdown(f"**Summary:**\n```json\n{json.dumps(entry, indent=2)}\n```")

            if release_note:
                st.markdown(f"*{release_note}*")

            if key_features:
                st.markdown("**Key Features:**")
                for feat in key_features:
                    st.markdown(f"- {feat}")

            st.markdown("---")
