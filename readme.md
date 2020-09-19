
# SFToCharm

Used to import members from Salesforce into ChARM EHR. Contains custom Salesforce ORM with aiohttp wrapper for Salesforce API.

## Usage
Run main.py

## Salesforce ORM Usage
Initialize instance of SalesForceSession, passing in the required information.
```python
sf_lib = SalesForceSession(client_id, client_secret, username, password)
await sf_lib.get_token()
```
Create an object that inherits from SFObject containing the fields of records you want to retrieve/upload. Implement `get_object_type` which returns the API name of the object.
```python
class SFAccount(SFObject):
    def __init__(self):
        super().__init__()
        self.Name = None
        self.Phone = None
        self.Primary_Email__c = None
        
    @staticmethod
    def get_object_type():
        return "Account"
```
To get all records of a certain object
```python
accounts = await sf_lib.get_all_objects_of_type(SFAccount)
```
Returns list of SFAccount objects with attributes filled in.
```
Account Id: 0016A00002TXwRAVA1, Name: Doe, John, Phone: 123-456-7890, Primary_Email__c: ex1@example.com
Account Id: 0017A00002BWwRAQZ1, Name: Smith, John, Phone: 111-111-1111, Primary_Email__c: ex2@example.com
Account Id: 0014A00002PDwJKQA1, Name: Doe, Jane, Phone: 222-222-2222, Primary_Email__c: ex3@example.com
```
To upsert object records, create a list of objects you want to upsert with attributes filled in.
```python
accounts = [...]
new_accounts = await sf_lib.perform_bulk_upsert(accounts)
```
new_accounts contains the same account objects, but with the Id field now containing the Id Salesforce assigns to the record.
## TODO

 - Implement bulk delete
 - Implement custom mapping for attributes
 - Implement custom external ID
## Dependencies
 - selenium
 - geckodriver exe file
 - aiohttp
 - asyncio