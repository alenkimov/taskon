import asyncio
from random import randrange
from typing import Iterable, Callable

import aiohttp
from aiohttp_socks import ProxyConnector
from better_automation.process import bounded_gather
from better_proxy import Proxy
from better_web3 import Chain
from better_web3 import Wallet
from eth_typing import HexStr
from web3.contract.async_contract import AsyncContractFunction
from web3.types import Wei

from bot.config import CONFIG
from bot.logger import logger, LoggingLevel
from bot.taskon import TaskonAccount


def filter_tokens(app_name, *, presence: bool):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            accounts: Iterable[TaskonAccount] = args[0]
            if not accounts:
                return

            if presence:
                filtered_accounts = [account for account in accounts if app_name in account.auth_tokens]
                log_message = f"No accounts with {app_name} authentication token"
            else:
                filtered_accounts = [account for account in accounts if app_name not in account.auth_tokens]
                log_message = f"All accounts have {app_name} authentication token"

            if not filtered_accounts:
                logger.warning(log_message)
                return

            return await func(filtered_accounts, *args[1:], **kwargs)

        return wrapper

    return decorator


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
        accounts_len = len(list(accounts))
        for account in accounts:
            await process_account_with_session(session, account, fn, ignore_errors)
            if accounts_len > 1 and sum(CONFIG.DELAY_RANGE) > 0:
                await sleep(account, randrange(*CONFIG.DELAY_RANGE), logging_level="INFO")


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


async def execute_fn(
        chain: Chain,
        account: TaskonAccount,
        fn: AsyncContractFunction,
        *,
        value: Wei | int = None,
        wait_for_tx_receipt: bool = False,
        logging_level: LoggingLevel = "DEBUG",
) -> HexStr:
    wallet = account.wallet
    tx_hash = await chain.execute_fn(wallet.account, fn, value=value)
    if wait_for_tx_receipt:
        tx_receipt = await chain.wait_for_tx_receipt(tx_hash)
        logger.log(logging_level, account.tx_receipt(chain, tx_receipt, value))
    else:
        logger.log(logging_level, account.tx_hash(chain, tx_hash, value))
    return tx_hash
