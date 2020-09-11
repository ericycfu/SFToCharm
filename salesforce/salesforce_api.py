import aiohttp
import asyncio

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
        async with self.session.post(url, params = self.auth_params) as response:
            r = await response.json()
            token = r["access_token"]
            self.session.headers = {"Authorization": f"Bearer {token}"}
            self.instance_url = r["instance_url"]

    async def create_job(self, object_type, operation, externalId = None):
        '''
        externalIdFieldName - required for upsert operations
        object - object type for data, single type per job
        operation - insert, delete, update, upsert
        '''
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest"
        params = {}
        print(self.session.headers)
        print(url)
        async with self.session.post(url, params = params) as response:
            r = await response.json()
            print(r)
            return r['id']


    async def delete_job(self, job_id):
        url = self.instance_url + f"/services/data/v{self.api_version}/jobs/ingest/{job_id}"
        async with self.session.delete(url) as response:
            assert response.status == 204 #indicates job was successfully deleted



    async def close_session(self):
        await self.session.close()
