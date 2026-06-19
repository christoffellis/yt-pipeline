import csv
import os
from pathlib import Path

COLUMNS = [
    "ID",
    "Status",
    "Title",
    "Description",
    "Project Folder",
    "Script Complete",
    "Audio Complete",
    "Visuals Complete",
    "Video Complete",
    "Thumbnail Complete",
    "YouTube Link",
    "Created Date",
    "Published Date",
    "Notes",
]


class GoogleSheetsTracker:
    def __init__(self, local_fallback: Path):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        self.sheet_name = "YouTube Content Pipeline"
        self.local_fallback = local_fallback

    def upsert_row(self, row: dict) -> None:
        if self.sheet_id:
            self._upsert_google_sheet(row)
            return
        self._upsert_local_csv(row)

    def _upsert_google_sheet(self, row: dict) -> None:
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            self._upsert_local_csv(row)
            return

        credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if not credentials_path or not Path(credentials_path).exists():
            self._upsert_local_csv(row)
            return

        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        service = build("sheets", "v4", credentials=credentials)

        values = [row.get(column, "") for column in COLUMNS]
        service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A:N",
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()

    def _upsert_local_csv(self, row: dict) -> None:
        self.local_fallback.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.local_fallback.exists()
        with self.local_fallback.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerow({column: row.get(column, "") for column in COLUMNS})
