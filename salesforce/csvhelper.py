"""Converts objects to and from CSV"""

import csv

#maps a csv to a list of objects with the csv columns as the attribute names
def csv_to_objects(csv_file, object):
    """Converts csv to objects

    Args:
        csv_file (file object or list(string)): csv file containing list of records to be converted to objects. Can also take a list of rows
        object (object class): class that contains instance variables that match all columns of csv
    Returns:
        list(object): list of instances of object with fields populated by csv records
    """
    reader = csv.reader(csv_file, skipinitialspace = True)
    res = []
    headers = next(reader)
    for row in reader:
        instance = object()
        for i in range(len(headers)):
            if hasattr(instance, headers[i]):
                setattr(instance, headers[i], row[i])
            else:
                raise HeaderException()
        res.append(instance)
    return res

#takes in a list of objects, returns csv
#expects all objects to be the same/have same attributes.
def objects_to_csv(objects):
    """Converts objects to a csv string.
    
    Expects all objects to be of the same class. Uses LF (\n) as the line ending, not CLRF (\r\n)

    Args:
        objects (list(obj)): list of objects to be converted
    Returns:
        str: csv string with columns representing the instance variables of the object.
    """
    res = []
    headers = list(vars(objects[0]).keys())
    for i in range(len(headers)):
        headers[i] = process_comma(headers[i])
    res.append(", ".join(headers))
    for object in objects:
        obj_values = []
        for i in range(len(headers)):
            obj_values.append(process_comma(str(getattr(object, headers[i]))))
        print(obj_values)
        res.append(", ".join(obj_values))
    return "\n".join(res)

#TODO: make this account for quotes too. And then always add a quote on each side instead of just checking. Sometimes a quote might actually be part of string
def process_comma(string):
    """Adds quotes around values that contain a comma
    
    Args:
        string: the string of the csv value
    Returns:
        str: the csv value surrounded by double quotes if it contains a comma
    """
    if ',' in string:
        if string[0] != "\"":
            string = "\"" + string
        if string[-1] != "\"":
            string = string + "\""
    return string


class HeaderException(Exception):
    """Raised when the csv header does not match the object's attributes"""

