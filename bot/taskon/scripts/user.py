import aiohttp

from bot._logger import LoggingLevel
from bot.logger import logger
from bot.taskon import TaskonAPI, TaskonAccount

from .auth import authenticated_taskon


async def _request_and_set_user_info(
        taskon: TaskonAPI,
        account: TaskonAccount,
        *,
        logging_level: LoggingLevel = "DEBUG",
):
    user_info = await taskon.request_user_info()
    logger.log(logging_level, f"{account} User info obtained")
    account.user_info = user_info
    account.save_to_csv()


async def request_and_set_user_info(session: aiohttp.ClientSession, account: TaskonAccount):
    async with authenticated_taskon(session, account) as tabi:
        await _request_and_set_user_info(tabi, account, logging_level="SUCCESS")
