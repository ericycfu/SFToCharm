import csv

#maps a csv to a list of objects with the csv columns as the attribute names
def csv_to_objects(csv_file, object):
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
    res = [] #list containing each csv line as a string
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



def process_comma(string):
    if ',' in string:
        if string[0] != "\"":
            string = "\"" + string
        if string[-1] != "\"":
            string = string + "\""
    return string


class HeaderException(Exception):
    """Raised when the csv header does not match the object's attributes"""

