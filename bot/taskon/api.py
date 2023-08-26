from functools import wraps
from typing import Any

from better_automation import BetterHTTPClient
import aiohttp

from .models import UserInfo, CampaignInfo, CampaignStatusInfo, UserCampaignStatus


TWITTER_BIND_INFO = {
    'response_type': 'code',
    'client_id': 'aTk5eEUxZlpvak1RYU9yTEZhZ0M6MTpjaQ',
    'scope': 'tweet.read users.read follows.read like.read offline.access',
    'code_challenge': 'challenge',
    'code_challenge_method': 'plain',
    'redirect_uri': 'https://taskon.xyz/twitter',
}

DISCORD_BIND_INFO = {
    'client_id': '986938000388796468',
    'response_type': 'code',
    'scope': 'identify guilds guilds.members.read',
    # 'redirect_uri': 'https://taskon.xyz/discord',
}


class TaskonError(Exception):
    pass


class TaskonAPI(BetterHTTPClient):

    def __init__(self, session: aiohttp.ClientSession, auth_token: str = None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._auth_token = None
        if auth_token:
            self.set_auth_token(auth_token)

    def set_auth_token(self, auth_token: str):
        self._auth_token = auth_token
        self._headers.update({'authorization': auth_token})

    @property
    def auth_token(self) -> str | None:
        return self._auth_token

    @staticmethod
    def check_auth_token(coro):
        @wraps(coro)
        async def wrapper(self, *args, **kwargs):
            if not self.auth_token:
                raise TaskonError("auth_token is required for this request")
            return await coro(self, *args, **kwargs)

        return wrapper

    async def handle_response(self, response: aiohttp.ClientResponse) -> Any:
        response_json = await response.json()
        error = response_json["error"]
        if error is not None:
            raise TaskonError(error)
        return response_json["result"]

    @check_auth_token
    async def request_user_info(self) -> UserInfo:
        url = 'https://api.taskon.xyz/v1/getUserInfo'
        response = await self.request('POST', url)
        result = await self.handle_response(response)
        return UserInfo(**result)

    async def request_campaign_info(self, campaign_id: int) -> CampaignInfo:
        url = 'https://api.taskon.xyz/v1/getCampaignInfo'
        data = str(campaign_id)
        response = await self.request('POST', url, data=data)
        result = await self.handle_response(response)
        return CampaignInfo(**result)

    async def request_campaign_status_info(self, campaign_id: int) -> CampaignStatusInfo:
        url = 'https://api.taskon.xyz/v1/getCampaignStatusInfo'
        payload = {'id': campaign_id}
        response = await self.request('POST', url, json=payload)
        result = await self.handle_response(response)
        return CampaignStatusInfo(**result)

    @check_auth_token
    async def request_user_campaign_status(self, campaign_id: int) -> UserCampaignStatus:
        url = 'https://api.taskon.xyz/v1/getUserCampaignStatus'
        data = str(campaign_id)
        response = await self.request('POST', url, data=data)
        result = await self.handle_response(response)
        return UserCampaignStatus(**result)

    async def check_user_campaign_eligibility(self, campaign_id: int) -> bool:
        url = 'https://api.taskon.xyz/v1/checkUserCampaignEligibility'
        data = str(campaign_id)
        response = await self.request('POST', url, data=data)
        result = await self.handle_response(response)
        return result["result"]

    async def request_nonce(self) -> str:
        url = 'https://api.taskon.xyz/v1/requestChallenge'
        payload = {
            'ver': '1.0',
            'type': 'ClientHello',
            'action': 0,
        }
        response = await self.request('POST', url, json=payload)
        result = await self.handle_response(response)
        return result['nonce']

    async def request_auth_token(
            self,
            address: str,
            signature: str,
            nonce: str,
            timestamp: int,
            invite_code: str = None,
    ) -> str:
        url = 'https://api.taskon.xyz/v1/submitChallenge'
        did = address.replace('0x', 'did:etho:')
        payload = {
            "ver": "1.0",
            "type": "ClientResponse",
            "nonce": nonce,
            "did": did,
            "proof": {
                "type": "ES256",
                "verificationMethod": f"{did}#key-1",
                "created": timestamp,
                "value": signature
            },
            "VPs": [],
            'invite_code': invite_code if invite_code else '',
        }
        response = await self.request('POST', url, json=payload)
        result = await self.handle_response(response)
        return result['token']

    async def submit_task(self, task_id: int, value: str = None, pre_submit: bool = False) -> bool:
        url = "https://api.taskon.xyz/v1/submitTask"
        payload = {
            "task_id": task_id,
            "value": value if value else "",
            "pre_submit": pre_submit
        }
        response = await self.request('POST', url, json=payload)
        return await self.handle_response(response)

    async def submit_campaign(self, campaign_id: int, g_captcha_response: str = None) -> bool:
        url = "https://api.taskon.xyz/v1/submitCampaign"
        payload = {
            "campaign_id": campaign_id,
            "auto_follow_owner": False
        }
        if g_captcha_response: payload["google_recaptcha"] = g_captcha_response
        response = await self.request('POST', url, json=payload)
        return await self.handle_response(response)

    @check_auth_token
    async def request_twitter_bind_state(self) -> str:
        url = 'https://api.taskon.xyz/v1/requestTwitterAuthState'
        response = await self.request('POST', url)
        return await self.handle_response(response)

    @check_auth_token
    async def bind_app(self, app_type: str, bind_code: str):
        url = "https://api.taskon.xyz/v1/bindSNS"
        payload = {
            "sns_type": app_type,
            "token": bind_code,
        }
        response = await self.request('POST', url, json=payload)
        await self.handle_response(response)

    async def bind_twitter(self, bind_code: str):
        await self.bind_app("Twitter", bind_code)

    async def bind_discord(self, bind_code: str):
        await self.bind_app("Discord", bind_code)
