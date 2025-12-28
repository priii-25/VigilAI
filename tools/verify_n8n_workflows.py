"""Verify n8n workflow JSON files."""
import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

workflows = [
    "n8n/competitor_monitoring.json",
    "n8n/battlecard_automation.json", 
    "n8n/weekly_digest.json",
    "n8n/aiops_incidents.json"
]

print("Validating n8n workflow files...")
print("-" * 40)

for workflow in workflows:
    try:
        with open(workflow, "r", encoding="utf-8") as f:
            data = json.load(f)
            name = data.get("name", "Unknown")
            nodes = len(data.get("nodes", []))
            print(f"✓ {os.path.basename(workflow)}: '{name}' ({nodes} nodes)")
    except Exception as e:
        print(f"✗ {workflow}: {e}")

print("-" * 40)
print("Validation complete!")
