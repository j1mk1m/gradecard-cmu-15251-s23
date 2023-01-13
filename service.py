import configparser
import csv
import io
import os

from cli import prompt_confirm_unpublished
from client import GoogleCloudClient, GradescopeClient
from constants import (
    ROSTER_SHEET_NAME,
    ROSTER_SHEET_RANGE_W,
    ROSTER_HEADER,
    EXPORT_SHEET_NAME,
    EXPORT_HEADER,
    EXPORT_SHEET_RANGE_R,
    EXPORT_SHEET_RANGE_W,
    CARD_SHEETS,
    EXPORT_SHEET_RANGE_HEADER,
    DATA_SHEET_NAME,
    CONFIG_PATH,
    STAR_THRESHOLD,
)
from secrets import (
    BASE_STUDENT_SPREADSHEET_ID,
    STUDENT_CARDS_FOLDER_ID,
    TA_CARDS_FOLDER_ID,
    GRADECARD_SPREADSHEET_ID,
)
from util import (
    get_entry,
    get_entries_across,
    get_entries,
    set_entry,
    set_entries_across,
    now,
    truncate_values,
    round_to_hundredths,
)
# imports for catching http errors and starting again
from googleapiclient.errors import HttpError
from time import sleep

class GoogleCloudService:
    def __init__(self):
        self.spreadsheet_id = GRADECARD_SPREADSHEET_ID
        self.client = GoogleCloudClient()

    def add_students(self, roster):
        # Create roster sheet in spreadsheet, if it does not exist
        sheets = self.client.get_sheets_from_spreadsheet(
            spreadsheet_id=self.spreadsheet_id
        )
        if ROSTER_SHEET_NAME not in sheets:
            print("[INFO] Creating roster sheet in spreadsheet")
            self.client.create_sheet_in_spreadsheet(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name=ROSTER_SHEET_NAME,
                header=ROSTER_HEADER,
            )

        # Get list of existing students
        values = self.client.get_values_from_sheet(
            sheet_range=ROSTER_SHEET_RANGE_W, spreadsheet_id=self.spreadsheet_id
        )
        andrew_ids = set(get_entries(values, "Andrew ID", ROSTER_HEADER))

        # Get list of new students
        new_students = []
        for student in roster:
            if get_entry(student, "Andrew ID", ROSTER_HEADER) not in andrew_ids:
                new_students.append(list(student))

        # Append new students to roster sheet
        if new_students:
            print("[INFO] Adding new students to spreadsheet")
            values.extend(new_students)
            self.client.set_values_in_sheet(
                sheet_range=ROSTER_SHEET_RANGE_W,
                spreadsheet_id=self.spreadsheet_id,
                values=values,
            )

    def create_cards(self, agents):
        # Create export sheet in spreadsheet, if it does not exist
        sheets = self.client.get_sheets_from_spreadsheet(
            spreadsheet_id=self.spreadsheet_id
        )
        if EXPORT_SHEET_NAME not in sheets:
            print("[INFO] Creating export sheet in spreadsheet")
            self.client.create_sheet_in_spreadsheet(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name=EXPORT_SHEET_NAME,
                header=EXPORT_HEADER,
            )

        # Get list of students in export sheet
        values = self.client.get_values_from_sheet(
            sheet_range=EXPORT_SHEET_RANGE_R, spreadsheet_id=self.spreadsheet_id
        )
        andrew_ids = set(get_entries(values, "andrew_id", EXPORT_HEADER))

        # Get list of students in roster sheet
        roster = self.client.get_values_from_sheet(
            sheet_range=ROSTER_SHEET_RANGE_W, spreadsheet_id=self.spreadsheet_id
        )

        # Get list of new students
        new_students = []
        for student in roster:
            # Get fields from record
            andrew_id = get_entry(student, "Andrew ID", ROSTER_HEADER)
            email_id = get_entry(student, "Email", ROSTER_HEADER)

            if andrew_id not in andrew_ids:
                entries_dict = {
                    "andrew_id": andrew_id,
                    "email": email_id,
                    "last_updated": now(),
                }

                # Create student card
                if "student" in agents:
                    print(f"[INFO] Creating student card for {andrew_id}")
                    ssid = self.client.create_new_spreadsheet(
                        f"[15-251] Student Card ({andrew_id})",
                        CARD_SHEETS,
                        STUDENT_CARDS_FOLDER_ID,
                        [email_id],
                    )
                    entries_dict["ssid"] = ssid

                # Create TA card
                if "ta" in agents:
                    print(f"[INFO] Creating TA card for {andrew_id}")
                    _ssid = self.client.create_new_spreadsheet(
                        andrew_id, CARD_SHEETS, TA_CARDS_FOLDER_ID
                    )
                    entries_dict["_ssid"] = _ssid

                # Create new record
                record = ["" for _ in EXPORT_HEADER]
                set_entries_across(record, entries_dict, EXPORT_HEADER)
                new_students.append(record)

            if len(new_students) >= 5:
                print("[INFO] Adding new cards IDs to spreadsheet")
                values.extend(new_students)
                self.client.set_values_in_sheet(
                    sheet_range=EXPORT_SHEET_RANGE_W,
                    spreadsheet_id=self.spreadsheet_id,
                    values=truncate_values(values, EXPORT_HEADER),
                )
                new_students = []

        if new_students:
            print("[INFO] Adding new cards IDs to spreadsheet")
            values.extend(new_students)
            self.client.set_values_in_sheet(
                sheet_range=EXPORT_SHEET_RANGE_W,
                spreadsheet_id=self.spreadsheet_id,
                values=truncate_values(values, EXPORT_HEADER),
            )

    def update_views(self, views, agents, permitlist=None, onwards_andrew_id=None):
        # Get list of students in export sheet
        values = self.client.get_values_from_sheet(
            sheet_range=EXPORT_SHEET_RANGE_R, spreadsheet_id=self.spreadsheet_id
        )

        onwards_flag = onwards_andrew_id is None

        for record in values:
            andrew_id = get_entry(record, "andrew_id", EXPORT_HEADER)
            onwards_flag = onwards_flag or andrew_id == onwards_andrew_id
            if permitlist is not None and andrew_id not in permitlist:
                continue
            if not onwards_flag:
                continue

            # Update student card view
            if "student" in agents:
                print(f"[INFO] Updating student view for {andrew_id}")
                ssid = get_entry(record, "ssid", EXPORT_HEADER)
                while True:
                    try:
                        self.client.copy_sheets_to_spreadsheet(
                            BASE_STUDENT_SPREADSHEET_ID, views, ssid, views
                        )
                        break
                    except HttpError:
                        print("[ERROR] Caught HttpError (likely rate-limit), waiting for 10s")
                        sleep(10)



            # Update TA card view
            if "ta" in agents:
                print(f"[INFO] Updating TA view for {andrew_id}")
                _ssid = get_entry(record, "_ssid", EXPORT_HEADER)
                self.client.copy_sheets_to_spreadsheet(
                    BASE_STUDENT_SPREADSHEET_ID, views, _ssid, views
                )

            set_entry(record, now(), "last_updated", EXPORT_HEADER)

        self.client.set_values_in_sheet(
            sheet_range=EXPORT_SHEET_RANGE_W,
            spreadsheet_id=self.spreadsheet_id,
            values=truncate_values(values, EXPORT_HEADER),
        )

    def sync_data(self, agents, permitlist=None, onwards_andrew_id=None):
        # Get list of variables
        variables = self.client.get_values_from_sheet(
            sheet_range=EXPORT_SHEET_RANGE_HEADER, spreadsheet_id=self.spreadsheet_id
        )[0]

        # Get list of students in export sheet
        values = self.client.get_values_from_sheet(
            sheet_range=EXPORT_SHEET_RANGE_R, spreadsheet_id=self.spreadsheet_id
        )

        onwards_flag = onwards_andrew_id is None

        for record in values:
            andrew_id = get_entry(record, "andrew_id", EXPORT_HEADER)
            onwards_flag = onwards_flag or andrew_id == onwards_andrew_id
            if permitlist is not None and andrew_id not in permitlist:
                continue
            if not onwards_flag:
                continue

            # Sync student card data
            if "student" in agents:
                print(f"[INFO] Syncing student data for {andrew_id}")

                public_variables = []
                for variable in variables:
                    if variable == "STOP":
                        # Stop syncing variables after this point
                        break
                    if variable[0] != "_":
                        public_variables.append(variable)

                entries = get_entries_across(record, public_variables, variables)
                data = list(zip(public_variables, entries))

                ssid = get_entry(record, "ssid", EXPORT_HEADER)
                while True:
                    try:
                        self.client.set_values_in_sheet(
                            sheet_range=DATA_SHEET_NAME,
                            spreadsheet_id=ssid,
                            values=data,
                            clear_range=True,
                        )
                        break
                    except HttpError:
                        print("[ERROR] Caught HttpError (likely rate-limit), waiting for 10s")
                        sleep(10)

            # Sync TA card data
            if "ta" in agents:
                print(f"[INFO] Syncing TA data for {andrew_id}")

                data = list(zip(variables, record))

                _ssid = get_entry(record, "_ssid", EXPORT_HEADER)
                self.client.set_values_in_sheet(
                    sheet_range=DATA_SHEET_NAME,
                    spreadsheet_id=_ssid,
                    values=data,
                    clear_range=True,
                )

            set_entry(record, now(), "last_updated", EXPORT_HEADER)

        self.client.set_values_in_sheet(
            sheet_range=EXPORT_SHEET_RANGE_W,
            spreadsheet_id=self.spreadsheet_id,
            values=truncate_values(values, EXPORT_HEADER),
        )

    def load_gradescope_data(self, data, sheet_name):
        print("[INFO] Uploading data to Gradecard")
        sheets = self.client.get_sheets_from_spreadsheet(self.spreadsheet_id)

        if sheet_name not in sheets:
            self.client.create_sheet_in_spreadsheet(self.spreadsheet_id, sheet_name)
        else:
            self.client.set_values_in_sheet(
                f"{sheet_name}!A1:NP", self.spreadsheet_id, [[]], clear_range=True
            )

        self.client.set_values_in_sheet(
            f"{sheet_name}!A1", self.spreadsheet_id, data, clear_range=True
        )


