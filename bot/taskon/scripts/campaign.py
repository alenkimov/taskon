from typing import Iterable

import aiohttp

from bot.logger import LoggingLevel
from bot.logger import logger
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import CampaignInfo, CampaignStatusInfo, UserCampaignStatus
from better_automation.anticaptcha import AnticaptchaClient
from .auth import authenticated_taskon
from bot.utils import convert_to_human_readable
from .bind import discords_are_binded, twitters_are_binded
from better_automation.utils import curry_async
from .helpers import process_accounts_with_session
from bot.questions import ask_int
from .task import TEMPLATE_ID_TO_TASK_SOLVER
from bot.config import CONFIG


SITE_KEY = "6LceulwgAAAAANtqJ7oIASNtNhTa2qMz-2z_m6VJ"


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
        *,
        anticaptcha: AnticaptchaClient,
        campaign_info: CampaignInfo,
):
    campaign_id = campaign_info.id
    async with authenticated_taskon(session, account) as taskon:
        user_campaign_status = await _request_user_campaign_status(
            taskon, account, campaign_id, logging_level="DEBUG")
        if not all((user_task_status.is_submitter for user_task_status
                   in user_campaign_status.task_status_details)):
            for i, (task_info, user_task_status) in enumerate(zip(campaign_info.tasks, user_campaign_status.task_status_details), start=1):
                log_message = f"{account} (task_number={i})"
                if not user_task_status.is_submitter:
                    solver = TEMPLATE_ID_TO_TASK_SOLVER[task_info.template_id]

                    if solver.twitter_is_required and not account.twitter_username:
                        logger.warning(f"{log_message} You need to bind a Twitter account before solving this task")
                        return

                    if solver.discord_is_required and not account.discord_username:
                        logger.warning(f"{log_message} You need to bind a Discord account before solving this task")
                        return

                    await solver.solve(session, taskon, account, task_info)
                    task_is_completed = await taskon.submit_task(task_info.id)

                    if task_is_completed:
                        logger.success(f"{log_message} Task completed!")
                    else:
                        logger.warning(f"{log_message} Failed to complete the task!")
                else:
                    logger.info(f"{log_message} Task is already completed")

            user_campaign_status = await _request_user_campaign_status(
                taskon, account, campaign_id, logging_level="DEBUG")

        if all((user_task_status.is_submitter for user_task_status
                in user_campaign_status.task_status_details)):
            g_captcha_response = None
            if campaign_info.recaptcha:
                url = f'https://taskon.xyz/campaign/detail/{campaign_id}'
                g_captcha_response = await anticaptcha.recaptcha_v2_with_proxy(
                    url,
                    SITE_KEY,
                    is_invisible=True,
                    proxy=account.proxy.as_url,
                    useragent=account.useragent,
                )
            campaign_is_submitted = await taskon.submit_campaign(campaign_id, g_captcha_response)
            if campaign_is_submitted:
                logger.success(f"{account} (campaign_id={campaign_id}) Campaign submited!")
            else:
                logger.warning(f"{account} (campaign_id={campaign_id}) Failed to submit campaign."
                               f" Some of tasks aren't completed")
            return campaign_is_submitted


async def _enter_campaign(accounts: Iterable[TaskonAccount], campaign_id: int):
    async with aiohttp.ClientSession() as session:
        anticaptcha = AnticaptchaClient(session, CONFIG.ANTICAPTCHA_API_KEY)
        async with authenticated_taskon(session) as taskon:
            campaign_info = await _request_campaign_info(taskon, campaign_id)
            log_info = f"(campaign_id={campaign_id})"

            if campaign_info.is_end:
                logger.warning(f"{log_info} The campaign is already over")
                return

            print(f"{log_info} {campaign_info.name}")
            if campaign_info.recaptcha:
                print(f"ATTENTION! ReCaptcha solving required!")
                balance = await anticaptcha.request_balance()
                print(f"Anticaptcha balance: ${balance}")
            start_time = convert_to_human_readable(campaign_info.start_time)
            end_time = convert_to_human_readable(campaign_info.end_time)
            print(f"Duration: {start_time} - {end_time}")

            print("\nRewards:")
            print(f"Max winners: {campaign_info.max_winners}")
            for reward in campaign_info.winner_rewards:
                reward_params = reward.reward_params
                if reward.reward_type == "Token":
                    print(f"<{reward_params['chain']}> Total: {reward_params['total_amount']} {reward_params['token_name']}")
                elif reward.reward_type == "Cap":
                    print(f"<{reward_params['chain']}> {reward_params['collection_name']}")

            print("\nTasks:")
            for task in campaign_info.tasks:
                print(f"{task.template_id}: {task.params}")

    enter_campaign_by_account = await curry_async(_enter_campaign_by_account)(
        anticaptcha=anticaptcha, campaign_info=campaign_info)
    await process_accounts_with_session(accounts, enter_campaign_by_account)


@discords_are_binded
@twitters_are_binded
async def enter_campaign(accounts: list[TaskonAccount]):
    campaign_id = await ask_int("Enter campaign id (int)", min=0)
    await _enter_campaign(accounts, campaign_id)
