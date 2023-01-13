EXPORT_SHEET_NAME = "export"
EXPORT_SHEET_RANGE_R = f"{EXPORT_SHEET_NAME}!A3:NP"  # haha, easter egg
EXPORT_SHEET_RANGE_W = f"{EXPORT_SHEET_NAME}!A3:E"
EXPORT_SHEET_RANGE_HEADER = f"{EXPORT_SHEET_NAME}!1:1"
EXPORT_HEADER = ["andrew_id", "email", "ssid", "_ssid", "last_updated"]

ROSTER_SHEET_NAME = "roster"
ROSTER_SHEET_RANGE_W = f"{ROSTER_SHEET_NAME}!A2:NP"
ROSTER_HEADER = [
    "Semester",
    "Course",
    "Section",
    "Lecture",
    "Mini",
    "Last Name",
    "Preferred/First Name",
    "MI",
    "Andrew ID",
    "Email",
    "College",
    "Department",
    "Major",
    "Class",
    "Graduation Semester",
    "Units",
    "Grade Option",
    "QPA Scale",
    "Mid-Semester Grade",
    "Primary Advisor",
    "Final Grade",
    "Default Grade",
    "Time Zone Code",
    "Time Zone Description",
    "Added By",
    "Added On",
    "Confirmed",
    "Waitlist Position",
    "Units Carried/Max Units",
    "Waitlisted By",
    "Waitlisted On",
    "Dropped By",
    "Dropped On",
    "Roster As Of Date",
]

USER_ENTERED = "USER_ENTERED"

DATA_SHEET_NAME = "Data"
CARD_VIEWS = ["Dashboard", "Scores"]
CARD_SHEETS = CARD_VIEWS + [DATA_SHEET_NAME]

CARD_SHEETS_TO_DELETE = [f"Copy of {sheet}" for sheet in CARD_VIEWS]

MAP_ACTION_TO_ATTRIBUTE = {
    "Add students": ("GoogleCloudResource", "post_add_new_students"),
    "Create cards": ("GoogleCloudResource", "post_create_cards"),
    "Update views": ("GoogleCloudResource", "post_update_card_views"),
    "Sync data": ("GoogleCloudResource", "post_update_card_data"),
    "Load Gradescope data": ("GradescopeResource", "post_load_data"),
}

ROSTER_PATH = "roster"
CONFIG_PATH = "config"

STAR_THRESHOLD = 0.01
