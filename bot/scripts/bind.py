from typing import Iterable

import aiohttp
from better_automation import TwitterAPI, DiscordAPI

from bot.logger import logger
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon import DISCORD_BIND_INFO, TWITTER_BIND_INFO
from .auth import authenticated_taskon
from .user import _request_and_set_user_info
from .helpers import process_accounts_with_session


async def bind_discord(session: aiohttp.ClientSession, account: TaskonAccount):
    async with authenticated_taskon(session, account) as taskon:
        if not account.user_info:
            await _request_and_set_user_info(taskon, account)

        if account.discord_username:
            logger.info(f"{account} Discord is already binded: @{account.discord_username}")
            return

        if "discord" not in account.auth_tokens:
            logger.warning(f"{account} No Discord authentication token")
            return

        discord_auth_token = account.auth_tokens["discord"]
        discord = DiscordAPI(session, auth_token=discord_auth_token, useragent=account.useragent)
        bind_code = await discord.bind_app(**DISCORD_BIND_INFO)

        await _request_and_set_user_info(taskon, account)
        logger.success(f"{account} Discord binded: @{account.discord_username}")
        account.save_to_csv()


def discords_are_binded(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if not account.discord_username:
                logger.warning(f"{account} Discord is not binded")
                continue
        return await func(*args, **kwargs)
    return wrapper


def discords_are_not_binded(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if account.discord_username:
                logger.info(f"{account} Discord is already binded: @{account.discord_username}")
                continue
        return await func(*args, **kwargs)
    return wrapper


def discord_tokens_are_present(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if "discord" not in account.auth_tokens:
                logger.warning(f"{account} No Discord authentication token")
                continue
        return await func(*args, **kwargs)
    return wrapper


@discords_are_not_binded
@discord_tokens_are_present
async def bind_discords(accounts: Iterable[TaskonAccount]):
    await process_accounts_with_session(accounts, bind_discord)


async def bind_twitter(session: aiohttp.ClientSession, account: TaskonAccount):
    async with authenticated_taskon(session, account) as taskon:
        if not account.user_info:
            await _request_and_set_user_info(taskon, account)

        if account.twitter_username:
            logger.info(f"{account} Twitter is already binded: @{account.twitter_username}")
            return

        if "twitter" not in account.auth_tokens:
            logger.warning(f"{account} No Twitter authentication token")
            return

        taskon: TaskonAPI
        state = await taskon.request_twitter_auth_state()

        twitter_auth_token = account.auth_tokens["twitter"]
        twitter = TwitterAPI(session, auth_token=twitter_auth_token, useragent=account.useragent)
        await twitter.request_username()
        bind_code = await twitter.bind_app(**TWITTER_BIND_INFO, state=state)

        twitter_is_binded = await taskon.bind_twitter(state, bind_code)
        await _request_and_set_user_info(taskon, account)
        logger.success(f"{account} Twitter binded: @{account.twitter_username}")
        account.save_to_csv()


def twitters_are_binded(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if not account.twitter_username:
                logger.warning(f"{account} Twitter is not binded")
                continue
        return await func(*args, **kwargs)
    return wrapper


def twitters_are_not_binded(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if account.twitter_username:
                logger.info(f"{account} Twitter is already binded: @{account.twitter_username}")
                continue
        return await func(*args, **kwargs)
    return wrapper


def twitter_tokens_are_present(func):
    async def wrapper(*args, **kwargs):
        accounts = args[0]
        for account in accounts:
            if "twitter" not in account.auth_tokens:
                logger.warning(f"{account} No Twitter authentication token")
                continue
        return await func(*args, **kwargs)
    return wrapper


@twitters_are_not_binded
@twitter_tokens_are_present
async def bind_twitters(accounts: Iterable[TaskonAccount]):
    await process_accounts_with_session(accounts, bind_twitter)
