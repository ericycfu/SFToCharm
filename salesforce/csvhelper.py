"""Converts objects to and from CSV"""

import csv

def csv_to_objects(csv_file, object):
    """Converts csv to objects

    Args:
        csv_file (file object or list(string)): csv file containing list of records to be converted to objects. Can also take a list of rows(e.g. csv_string.splitlines())
        object (object class): class that contains instance variables that match all columns of csv
    Returns:
        list(object): list of instances of object with fields populated by csv records
    """
    #our ojbects_to_csv method contains an initial space after comma when populating each row
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

def get_object_ids(objects):
    """Gets csv of only object ids

    Accepts anything that has an Id attribute. Uses LF (\n) as the line ending, not CLRF (\r\n)

    Args:
        objects (list(obj)): list of objects with Ids
    Returns:
        str: csv string with only one Id column
    """
    res = ["Id"]
    for object in objects:
        res.append(getattr(object, "Id"))
    return "\n".join(res)

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
        headers[i] = process_string(headers[i])
    #salesforce doesn't like spaces in csv, which is why in both joins, we don't have space after comma
    res.append(",".join(headers))
    for object in objects:
        obj_values = []
        for i in range(len(headers)):
            attr_value = getattr(object, headers[i])
            if attr_value is None:
                attr_value = ""
            obj_values.append(process_string(str(attr_value)))
        res.append(",".join(obj_values))
    return "\n".join(res)

def process_string(string):
    """Processes an object attribute's string value so it can become a properly formatted as a csv
    
    Args:
        string: the string of the csv value
    Returns:
        str: the csv value, surrounding spaces removed, surrounded by quotes if contains comma, and double quotes escaped
    """
    string = string.strip()
    #escape the quotes first so the quotes aroudn the string aren't affected
    if "\"" in string:
        indices = [index for index, char, in enumerate(string) if char == "\""]
        for index in reversed(indices): #iterate backwards so we don't need to account for offset
            string = string[:index] + "\"" + string[index:]
    if ',' in string:
        string = "\"" + string + "\""
    return string

def process_sf_response(csv_string):
    """Used for format salesforce csv response after job to match be able to convert back to objects

    Salesforce csv response will first contain something like
    "sf__Id","sf__Created",Id,Name__c
    "a1O5A000004ikUOUAY","true","","Doe, John"
    Delete Id column, rename sf__Id to Id, and delete sf_Created
    TODO: sf_Created is probably false for failed jobs. Not sure how to deal with this right now.

    Args:
        csv_string: the string response returned by salesforce
    Returns:
        list(str): the each string is a record to be converted to an object. Matches expected input of csv_to_objects
    """
    csv_string = csv_string.splitlines()
    #salesforce has no spaces between values, no need for skipinitialspace
    reader = csv.reader(csv_string)
    res = []
    #each row of reader is a list of string
    headers = next(reader)
    #get indices to keep
    indices_to_keep = [i for i in range(len(headers)) if headers[i] not in ['sf__Created', 'Id']]
    #rename sf__Id, delete Id and sf__created
    for i in range(len(headers)):
        if headers[i] == "sf__Id":
            headers[i] = "Id"
            break
    processed_headers = [headers[i] for i in indices_to_keep]
    res.append(",".join(processed_headers))
    for row in reader:
        processed_row = [row[i] for i in indices_to_keep]
        res.append(",".join(processed_row))
    return res


class HeaderException(Exception):
    """Raised when the csv header does not match the object's attributes"""

