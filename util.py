from datetime import datetime as dt
import time


def get_entry(record, column_name, columns):
    i = columns.index(column_name)
    return record[i]


def get_entries_across(record, column_names, columns):
    result = []
    for value, column in zip(record, columns):
        if column in column_names:
            result.append(value)
    return result


def get_entries(records, column_name, columns):
    i = columns.index(column_name)
    return [list(record)[i] for record in records]


def set_entry(record, value, column_name, columns):
    i = columns.index(column_name)
    record[i] = value


def set_entries_across(record, map_column_name_to_value, columns):
    for column_name, value in map_column_name_to_value.items():
        i = columns.index(column_name)
        record[i] = value


def set_entries(records, values, column_name, columns):
    i = columns.index(column_name)
    for (record, value) in zip(records, values):
        record[i] = value


def truncate_values(values, header):
    max_length = len(header)
    return [record[:max_length] for record in values]


def now():
    return str(dt.now())


def round_to_hundredths(num):
    return round(num * 100) / 100