class GradescopeService:
    def __init__(self):
        self.client = GradescopeClient()
        self.gcp_service = GoogleCloudService()

    def get_configs(self):
        # Fetch list of config files
        try:
            config_files = [i for i in os.listdir(CONFIG_PATH) if i.endswith(".ini")]
        except FileNotFoundError:
            return []

        # Get names for config files
        configs = []
        for config_file in config_files:
            config = configparser.ConfigParser()
            config.read(os.path.join(CONFIG_PATH, config_file))
            try:
                name = config["overview"]["name"]
            except KeyError:
                continue

            configs.append({"name": name, "value": config_file})

        # Sort configs
        configs.sort(
            key=lambda config: map(
                lambda s: int(s) if s.isdigit() else s, config["name"].split(" ")
            )
        )

        return configs

    def read_config(self, config):
        # Load config file
        config_dict = configparser.ConfigParser()
        config_dict.read(os.path.join(CONFIG_PATH, config))

        try:
            # Read initial name info
            config_data = {
                "name": config_dict["overview"]["name"],
                "cyu": config_dict["overview"]["cyu"],
                "num_questions": config_dict.getint(
                    "overview", "num_questions", fallback=0
                ),
                "gsheet_name": config_dict["overview"]["gsheet_name"],
                "questions": [],
            }

            # Read question data
            questions = [
                f"question{i}" for i in range(1, 1 + config_data["num_questions"])
            ]
            for question in questions:
                if question in config_dict:
                    config_data["questions"].append(
                        {
                            "name": config_dict[question]["name"],
                            "star_name": config_dict[question].get("star_name", None),
                        }
                    )
                else:
                    config_data["questions"].append(None)
        except KeyError:
            raise ValueError("Malformed Configuration")

        return config_data

    def load_data_from_config(self, config):
        try:
            config_data = self.read_config(config)
        except ValueError:
            print(f"[ERROR] {config} is malformed")
            return

        # Fetch assignment data
        print(f"[INFO] Fetching data for {config}")
        try:
            assignment_data = self.get_assignment_evaluations(config_data)
        except KeyError as e:
            assignment_data = {}
            print(f"[ERROR] Fetching data failed for {config}")

        # Fetch CYU data
        if config_data["cyu"]:
            print(f"[INFO] Fetching CYU data for {config}")
            try:
                cyu_data = self.get_cyu_evaluations(config_data)
            except KeyError:
                cyu_data = {}
                print(f"[ERROR] Fetching CYU data failed for {config}")

        # Generate CSV file
        print("[INFO] Generating CSV file")
        data = self.combine_assignment_and_cyu_data(
            assignment_data,
            config_data["num_questions"],
            cyu_data,
        )

        # Convert CSV to text
        with io.StringIO() as csvfile:
            fieldnames = ["Andrew ID", "Submission Time", "CYU Quiz Score"]
            question_fieldnames = [
                [
                    f"Problem {i} Score",
                    f"Problem {i} TA",
                    f"Problem {i} Name",
                    f"Problem {i} ⭐",
                    f"Problem {i} Comments",
                ]
                for i in range(1, 1 + config_data["num_questions"])
            ]
            for question in question_fieldnames:
                fieldnames.extend(question)

            csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

            csvwriter.writeheader()
            for line in data:
                csvwriter.writerow(line)

            csvfile.seek(0)

            csvreader = csv.reader(csvfile)
            data = [line for line in csvreader]

        # Upload data
        self.gcp_service.load_gradescope_data(data, config_data["gsheet_name"])

    def get_question_names_for_question(self, question, all_question_names):
        data = []

        for q in all_question_names:
            try:
                colon = q.index(":")
                paren = q.index("(")
            except ValueError:
                continue

            if q[colon + 1 : paren].strip().startswith(question):
                data.append(q)

        if len(data) == 0:
            raise KeyError("No Matching Question Found")

        return data

    def get_question_data_for_question(self, question_names, q_evaluation):  # TODO
        tas = ";".join(
            self.get_question_tas_for_question(q_evaluation[q])
            for q in question_names
            if self.get_question_tas_for_question(q_evaluation[q]) is not None
        )

        return {
            "score": sum(
                round_to_hundredths(q_evaluation[q]["score"]) for q in question_names
            ),
            "TA": tas,
            "comments": ";".join(q_evaluation[q]["comment"] for q in question_names),
        }

    def get_question_tas_for_question(self, q_evaluation):  # TODO
        for key, value in q_evaluation["rubric_items"].items():
            if key.startswith("Grader") and value:
                try:
                    paren = key.index("(")
                except ValueError:
                    continue

                return key[paren + 1 : paren + 3]

        return None

    def get_assignment_evaluations(self, config_data):
        assignment = self.client.get_assignment_by_name(config_data["name"])

        if not assignment["published"]:
            if not prompt_confirm_unpublished(assignment["name"]):
                print(f"[INFO] Skipping {assignment['name']}")
                return {}

        evaluation_data = self.client.get_evaluation_data_by_assignment_id(
            assignment["id"]
        )
        if len(evaluation_data) == 0:
            return {}

        all_questions = []
        for q in range(config_data["num_questions"]):
            if config_data["questions"][q] is None:
                continue

            all_questions.append(config_data["questions"][q]["name"])
            if config_data["questions"][q]["star_name"]:
                all_questions.append(config_data["questions"][q]["star_name"])

        # Get map of question from config to question name(s) on Gradescope
        all_question_data = list(evaluation_data[0]["questions"].keys())
        map_question_to_question_names = {
            q: self.get_question_names_for_question(q, all_question_data)
            for q in all_questions
        }

        evaluations = {}

        for evaluation in evaluation_data:
            if evaluation["Status"] != "Graded":
                continue

            current_evaluation = {
                "Submission Time": evaluation["Submission Time"],
                "questions": [],
            }

            # Read each question
            for q in range(config_data["num_questions"]):
                q_config = config_data["questions"][q]
                if q_config is None:
                    current_evaluation["questions"].append(None)
                    continue

                star = False
                data = self.get_question_data_for_question(
                    map_question_to_question_names[q_config["name"]],
                    evaluation["questions"],
                )

                if data["score"] < STAR_THRESHOLD and q_config["star_name"]:
                    star_data = self.get_question_data_for_question(
                        map_question_to_question_names[q_config["star_name"]],
                        evaluation["questions"],
                    )

                    # Take star marked question
                    if star_data["score"] >= STAR_THRESHOLD:
                        star = True
                        data = star_data

                current_evaluation["questions"].append(data)
                current_evaluation["questions"][q]["name"] = (
                    q_config["star_name"] if star else q_config["name"]
                )
                current_evaluation["questions"][q]["star"] = star

            evaluations[evaluation["Email"]] = current_evaluation

        return evaluations

    def get_cyu_evaluations(self, config_data):
        assignment = self.client.get_assignment_by_name(config_data["cyu"])

        if not assignment["published"]:
            if not prompt_confirm_unpublished(assignment["name"]):
                print(f"[INFO] Skipping {assignment['name']}")
                return {}

        evaluation_data = self.client.get_evaluation_data_by_assignment_id(
            assignment["id"]
        )

        return {
            evaluation["Email"]: round_to_hundredths(evaluation["Total Score"])
            for evaluation in evaluation_data
            if evaluation["Status"] == "Graded"
        }

    def combine_assignment_and_cyu_data(self, assignment_data, num_questions, cyu_data):
        # Find all submissions
        all_emails = set(assignment_data) | set(cyu_data)
        data = []

        for email in all_emails:
            current = {"Andrew ID": email.split("@")[0]}

            if email in assignment_data:
                evaluation = assignment_data[email]
                current["Submission Time"] = evaluation["Submission Time"]

                for q in range(num_questions):
                    current_q = evaluation["questions"][q]
                    if current_q is None:
                        continue

                    current[f"Problem {q+1} Score"] = current_q["score"]
                    current[f"Problem {q+1} TA"] = current_q["TA"]
                    current[f"Problem {q+1} Name"] = current_q["name"]
                    current[f"Problem {q+1} ⭐"] = current_q["star"]
                    current[f"Problem {q+1} Comments"] = current_q["comments"]

            if email in cyu_data:
                current["CYU Quiz Score"] = cyu_data[email]

            data.append(current)

        return data
