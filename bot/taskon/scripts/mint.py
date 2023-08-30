import aiohttp
from better_automation.utils import curry_async
from web3.exceptions import ContractLogicError

from better_web3 import Chain
from bot.chains import CHAINS
from bot.logger import logger
from bot.questions import ask_int
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.contract import CapMinter
from .auth import authenticated_taskon
from .campaign import _request_campaign_info
from .check_winners import _request_campaign_winners
from .helpers import execute_fn, process_accounts_with_session
from ..models import MintData

TASKON_CHAIN_NAME_TO_CHAIN_ID = {
    "polygon": 137,
    "bsc": 56,
}


async def _claim_cap(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        *,
        mint_data: MintData,
        chain: Chain,
):
    log_prefix = f"{account} (campaign_id={mint_data.campaign_id}) {chain}"
    cap_minter = CapMinter(chain, mint_data.contract_address)
    claim_fn = cap_minter.mint_function(
        account.wallet.address,
        mint_data.campaign_id,
        mint_data.token_uri,
        mint_data.total,
        mint_data.hash,
        mint_data.signature,
    )
    try:
        await execute_fn(chain, account, claim_fn, logging_level="SUCCESS")
    except (ContractLogicError, ValueError) as e:
        logger.error(f"{log_prefix} Failed to mint CAP: {e}.")
        return


async def _claim_caps(accounts: list[TaskonAccount], campaign_id: int):
    async with aiohttp.ClientSession() as session:
        async with authenticated_taskon(session, accounts[0]) as taskon:
            campaign_info = await _request_campaign_info(taskon, campaign_id)
            # Не стал реализовывать проверку на победные аккаунты,
            # так как победителей может быть очень много и это занимает уйму времени
            # all_winners_info = await _request_campaign_winners(taskon, campaign_info)
            # all_winner_addresses = {winner_info.user_address for winner_info in all_winners_info}
            # winner_accounts = {account for account in accounts if account.wallet.address in all_winner_addresses}
            # print(winner_accounts)
            # if winner_accounts:
            for reward in campaign_info.winner_rewards:
                reward_params = reward.reward_params
                if reward.reward_type == "Cap":
                    taskon_chain_name = reward_params['chain']
                    mint_data = await taskon.request_mint_data(taskon_chain_name, campaign_id)
                    chain_id = TASKON_CHAIN_NAME_TO_CHAIN_ID[taskon_chain_name]
                    chain = CHAINS[chain_id]
                    claim_cap = await curry_async(_claim_cap)(mint_data=mint_data, chain=chain)
                    await process_accounts_with_session(accounts, claim_cap)


async def claim_caps(accounts: list[TaskonAccount]):
    campaign_id = await ask_int("Enter campaign id (int)", min=0)
    await _claim_caps(accounts, campaign_id)
