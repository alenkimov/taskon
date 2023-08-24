import aiohttp
from better_automation import TwitterAPI

from bot.logger import LoggingLevel
from bot.logger import logger
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import TaskInfo

TEMPLATE_ID_TO_FUNCTION = {
    'FollowTwitter': ...,
    'LikeATweet': ...,
    'JoinDiscord': ...,
}


async def follow_twitter(session: aiohttp.ClientSession, account: TaskonAccount):
    async with TwitterAPI(session, account.auth_tokens['twitter']) as twitter:
        ...


async def _submit_task_by_id(
        taskon: TaskonAPI,
        account: TaskonAccount,
        task_id: int,
        bind_code: str = None,
        *,
        logging_level: LoggingLevel = "DEBUG",
) -> bool:
    task_is_completed = await taskon.submit_task(task_id, value=bind_code)
    logger.log(logging_level, f"{account} (task_id={task_id}) Task submitted")
    return task_is_completed


async def _submit_task_by_task_info(
        taskon: TaskonAPI,
        account: TaskonAccount,
        task_info: TaskInfo,
        bind_code: str = None,
        *,
        logging_level: LoggingLevel = "DEBUG",
):
    ...
