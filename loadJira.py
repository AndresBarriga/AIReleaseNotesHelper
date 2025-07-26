import requests

def format_jira_issue_to_csv_structure(issue):
    return {
        "key": issue["key"],
        "summary": issue["fields"].get("summary", ""),
        "description": issue["fields"].get("description", ""),
        "fix_versions": ", ".join([v["name"] for v in issue["fields"].get("fixVersions", [])])
    }
def load_tickets_by_project_and_fix_version(project_key, fix_versions, email, api_token, base_url):
    # Build JQL
    fix_version_jql = " OR ".join([f'fixVersion = "{fv}"' for fv in fix_versions])
    jql = f'project = {project_key} AND ({fix_version_jql}) ORDER BY key ASC'

    print(f"\n🔍 Running JQL: {jql}\n")

    url = f"{base_url}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "key,summary,description,issuetype,fixVersions"  # adjust as needed
    }

    response = requests.get(url, params=params, auth=(email, api_token))
    if response.status_code != 200:
        raise Exception(f"Jira request failed: {response.status_code} - {response.text}")

    data = response.json()
    issues = data.get("issues", [])

    if not issues:
        print("⚠️  No issues found.")
        return []

    print(f"✅ {len(issues)} issues loaded from Jira.")

    # Format issues to your expected dict structure
    formatted_issues = [
        {
            "Key": issue["key"],
            "Summary": issue["fields"].get("summary", ""),
            "Description": issue["fields"].get("description", ""),
            "Issue Type": issue["fields"]["issuetype"]["name"] if "issuetype" in issue["fields"] else "Other",
            "Fix Versions": ", ".join([v["name"] for v in issue["fields"].get("fixVersions", [])])
        }
        for issue in issues
    ]
    return formatted_issues


def load_tickets_by_project_and_fix_version_input(email, api_token, base_url):
    # Ask user for project key and fix versions
    project_key = input("Enter the project key (e.g. TNG4): ").strip()
    fix_versions_input = input("Which Fix Versions do you need? (comma-separated): ")
    fix_versions = [v.strip() for v in fix_versions_input.split(",") if v.strip()]

    if not project_key or not fix_versions:
        raise ValueError("Project key and at least one fix version are required.")

    # Build JQL
    fix_version_jql = " OR ".join([f'fixVersion = "{fv}"' for fv in fix_versions])
    jql = f'project = {project_key} AND ({fix_version_jql}) ORDER BY key ASC'

    print(f"\n🔍 Running JQL: {jql}\n")

    url = f"{base_url}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "key,summary,description,fixVersions"  # adjust as needed
    }

    response = requests.get(url, params=params, auth=(email, api_token))
    if response.status_code != 200:
        raise Exception(f"Jira request failed: {response.status_code} - {response.text}")

    data = response.json()
    issues = data.get("issues", [])

    if not issues:
        print("⚠️  No issues found for the specified project and fix versions.")
        return []

    print(f"✅ {len(issues)} issues loaded from Jira.")

    # Format issues like CSV output
    formatted_issues = [format_jira_issue_to_csv_structure(issue) for issue in issues]
    return formatted_issues
