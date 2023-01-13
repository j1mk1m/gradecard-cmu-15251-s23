import gradescope

from constants import (
    USER_ENTERED,
    CARD_SHEETS,
    CARD_SHEETS_TO_DELETE,
)
from secrets import GRADESCOPE_COURSE_ID
from auth import get_sheet_service, get_drive_service, get_permissions_service


class GoogleCloudClient:
    def __init__(self):
        self.sheet = get_sheet_service()
        self.drive = get_drive_service()
        self.permissions = get_permissions_service()

    def __batch_update_sheet(self, spreadsheet_id, requests):
        self.sheet.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()

    def get_values_from_sheet(self, sheet_range, spreadsheet_id):
        result = (
            self.sheet.values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=sheet_range,
            )
            .execute()
        )
        return result.get("values", [])

    def set_values_in_sheet(
        self, sheet_range, spreadsheet_id, values, clear_range=False
    ):
        if clear_range:
            self.sheet.values().clear(
                spreadsheetId=spreadsheet_id,
                range=sheet_range,
            ).execute()

        self.sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            valueInputOption=USER_ENTERED,
            body={"values": values},
        ).execute()

    def get_sheets_from_spreadsheet(self, spreadsheet_id, as_dict=False):
        result = self.sheet.get(spreadsheetId=spreadsheet_id).execute()
        if as_dict:
            return {
                sheet["properties"]["title"]: sheet["properties"]["sheetId"]
                for sheet in result["sheets"]
            }
        else:
            return [sheet["properties"]["title"] for sheet in result["sheets"]]

    def create_sheet_in_spreadsheet(self, spreadsheet_id, sheet_name, header=None):
        self.__batch_update_sheet(
            spreadsheet_id,
            [
                {"addSheet": {"properties": {"title": sheet_name}}},
            ],
        )
        if header:
            self.set_values_in_sheet(
                sheet_range=sheet_name,
                spreadsheet_id=self.spreadsheet_id,
                values=[header],
            )

    def create_new_spreadsheet(self, name, sheets, destination, email_ids=[]):
        # Create new spreadsheet
        create = {
            "properties": {"title": name},
            "sheets": [{"properties": {"title": sheet}} for sheet in sheets],
        }
        response = self.sheet.create(body=create).execute()
        ssid = response["spreadsheetId"]

        # Move spreadsheet to folder
        file = self.drive.get(fileId=ssid, fields="parents").execute()
        previous_parents = ",".join(file.get("parents"))
        file = self.drive.update(
            fileId=ssid,
            addParents=destination,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()

        # Share spreadsheet with emails
        for email_id in email_ids:
            share = {"role": "writer", "type": "user", "emailAddress": email_id}
            self.permissions.create(body=share, fileId=ssid).execute()

        return ssid

    def copy_sheets_to_spreadsheet(
        self,
        source_spreadsheet_id,
        source_sheet_names,
        destination_spreadsheet_id,
        destination_sheet_names,
    ):
        requests = []

        map_source_sheet_name_to_id = self.get_sheets_from_spreadsheet(
            spreadsheet_id=source_spreadsheet_id, as_dict=True
        )
        map_destination_sheet_name_to_id = self.get_sheets_from_spreadsheet(
            spreadsheet_id=destination_spreadsheet_id, as_dict=True
        )

        for source_sheet_name, destination_sheet_name in zip(
            source_sheet_names, destination_sheet_names
        ):
            destination_sheet_id = map_destination_sheet_name_to_id.get(
                destination_sheet_name
            )
            if destination_sheet_id is not None:
                requests.append({"deleteSheet": {"sheetId": destination_sheet_id}})

            # Copy source_sheet to destination
            source_sheet_id = map_source_sheet_name_to_id.get(source_sheet_name)
            response = (
                self.sheet.sheets()
                .copyTo(
                    spreadsheetId=source_spreadsheet_id,
                    sheetId=source_sheet_id,
                    body={"destination_spreadsheet_id": destination_spreadsheet_id},
                )
                .execute()
            )
            new_sheet_id = response["sheetId"]

            # Refactor new sheet
            requests.append(
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": new_sheet_id,
                            "index": CARD_SHEETS.index(destination_sheet_name),
                            "title": destination_sheet_name,
                        },
                        "fields": "title, index",
                    }
                }
            )

        # Delete any sheets to delete, if they still exist
        for sheet in CARD_SHEETS_TO_DELETE:
            destination_sheet_id = map_destination_sheet_name_to_id.get(sheet)
            if destination_sheet_id is not None:
                requests.append({"deleteSheet": {"sheetId": destination_sheet_id}})

        self.__batch_update_sheet(destination_spreadsheet_id, requests)


class GradescopeClient:
    def __init__(self):
        self.client = GoogleCloudClient()
        self.assignments = gradescope.get_course_assignments(GRADESCOPE_COURSE_ID)

    def get_assignment_by_name(self, assignment_name):
        for assignment in self.assignments:
            if assignment_name == assignment["name"]:
                return assignment

        raise KeyError("No Assignment Found")

    def get_evaluation_data_by_assignment_id(self, assignment_id):
        return gradescope.get_assignment_evaluations(
            GRADESCOPE_COURSE_ID, assignment_id
        )
