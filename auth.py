import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials():
    credentials = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    return credentials


def get_service(service, version):
    credentials = get_credentials()
    service = build(service, version, credentials=credentials)
    return service


def get_sheet_service():
    service = get_service("sheets", "v4")
    sheet = service.spreadsheets()
    return sheet


def get_drive_service():
    service = get_service("drive", "v3")
    drive = service.files()
    return drive


def get_permissions_service():
    service = get_service("drive", "v3")
    permissions = service.permissions()
    return permissions


if __name__ == "__main__":
    get_credentials()
