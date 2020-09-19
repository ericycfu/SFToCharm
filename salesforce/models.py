"""Contains the object models used for the ORM functionality"""

from abc import ABC, abstractmethod

#give each SFObject instance variables with the same names as they have in salesforce(including capitalization)
class SFObject(ABC):
    """Base class for all Salesforce objects

    Each class you want to use as part of ORM functionality must implement this class
    """
    def __init__(self):
        """
        Attributes:
            Id (str): used to match the salesforce Id. Also used as the external Id when uploading.
        """
        self.Id = None

    def __repr__(self):
        """Returns well-formatted string representation of object"""
        s =  f"{self.__class__.get_object_type()} "
        variables = [f'{key}: {getattr(self, key)}' for key in list(vars(self).keys())]
        s += ", ".join(variables)
        return s
    
    #static method because all instances of a class return the same value
    #static method over classmethod because we don't need to access any other variables/methods in class
    @staticmethod #this needs to come first
    @abstractmethod
    def get_object_type():
        """Returns the API name of a salesforce object. Can be found in setup->object manager"""
        pass

class SFTempAccount(SFObject):
    def __init__(self):
        super().__init__()
        self.Name__c = None
        self.Phone__c = None
        self.Primary_Email__c = None

    @staticmethod
    def get_object_type():
        return "TempAccount__c"
    
class SFTempContact(SFObject):
    def __init__(self):
        super().__init__()
        self.FirstName__c = None
        self.LastName__c = None
        self.BirthDate__c = None
        self.Gender__c = None
        self.TempAccount__c = None

    @staticmethod
    def get_object_type():
        return "TempContact__c"

class CharmPatient():
    def __init__(self, first_name, last_name, dob, gender, phone, email):
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.gender = gender
        self.phone = phone
        self.email = email