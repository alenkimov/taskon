import time
from contextlib import asynccontextmanager

import aiohttp
from better_automation.utils import to_json

from bot.taskon import TaskonAPI, TaskonAccount


async def auth_taskon(taskon: TaskonAPI, account: TaskonAccount):
    if "taskon" not in account.auth_tokens:
        timestamp = int(time.time())
        nonce = await taskon.request_nonce()
        message = {
            "type": "ClientResponse",
            "server": {
                "name": "taskon_server",
                "url": "https://taskon.xyz"
            },
            "nonce": nonce,
            "did": account.wallet.address.replace("0x", "did:etho:"),
            "created": timestamp
        }
        signature = account.wallet.sign_message(to_json(message))
        account.auth_tokens["taskon"] = await taskon.request_auth_token(
            account.wallet.address, signature, nonce, timestamp, invite_code=account.invite_code)
        account.save_to_csv()
    taskon.set_auth_token(account.auth_tokens["taskon"])


@asynccontextmanager
async def authenticated_taskon(session: aiohttp.ClientSession, account: TaskonAccount = None) -> TaskonAPI:
    taskon = TaskonAPI(session, useragent=account.useragent if account else None)
    if account: await auth_taskon(taskon, account)
    yield taskon
