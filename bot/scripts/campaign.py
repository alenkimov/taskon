from typing import Iterable

import aiohttp

from bot.logger import LoggingLevel
from bot.logger import logger
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import CampaignInfo, CampaignStatusInfo, UserCampaignStatus
from .auth import authenticated_taskon
from bot.utils import convert_to_human_readable
from bot.scripts.bind import discords_are_binded, twitters_are_binded
from better_automation.utils import curry_async
from .helpers import process_accounts_with_session
from bot.questions import ask_int
from .task import submit_task_by_task_info


async def _request_campaign_info(
        taskon: TaskonAPI,
        campaign_id: int,
        *,
        logging_level: LoggingLevel = "DEBUG",
) -> CampaignInfo:
    campaign_info = await taskon.request_campaign_info(campaign_id)
    logger.log(logging_level, f"(campaign_id={campaign_id}) Campaign info obtained")
    return campaign_info


async def _request_campaign_status_info(
        taskon: TaskonAPI,
        campaign_id: int,
        *,
        logging_level: LoggingLevel = "DEBUG",
) -> CampaignStatusInfo:
    campaign_status_info = await taskon.request_campaign_status_info(campaign_id)
    logger.log(logging_level, f"(campaign_id={campaign_id}) Campaign status info obtained")
    return campaign_status_info


async def _request_user_campaign_status(
        taskon: TaskonAPI,
        account: TaskonAccount,
        campaign_id: int,
        *,
        logging_level: LoggingLevel = "DEBUG",
) -> UserCampaignStatus:
    user_campaign_status = await taskon.request_user_campaign_status(campaign_id)
    logger.log(logging_level, f"{account} (campaign_id={campaign_id}) Campaign status info obtained")
    return user_campaign_status


async def _enter_campaign_by_account(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        campaign_info: CampaignInfo,
        campaign_status_info: CampaignStatusInfo,
):
    campaign_id = campaign_info.id
    async with authenticated_taskon(session, account) as taskon:
        user_campaign_status = await _request_user_campaign_status(
            taskon, account, campaign_id, logging_level="DEBUG")
        for task_info in campaign_info.tasks:
            await submit_task_by_task_info(session, taskon, account, task_info)


# @discords_are_binded
# @twitters_are_binded
async def _enter_campaign(accounts: Iterable[TaskonAccount], campaign_id: int):
    async with aiohttp.ClientSession() as session:
        async with authenticated_taskon(session) as taskon:
            campaign_info = await _request_campaign_info(taskon, campaign_id)
            campaign_status_info = await _request_campaign_status_info(taskon, campaign_id)

            print(f"(campaign_id={campaign_id}) {campaign_info.name}")
            if campaign_info.recaptcha: print(f"ATTENTION! ReCaptcha solving required!")
            start_time = convert_to_human_readable(campaign_info.start_time)
            end_time = convert_to_human_readable(campaign_info.end_time)
            print(f"Duration: {start_time} - {end_time}")

            print("\nRewards:")
            print(f"Max winners: {campaign_info.max_winners}")
            for reward in campaign_info.winner_rewards:
                reward_params = reward.reward_params
                if reward.reward_type == "Token":
                    print(f"<{reward_params.chain}> Total: {reward_params.total_amount} {reward_params.token_name}")
                else:
                    print(f"{reward.reward_type}")

            print("\nTasks:")
            for task in campaign_info.tasks:
                print(f"{task.template_id}: {task.params}")

    enter_campaign_campaign_info = await curry_async(_enter_campaign_by_account)(
        campaign_info=campaign_info, campaign_status_info=campaign_status_info)
    await process_accounts_with_session(accounts, enter_campaign_campaign_info)


async def enter_campaign(accounts):
    campaign_id = await ask_int("Enter campaign id (int)", min=0)
    await _enter_campaign(accounts, campaign_id)
