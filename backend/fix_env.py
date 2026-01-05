
import os

try:
    with open('.env', 'r', encoding='utf-8-sig') as f:
        content = f.read()
except FileNotFoundError:
    content = ""
except UnicodeDecodeError:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()

lines = content.splitlines()
api_key = "PLACEHOLDER"
for line in lines:
    if line.startswith("OPENAI_API_KEY="):
        api_key = line.split("=", 1)[1].strip()

new_content = f"""POSTGRES_SERVER=localhost
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=exam_evaluation_db
POSTGRES_PORT=5432
OPENAI_API_KEY={api_key}
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed .env file")
