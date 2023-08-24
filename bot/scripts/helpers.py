import asyncio
from typing import Iterable, Callable

import aiohttp
from aiohttp_socks import ProxyConnector
from better_proxy import Proxy
from better_automation.process import bounded_gather

from bot.config import CONFIG
from bot.logger import logger, LoggingLevel
from bot.taskon import TaskonAccount


async def sleep(account, seconds: int, logging_level: LoggingLevel = "DEBUG"):
    if seconds <= 0:
        return

    logger.log(logging_level, f"{account} Sleeping {seconds} sec.")
    await asyncio.sleep(seconds)


async def process_account_with_session(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        fn: Callable,
        ignore_errors: bool = True,
):
    if ignore_errors:
        try:
            await fn(session, account)
        except Exception as e:
            logger.error(f"{account} Account was skipped: {e}")
            return
    else:
        await fn(session, account)


async def _process_accounts_with_session(
        accounts: Iterable[TaskonAccount],
        fn: Callable,
        *,
        proxy: Proxy = None,
        ignore_errors: bool = True,
):
    connector = ProxyConnector.from_url(proxy) if proxy else aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as session:
        for account in accounts:
            await process_account_with_session(session, account, fn, ignore_errors)


async def process_accounts_with_session(
        accounts: Iterable[TaskonAccount],
        fn: Callable,
        max_tasks: int = None,
):
    proxy_to_accounts: dict[Proxy: list[accounts]] = {}
    for account in accounts:
        if account.proxy not in proxy_to_accounts:
            proxy_to_accounts[account.proxy] = []
        proxy_to_accounts[account.proxy].append(account)
    tasks = [_process_accounts_with_session(accounts, fn, ignore_errors=CONFIG.IGNORE_ERRORS)
             for accounts in proxy_to_accounts.values()]
    max_tasks = max_tasks or CONFIG.MAX_TASKS
    await bounded_gather(tasks, max_tasks)
