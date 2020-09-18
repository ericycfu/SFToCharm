from abc import ABC, abstractmethod

#give each SFObject instance variables with the same names as they have in salesforce(including capitalization)
class SFObject(ABC):
    def __init__(self):
        self.Id = None

    def __repr__(self):
        s =  f"{self.__class__.get_object_type()} "
        variables = [f'{key}: {getattr(self, key)}' for key in list(vars(self).keys())]
        s += ", ".join(variables)
        return s
    
    @staticmethod #this needs to come first
    @abstractmethod
    def get_object_type():
        pass

class SFTempAccount(SFObject):
    def __init__(self):
        super().__init__()
        self.Name__c = None

    @staticmethod
    def get_object_type():
        return "TempAccount__c"
    
class SFAccount(SFObject):
    def __init(self):
        super().__init__()
        self.Name = None

    @staticmethod
    def get_object_type():
        return "Account"