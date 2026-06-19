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
        end_column = self._column_letter(len(COLUMNS))
        range_name = f"{self.sheet_name}!A:{end_column}"
        existing = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=range_name)
            .execute()
            .get("values", [])
        )
        row_id = str(row.get("ID", ""))

        has_header = bool(existing and existing[0] and existing[0][0] == "ID")
        data_rows = existing[1:] if has_header else existing
        start_index = 2 if has_header else 1
        target_row_index = None
        for index, existing_row in enumerate(data_rows, start=start_index):
            if existing_row and str(existing_row[0]) == row_id:
                target_row_index = index
                break

        if target_row_index is None:
            service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body={"values": [values]},
            ).execute()
            return

        service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A{target_row_index}:{end_column}{target_row_index}",
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()

    def _upsert_local_csv(self, row: dict) -> None:
        self.local_fallback.parent.mkdir(parents=True, exist_ok=True)
        normalized_row = {column: row.get(column, "") for column in COLUMNS}
        existing_rows = []
        if self.local_fallback.exists():
            with self.local_fallback.open("r", newline="", encoding="utf-8") as f:
                existing_rows = list(csv.DictReader(f))

        replaced = False
        row_id = str(normalized_row.get("ID", ""))
        for index, existing_row in enumerate(existing_rows):
            if str(existing_row.get("ID", "")) == row_id:
                existing_rows[index] = normalized_row
                replaced = True
                break

        if not replaced:
            existing_rows.append(normalized_row)

        with self.local_fallback.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(existing_rows)

    @staticmethod
    def _column_letter(index: int) -> str:
        if index < 1:
            raise ValueError("index must be >= 1")
        value = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            value = chr(65 + remainder) + value
        return value
