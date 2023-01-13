from PyInquirer import prompt
import glob
import os

from constants import MAP_ACTION_TO_ATTRIBUTE, CARD_VIEWS, ROSTER_PATH


def prompt_action():
    questions = [
        {
            "type": "list",
            "name": "action",
            "message": "What action would you like to perform?",
            "choices": MAP_ACTION_TO_ATTRIBUTE.keys(),
        },
    ]
    answers = prompt(questions)
    return answers["action"]


def prompt_roster():
    questions = [
        {
            "type": "list",
            "name": "file",
            "message": "Which roster do you want to sync?",
            "choices": glob.glob("*.csv") + glob.glob(f"{ROSTER_PATH}/*.csv"),
        },
    ]
    answers = prompt(questions)
    return answers["file"]


def prompt_views():
    questions = [
        {
            "type": "checkbox",
            "name": "views",
            "message": "Which sheet views do you want to update?",
            "choices": [{"name": sheet} for sheet in CARD_VIEWS],
        },
    ]
    answers = prompt(questions)
    return answers["views"]


def prompt_agents():
    questions = [
        {
            "type": "checkbox",
            "name": "agents",
            "message": "Which agents' cards do you want to update?",
            "choices": [
                {"name": "student"},
                {"name": "ta"},
            ],
        },
    ]
    answers = prompt(questions)
    return answers["agents"]


def prompt_students():
    questions = [
        {
            "type": "input",
            "name": "students",
            "message": "Which students' cards do you want to update?",
        }
    ]
    answers = prompt(questions)
    if len(answers["students"]) == 0:
        return None, None
    elif answers["students"].endswith("..."):
        return None, answers["students"][:-3]
    else:
        return [student.strip() for student in answers["students"].split(",")], None


def prompt_configs(configs):
    questions = [
        {
            "type": "checkbox",
            "name": "configs",
            "message": "Which assignments to pull grade data for?",
            "choices": configs,
        }
    ]
    answers = prompt(questions)
    return answers["configs"]


def prompt_confirm_unpublished(assignment):
    if "GC_HEADLESS" in os.environ and "true" in os.environ["GC_HEADLESS"].lower():
        return True

    questions = [
        {
            "type": "confirm",
            "name": "pull",
            "message": f"Are you sure you want to pull grades for unpublished assignment {assignment}?",
            "default": False,
        }
    ]
    answers = prompt(questions)
    return answers["pull"]
