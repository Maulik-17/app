import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import json

FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
SERVICE_JSON = os.getenv("SERVICE_JSON_BASE64")

# Decode base64 credentials
if SERVICE_JSON:
    import base64
    service_json = base64.b64decode(SERVICE_JSON).decode("utf-8")
    with open("/tmp/service.json", "w") as f:
        f.write(service_json)
    SERVICE_ACCOUNT_FILE = "/tmp/service.json"
else:
    SERVICE_ACCOUNT_FILE = "service_account.json"


SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)


def upload_to_drive(filepath):
    filename = os.path.basename(filepath)

    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID],
    }

    media = MediaFileUpload(filepath, mimetype="application/pdf")

    file = service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    print(f"✅ Uploaded {filename} → ID: {file['id']}")
