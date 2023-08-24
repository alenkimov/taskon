from typing import Callable

import aiohttp
from better_automation import TwitterAPI, DiscordAPI
import json
from bot.logger import LoggingLevel
from bot.logger import logger
from bot.scripts.user import _request_and_set_user_info
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import TaskInfo
from bot.taskon import DISCORD_BIND_INFO, TWITTER_BIND_INFO


async def follow_twitter(account: TaskonAccount, task_params: dict, *, twitter: TwitterAPI):
    user_id = task_params["user_to_follow_id"]
    username = task_params["user_to_follow"]
    await twitter.follow(user_id)
    logger.info(f"{account} Follow @{username}")


# async def _submit_task_by_task_id(
#         taskon: TaskonAPI,
#         account: TaskonAccount,
#         task_id: int,
#         bind_code: str = None,
#         *,
#         logging_level: LoggingLevel = "DEBUG",
# ) -> bool:
#     task_is_completed = await taskon.submit_task(task_id, value=bind_code)
#     logger.log(logging_level, f"{account} (task_id={task_id}) Task submitted")
#     return task_is_completed


class TaskSolver:
    def __init__(
            self,
            template_id: str,
            solver: Callable or None,
            twitter_is_required: bool = False,
            discord_is_required: bool = False,
    ):
        self.template_id = template_id
        self._solver = solver
        self.twitter_is_required = twitter_is_required
        self.discord_is_required = discord_is_required

    async def bind_twitter(
            self,
            taskon: TaskonAPI,
            twitter: TwitterAPI,
    ):
        state = await taskon.request_twitter_auth_state()
        await twitter.request_username()
        bind_code = await twitter.bind_app(**TWITTER_BIND_INFO, state=state)
        await taskon.bind_twitter(state, bind_code)

    async def solve(
            self,
            session: aiohttp.ClientSession,
            taskon: TaskonAPI,
            account: TaskonAccount,
            task_info: TaskInfo,
    ) -> str | None:
        if self._solver is None:
            return None

        task_params = json.loads(task_info.params)

        if not account.user_info:
            await _request_and_set_user_info(taskon, account)

        bind_code = None
        if self.twitter_is_required:
            if "twitter" not in account.auth_tokens:
                logger.warning(f"{account} No Twitter authentication token")
                return

            twitter = TwitterAPI(session, auth_token=account.auth_tokens["twitter"], useragent=account.useragent)

            if not account.twitter_username:
                bind_code = await self.bind_twitter(taskon, twitter)

            await self._solver(account, task_params, twitter=twitter)

        elif self.discord_is_required:
            if "discord" not in account.auth_tokens:
                logger.warning(f"{account} No Discord authentication token")
                return

            discord = DiscordAPI(session, auth_token=account.auth_tokens["discord"], useragent=account.useragent)

            if not account.discord_username:
                bind_code = await discord.bind_app(**DISCORD_BIND_INFO)

            await self._solver(account, task_params)

        else:
            await self._solver(account, task_params)

        return bind_code


TEMPLATE_ID_TO_TASK_SOLVER = {
    'FollowTwitter': TaskSolver('FollowTwitter', follow_twitter, twitter_is_required=True),
    'RetweetTwitter': TaskSolver('RetweetTwitter', None, twitter_is_required=True),
    'QuoteTweetAndTag': TaskSolver('QuoteTweetAndTag', None, twitter_is_required=True),
    'QuoteTweetAndHashTag': TaskSolver('QuoteTweetAndHashTag', None, twitter_is_required=True),
    'LikeATweet': TaskSolver('LikeATweet', None, twitter_is_required=True),
    'JoinDiscord': TaskSolver('JoinDiscord', None, discord_is_required=True),
    'PowTask': TaskSolver('PowTask', None),
    'PowQa': TaskSolver('PowQa', None),
    'PowQaWithAnswer': TaskSolver('PowQaWithAnswer', None),
    'LinkTask': TaskSolver('LinkTask', None),
    'JoinTelegram': TaskSolver('JoinTelegram', None),
    'OuterAPI': TaskSolver('OuterAPI', None),
    'Youtube': TaskSolver('Youtube', None),
    'QuizChoose': TaskSolver('QuizChoose', None),
    'SurveyChoose': TaskSolver('SurveyChoose', None),
    'TokenBalance': TaskSolver('TokenBalance', None),
    'NftHolder': TaskSolver('NftHolder', None),
}


async def submit_task_by_task_info(
        session: aiohttp.ClientSession,
        taskon: TaskonAPI,
        account: TaskonAccount,
        task_info: TaskInfo,
):
    task_id = task_info.id
    template_id = task_info.template_id
    solver = TEMPLATE_ID_TO_TASK_SOLVER[task_info.template_id]
    bind_code = await solver.solve(session, taskon, account, task_info)
    task_is_completed = await taskon.submit_task(task_id, value=bind_code)
    message = f"{account} (task_id={task_id}, template_id='{template_id}') Task is completed: {task_is_completed}"
    logger.log(message, "SUCCESS" if task_is_completed else "WARNING")
