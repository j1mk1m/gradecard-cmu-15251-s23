#!/usr/bin/env python3
from cli import prompt_action
from constants import MAP_ACTION_TO_ATTRIBUTE
import resource


def main():
    action = prompt_action()
    resource_name, attribute = MAP_ACTION_TO_ATTRIBUTE[action]

    resource_inst = resource.__getattribute__(resource_name)()
    resource_inst.__getattribute__(attribute)()


if __name__ == "__main__":
    main()
