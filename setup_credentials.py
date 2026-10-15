
import json
import getpass
from pathlib import Path

print("MANJHANPUR DASHBOARD — GOOGLE CONNECTION")

# Enter the location of your downloaded Google JSON key
json_path = input("Paste the full path of your JSON file: ").strip().strip('"')

with open(json_path, "r", encoding="utf-8") as f:
    credentials = json.load(f)

if credentials.get("type") != "service_account":
    raise ValueError("This is not a service account JSON key.")

password = getpass.getpass("Create your office dashboard password: ")

if len(password) < 12:
    raise ValueError("Use a password of at least 12 characters.")

folder = Path(".streamlit")
folder.mkdir(exist_ok=True)

content = "dashboard_password = " + json.dumps(password) + "\n\n"
content += "[gcp_service_account]\n"

for key, value in credentials.items():
    content += f"{key} = {json.dumps(str(value))}\n"

output = folder / "secrets.toml"
output.write_text(content, encoding="utf-8")

print("\nSUCCESS: Google credentials configured!")
print("Service account:", credentials["client_email"])
print("Credentials saved in .streamlit/secrets.toml")
print("Keep this file private.")
