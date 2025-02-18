import asyncio
import httpx

class ModelDerivativesClient:
    def __init__(self, access_token: str, host: str = "https://developer.api.autodesk.com"):
        self.client = httpx.AsyncClient()
        self.access_token = access_token
        self.host = host

    async def _get(self, endpoint: str) -> dict:
        response = await self.client.get(f"{self.host}/{endpoint}", headers={"Authorization": f"Bearer {self.access_token}"})
        while response.status_code == 202:
            await asyncio.sleep(1)
            response = await self.client.get(f"{self.host}/{endpoint}", headers={"Authorization": f"Bearer {self.access_token}"})
        if response.status_code >= 400:
            raise Exception(response.text)
        return response.json()

    async def list_model_views(self, urn: str) -> dict:
        json = await self._get(f"modelderivative/v2/designdata/{urn}/metadata")
        return json["data"]["metadata"]

    async def fetch_object_tree(self, urn: str, model_guid: str) -> dict:
        json = await self._get(f"modelderivative/v2/designdata/{urn}/metadata/{model_guid}")
        return json["data"]["objects"]

    async def fetch_all_properties(self, urn: str, model_guid: str) -> dict:
        json = await self._get(f"modelderivative/v2/designdata/{urn}/metadata/{model_guid}/properties")
        return json["data"]["collection"]