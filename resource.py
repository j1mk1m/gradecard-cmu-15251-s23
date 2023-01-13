import csv

from cli import prompt_roster, prompt_views, prompt_students, prompt_configs
from service import GoogleCloudService, GradescopeService


class GoogleCloudResource:
    def __init__(self):
        self.service = GoogleCloudService()

    def post_add_new_students(self):
        try:
            roster_path = prompt_roster()
        except IndexError:
            raise FileNotFoundError("No CSV Rosters Found") from None

        with open(roster_path) as f:
            roster = csv.reader(f)
            next(roster)  # ignore header
            self.service.add_students(roster)

    def post_create_cards(self):
        agents = ["student"]
        self.service.create_cards(agents)

    def post_update_card_data(self):
        agents = ["student"]
        students, onwards = prompt_students()
        self.service.sync_data(agents, students, onwards)

    def post_update_card_views(self):
        views = prompt_views()
        agents = ["student"]
        students, onwards = prompt_students()
        self.service.update_views(views, agents, students, onwards)


class GradescopeResource:
    def __init__(self):
        self.service = GradescopeService()

    def post_load_data(self, load_all_data=False):
        all_configs = self.service.get_configs()

        if len(all_configs) == 0:
            raise FileNotFoundError("No Homework Configs Found") from None

        if not load_all_data:
            configs = prompt_configs(all_configs)
        for config in configs:
            self.service.load_data_from_config(config)
