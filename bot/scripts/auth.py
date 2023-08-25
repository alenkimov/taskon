import time
from contextlib import asynccontextmanager
from typing import Iterable

import aiohttp
from better_automation import TwitterAPI
from better_automation.utils import to_json


from bot.taskon import TaskonAPI, TaskonAccount
from bot.logger import logger, LoggingLevel
from .helpers import filter_tokens, process_accounts_with_session


async def _auth_taskon(taskon: TaskonAPI, account: TaskonAccount, *, logging_level: LoggingLevel = "DEBUG"):
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
        account.auth_tokens['taskon'] = await taskon.request_auth_token(
            account.wallet.address, signature, nonce, timestamp, invite_code=account.invite_code)
        logger.log(logging_level, f"{account} Auth token obtained: {account.auth_tokens['taskon']}")
        logger.log(logging_level, f"{account} User invited by invite code: {account.invite_code}")
        account.save_to_csv()
    taskon.set_auth_token(account.auth_tokens["taskon"])


@asynccontextmanager
async def authenticated_taskon(
        session: aiohttp.ClientSession,
        account: TaskonAccount = None,
        *,
        logging_level: LoggingLevel = "DEBUG"
) -> TaskonAPI:
    taskon = TaskonAPI(session, useragent=account.useragent if account else None)
    if account: await _auth_taskon(taskon, account, logging_level=logging_level)
    yield taskon


@asynccontextmanager
async def authenticated_twitter(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
) -> TwitterAPI:
    twitter = TwitterAPI(session, auth_token=account.auth_tokens["twitter"], useragent=account.useragent)
    if "twitter_ct0" in account.auth_tokens:
        twitter.set_ct0(account.auth_tokens["twitter_ct0"])
    yield twitter
    account.auth_tokens["twitter_ct0"] = twitter.ct0


async def auth_taskon(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
):
    async with authenticated_taskon(session, account, logging_level="SUCCESS"):
        pass


@filter_tokens('taskon', presence=False)
async def auth_taskon_accounts(accounts: Iterable[TaskonAccount]):
    await process_accounts_with_session(accounts, auth_taskon)
