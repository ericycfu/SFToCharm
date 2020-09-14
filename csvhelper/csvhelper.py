import csv

#maps a csv to a list of objects
def csv_to_object(csv_file, object):
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




class HeaderException(Exception):
    """Raised when the csv header does not match the object's attributes"""

