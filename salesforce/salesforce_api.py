import aiohttp
import asyncio
from csvhelper.csvhelper import csv_to_object

class SalesForceSession():
    def __init__(self, client_id, client_secret, username, password):
        self.session = aiohttp.ClientSession()
        self.auth_params = {"grant_type": "password", 
                "client_id": client_id, 
                "client_secret" : client_secret, 
                "username": username,
                "password": password}
        self.instance_url = None
        self.api_version = "49.0"

    async def get_token(self):
        url = "https://login.salesforce.com/services/oauth2/token"
        #params is used to pass these as query string parameters. 
        async with self.session.post(url, params = self.auth_params) as response:
            r = await response.json()
            token = r["access_token"]
            #using session.headers doesn't throw error (because it creates a 'header' attribute even it if doesn't exist) but it doesn't work.
            self.session._default_headers = {"Authorization": f'Bearer {token}', 
                                    'content-type': 'application/json'}     
            self.instance_url = r["instance_url"]
            print(token)
            print(self.instance_url)
    

    def get_query_string_fields(self, object):
        instance_variables = list(vars(object()).keys())
        return ', '.join(instance_variables)

    #TODO: doesn't work
    async def get_all_objects_of_type(self, object):
        #create query
        create_url = self.instance_url + f'/services/data/v{self.api_version}/jobs/query'
        query = f"SELECT {self.get_query_string_fields(object)} FROM {object.get_object_type()}"
        body = {"operation": "query", "query": query}
        #json is used to send the body of the request
        async with self.session.post(create_url, json = body) as response:
            r = await response.json()
            job_id = r['id']
            print(job_id)
        #monitor query status, until job complete
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
            print('results successfully retrieved')
            return csv_to_object(r.splitlines(), object)

    #TODO: doesn't work
    async def create_job(self, object_type, operation, externalId = None):
        '''
        externalIdFieldName - required for upsert operations
        object - object type for data, single type per job
        operation - insert, delete, update, upsert
        '''
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest"
        params = {'object': object_type, 'operation': operation}
        print(url)
        async with self.session.post(url, params = params) as response:
            r = await response.json()
            print(r)
            return r['id']

    #TODO: not sure if works
    async def delete_job(self, job_id):
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}"
        async with self.session.delete(url) as response:
            assert response.status == 204 #indicates job was successfully deleted

    

    async def close_session(self):
        await self.session.close()
