from functools import wraps
from typing import Iterable

import aiohttp
from better_automation import TwitterAPI, DiscordAPI

from bot.logger import logger
from bot.taskon import DISCORD_BIND_INFO, TWITTER_BIND_INFO
from bot.taskon import TaskonAccount, TaskonAPI
from .auth import authenticated_taskon
from .helpers import process_accounts_with_session
from .user import _request_and_set_user_info
from .helpers import filter_tokens


def bind_app(bind_fn):
    @wraps(bind_fn)
    async def wrapper(session: aiohttp.ClientSession, account: TaskonAccount):
        async with authenticated_taskon(session, account) as taskon:
            if not account.user_info:
                await _request_and_set_user_info(taskon, account)
            await bind_fn(session, taskon, account)
            account.save_to_csv()

    return wrapper


@bind_app
async def bind_discord(session: aiohttp.ClientSession, taskon: TaskonAPI, account: TaskonAccount):
    if account.discord_username:
        logger.info(f"{account} Discord is already binded: @{account.discord_username}")
        return

    if "discord" not in account.auth_tokens:
        logger.warning(f"{account} No Discord authentication token")
        return

    discord = DiscordAPI(session, auth_token=account.auth_tokens["discord"], useragent=account.useragent)
    bind_code = await discord.bind_app(**DISCORD_BIND_INFO)
    await taskon.bind_discord(bind_code)
    await _request_and_set_user_info(taskon, account)
    logger.success(f"{account} Discord binded: @{account.discord_username}")


def discords_are_binded(func):
    async def wrapper(*args, **kwargs):
        accounts: Iterable[TaskonAccount] = args[0]
        filtered_accounts = [account for account in accounts if account.discord_username]

        for account in accounts:
            if not account.discord_username:
                logger.warning(f"{account} Discord is not binded")

        return await func(filtered_accounts, *args[1:], **kwargs)

    return wrapper


def discords_are_not_binded(func):
    async def wrapper(*args, **kwargs):
        accounts: Iterable[TaskonAccount] = args[0]
        filtered_accounts = [account for account in accounts if not account.discord_username]

        for account in accounts:
            if account.discord_username:
                logger.info(f"{account} Discord is already binded: @{account.discord_username}")

        return await func(filtered_accounts, *args[1:], **kwargs)

    return wrapper


@discords_are_not_binded
@filter_tokens('discord', presence=True)
async def bind_discords(accounts: Iterable[TaskonAccount]):
    await process_accounts_with_session(accounts, bind_discord)


@bind_app
async def bind_twitter(session: aiohttp.ClientSession, taskon: TaskonAPI, account: TaskonAccount):
    if account.twitter_username:
        logger.info(f"{account} Twitter is already binded: @{account.twitter_username}")
        return

    if "twitter" not in account.auth_tokens:
        logger.warning(f"{account} No Twitter authentication token")
        return

    state = await taskon.request_twitter_bind_state()

    twitter = TwitterAPI(session, auth_token=account.auth_tokens["twitter"], useragent=account.useragent)
    if "twitter_ct0" in account.auth_tokens:
        twitter.set_ct0(account.auth_tokens["twitter_ct0"])
    bind_code = await twitter.bind_app(**TWITTER_BIND_INFO, state=state)
    account.auth_tokens["twitter_ct0"] = twitter.ct0
    await taskon.bind_twitter(bind_code)
    await _request_and_set_user_info(taskon, account)
    logger.success(f"{account} Twitter binded: @{account.twitter_username}")


def twitters_are_binded(func):
    async def wrapper(*args, **kwargs):
        accounts: Iterable[TaskonAccount] = args[0]
        filtered_accounts = [account for account in accounts if account.twitter_username]

        for account in accounts:
            if not account.twitter_username:
                logger.warning(f"{account} Twitter is not binded")

        return await func(filtered_accounts, *args[1:], **kwargs)

    return wrapper


def twitters_are_not_binded(func):
    async def wrapper(*args, **kwargs):
        accounts: Iterable[TaskonAccount] = args[0]
        filtered_accounts = [account for account in accounts if not account.twitter_username]

        for account in accounts:
            if account.twitter_username:
                logger.info(f"{account} Twitter is already binded: @{account.twitter_username}")

        return await func(filtered_accounts, *args[1:], **kwargs)

    return wrapper


@twitters_are_not_binded
@filter_tokens('twitter', presence=True)
async def bind_twitters(accounts: Iterable[TaskonAccount]):
    await process_accounts_with_session(accounts, bind_twitter)
