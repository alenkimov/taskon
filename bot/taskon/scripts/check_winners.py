from typing import Iterable

import aiohttp

from bot.logger import LoggingLevel
from bot.logger import logger
from bot.questions import ask_int
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import WinnerInfo, CampaignInfo
from .auth import authenticated_taskon
from .campaign import _request_campaign_info


async def _request_campaign_winners(
        taskon: TaskonAPI,
        campaign_info: CampaignInfo,
        *,
        logging_level: LoggingLevel = "DEBUG",
) -> list[WinnerInfo]:
    campaign_id = campaign_info.id
    size = 50
    total_pages = (campaign_info.max_winners // size) + 1
    campaign_winners: list[WinnerInfo] = []
    for page in range(total_pages):
        _campaign_winners = await taskon.request_campaign_winners(campaign_id, size=size, page=page)
        campaign_winners.extend(_campaign_winners)
    logger.log(logging_level, f"(campaign_id={campaign_id}) Campaign winners obtained")
    return campaign_winners


async def _check_winners(accounts: Iterable[TaskonAccount], campaign_id: int):
    async with aiohttp.ClientSession() as session:
        async with authenticated_taskon(session) as taskon:
            campaign_info = await _request_campaign_info(taskon, campaign_id)
            log_info = f"(campaign_id={campaign_id})"

            winners = await _request_campaign_winners(taskon, campaign_info)
            winner_addresses = {winner.user_address for winner in winners} & {account.wallet.address for account in accounts}

            if not winner_addresses:
                print(f"{log_info} No winning accounts :(")
                return

            print(f"{log_info} Winners:")
            for address in winner_addresses:
                print(f"\t{address}")


async def check_winners(accounts: list[TaskonAccount]):
    campaign_id = await ask_int("Enter campaign id (int)", min=0)
    await _check_winners(accounts, campaign_id)
