'''Async Wrapper for the Salesforce API'''
import aiohttp
import asyncio
from salesforce.csvhelper import csv_to_objects, objects_to_csv, process_sf_response, get_object_ids

class SalesForceSession():
    """Represents a connection to a specific Salesforce Instance"""

    def __init__(self, client_id, client_secret, username, password):
        """
        Args:
            client_id (str): the client id associated with application
            client_secret (str): the client secret associated with an application
            username (str): username of the user that the app is imitating
            password (str): password of the user the app is imiatating. The security token should be appended to the end

        Attributes:
            session (aiohttp.ClientSession) : client session used for all http requests
            auth_params (dict): authentication parameters used for oauth flow
            instance_url (string): the unique base URL corresponding to a salesforce instance
            api_version (string): the version of the API you are using.
        """

        self.session = aiohttp.ClientSession()
        self.auth_params = {"grant_type": "password", 
                "client_id": client_id, 
                "client_secret" : client_secret, 
                "username": username,
                "password": password}
        self.instance_url = None
        self.api_version = "49.0"

    async def get_token(self):
        """Performs Authentication for the session.
        
        Uses the OAuth2.0 Username-Password flow to obtain a bearer token and add it to the header
        Should always be called after initializing an instance of SalesForceSession
        """

        url = "https://login.salesforce.com/services/oauth2/token"
        #params is used to pass these as query string parameters. 
        async with self.session.post(url, params = self.auth_params) as response:
            r = await response.json()
            token = r["access_token"]
            #using session.headers doesn't throw error (because it creates a 'header' attribute even it if doesn't exist) but it doesn't work.
            self.session._default_headers = {"Authorization": f'Bearer {token}'}     
            self.instance_url = r["instance_url"]
    
    def get_query_string_fields(self, object):
        """Generates comma-separated list of fields for an object query

        Args:
            object (SFObject class): The object the query is being performed on.
        Returns:
            string: comma-separate list of the SFOBject's attributes
        """

        instance_variables = list(vars(object()).keys())
        return ', '.join(instance_variables)

    async def get_all_objects_of_type(self, object):
        """Retreives all Salesforce objects of a specific type
        
        Args: 
            object (SFObject class): Type of object to be retreived
        Returns:
            list(SFObject): List of all SFObjects of that type 
        """

        #create query
        create_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/query'
        query = f"SELECT {self.get_query_string_fields(object)} FROM {object.get_object_type()}"
        body = {"operation": "query", "query": query}
        async with self.session.post(create_url, json = body) as response:
            r = await response.json()
            job_id = r['id']

        #monitor query status until job complete
        monitor_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/query/{job_id}'
        while True:
            async with self.session.get(monitor_url) as response:
                r = await response.json()
                status = r['state']
                print(status)
                if status not in ['JobComplete', 'Failed', 'Aborted']:
                    await asyncio.sleep(2)
                elif status in ['Failed', 'Aborted']:
                    raise Exception('something went wrong with the SF query')
                elif status == 'JobComplete':
                    break

        #get results
        get_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/query/{job_id}/results'
        async with self.session.get(get_url) as response:
            r = await response.text()
            return csv_to_objects(r.splitlines(), object)

    async def perform_bulk_upsert(self, objects):
        """Upserts all objects

        Requires that all objects be of the same type

        Args:
            objects (list of SFObject): All records that you would like to upsert
        Returns:
            str: csv response containing the records of the objects upserted
        """

        #create csv from objects
        csv_string = objects_to_csv(objects)

        #create job
        object_class = objects[0].__class__
        job_id = await self.create_job(object_class, 'upsert')

        #upload csv data to job
        upload_url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}/batches/"
        headers = {'Content-Type': 'text/csv', 'Accept': 'application/json'}
        async with self.session.put(upload_url, data = csv_string, headers = headers) as response:
            assert response.status == 201 #data was succesfully received.
        
        #close job
        await self.close_job(job_id)

        #check job status and results
        monitor_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/ingest/{job_id}'
        while True:
            async with self.session.get(monitor_url) as response:
                r = await response.json()
                status = r['state']
                print(status)
                if status not in ['JobComplete', 'Failed']:
                    await asyncio.sleep(2)
                elif status in ['Failed', 'Aborted']:
                    #not raising exception here because we can still get data of which records were succesfully processed
                    print("something went wrong with job")
                    await self.get_failed_job(job_id)
                    break
                elif status == 'JobComplete':
                    break

        #get processed jobs:
        results_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/ingest/{job_id}/successfulResults/'
        async with self.session.get(results_url) as response:
            r = await response.text()
            #convert returned csv back to objects -> now they contain the salesforce id in Id field
            return csv_to_objects(process_sf_response(r), object_class)

    #TODO: implement this
    async def perform_bulk_delete(self, objects):

        #create csv
        csv_string = get_object_ids(objects)


        #create job
        object_class = objects[0].__class__
        job_id = await self.create_job(object_class, 'delete')

        #upload csv data to job
        upload_url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}/batches/"
        headers = {'Content-Type': 'text/csv', 'Accept': 'application/json'}
        async with self.session.put(upload_url, data = csv_string, headers = headers) as response:
            assert response.status == 201 #data was succesfully received.

        #close job
        await self.close_job(job_id)

        #check job status and results
        monitor_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/ingest/{job_id}'
        while True:
            async with self.session.get(monitor_url) as response:
                r = await response.json()
                status = r['state']
                print(status)
                if status not in ['JobComplete', 'Failed']:
                    await asyncio.sleep(2)
                elif status in ['Failed', 'Aborted']:
                    #not raising exception here because we can still get data of which records were succesfully processed
                    print("something went wrong with job")
                    await self.get_failed_job(job_id)
                    break
                elif status == 'JobComplete':
                    break

        #get processed jobs:
        results_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/ingest/{job_id}/successfulResults/'
        async with self.session.get(results_url) as response:
            r = await response.text()
            print(r)
            #objects should be deleted so there is nothing to return

    async def create_job(self, object, operation):
        """Creates a job
        
        Args:
            object (SFObject class): object type for job, single type per job
            operation (str): operation of the job - one of insert, delete, update, upsert
        Returns:
            str: Id of the job
        """

        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest"
        body = {'object': object.get_object_type(), 
                'contentType': 'CSV', 
                'operation': operation, 
                "lineEnding": "LF",
                "externalIdFieldName": "Id" }
        async with self.session.post(url, json = body) as response:
            r = await response.json()
            #could just return contentUrl, but returning id is better since it can be used in delete_job
            return r['id']

    async def get_failed_job(self, job_id):
        """Retrieves the failed results of a job

        Args:
            job_id (str): the id of the failed job
        Returns:
            str: csv records of the failed jobs
        """
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}/failedResults/"
        async with self.session.get(url) as response:
            r = await response.text()
            return r

    async def abort_job(self, job_id):
        """Aborts an ongoing job

        Args:
            job_id (str): the id of the job to abort
        """
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}"
        body = {"state": "Aborted"}
        async with self.session.patch(url, json = body) as response:
            r = await response.json()
            print(r)

    async def close_job(self, job_id):
        """Closes a job
        
        Args:
            job_id (str): the id of the job to close
        """
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}"
        body = {"state": "UploadComplete"}
        async with self.session.patch(url, json = body) as response:
            pass
            #r = await response.json()
            #print(r)

    async def delete_job(self, job_id):
        """Deletes a job

        The job must have a status of UploadComplete, JobComplete, Aborted, or Failed
        Args:
            job_id (str): the id of the job to delete
        """
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}"
        async with self.session.delete(url) as response:
            assert response.status == 204 #indicates job was successfully deleted
            
    async def close_session(self):
        """Closes the aiohttp.ClientSession()"""
        await self.session.close()
