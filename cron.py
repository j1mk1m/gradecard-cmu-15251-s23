#!/usr/bin/env python3
from resource import GradescopeResource


def main():
    # Run Gradescope autopull
    gradescope_resource = GradescopeResource()
    gradescope_resource.post_load_data(load_all_data=True)


if __name__ == "__main__":
    main()
