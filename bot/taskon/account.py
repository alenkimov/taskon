from functools import cached_property
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import pyuseragents
from better_proxy import Proxy
from better_web3 import Wallet, Chain
from web3.types import TxReceipt, HexStr, Wei
from eth_utils import from_wei

from bot.config import CONFIG
from bot.logger import logger
from .models import UserInfo

TABLE_COLUMNS = [
    "(required) Proxy",
    "(required) Private key",
    "(optional) Invite code",
    "(optional) Discord token",
    "(optional) Twitter token",
    "(auto) Twitter ct0",
    "(auto) Site token",
    "(auto) Discord username",
    "(auto) Twitter username",
    "(auto) Invite code",
]


class TaskonAccount:
    wallet: Wallet
    proxy: Proxy | None
    invite_code: str | None
    user_info: UserInfo | None
    auth_tokens: dict[str: str]  # {app_name: auth_token}

    def __init__(
            self,
            wallet: Wallet,
            *,
            number: int = None,
            proxy: Proxy = None,
            invite_code: str = None,
            csv_filepath: Path = None,
    ):
        self.wallet = wallet
        self.proxy = proxy
        self.number = number
        self.invite_code = invite_code
        self.csv_filepath = csv_filepath
        self.useragent = pyuseragents.random()
        self.auth_tokens = {}
        self.user_info = None
        self._discord_username = None
        self._twitter_username = None

    def __str__(self):
        if CONFIG.HIDE_SECRETS:
            address = self.wallet.short_address
        else:
            address = self.wallet.address

        additional_info = f'[{self.number:04}]' if self.number is not None else ''

        if not CONFIG.HIDE_SECRETS and self.proxy:
            additional_info += f' {self.proxy}'

        return f"{additional_info} [{address}]"

    def _get_username(self, sns_type: str) -> str | None:
        username = getattr(self, f"_{sns_type.lower()}_username")
        if not username and self.user_info:
            for sns_data in self.user_info.sns:
                if sns_data.sns_type == sns_type:
                    username = sns_data.sns_user_name
                    setattr(self, f"_{sns_type.lower()}_username", username)
                    break
        return username

    @property
    def discord_username(self) -> str | None:
        return self._get_username('Discord')

    @property
    def twitter_username(self) -> str | None:
        return self._get_username('Twitter')

    def save_to_csv(self):
        df = pd.read_csv(self.csv_filepath)
        new_data = {
            "(auto) Twitter ct0": self.auth_tokens.get("twitter_ct0"),
            "(auto) Site token": self.auth_tokens.get("taskon"),
            "(auto) Discord username": self.discord_username,
            "(auto) Twitter username": self.twitter_username,
        }
        if self.user_info is not None:
            new_data["(auto) Invite code"] = self.user_info.invite_code

        for col in df.columns:
            if col in new_data:
                if new_data[col] is not None:
                    df.loc[df["(required) Private key"] == self.wallet.private_key, col] = new_data[col]
            else:
                continue

        df.to_csv(self.csv_filepath, index=False)

    @classmethod
    def from_csv(cls, csv_filepath: Path | str) -> list['TaskonAccount']:
        accounts: list[TaskonAccount] = []
        df = pd.read_csv(csv_filepath).replace({np.nan: None})
        for i, row in df.iterrows():
            i: int
            private_key = row.get("(required) Private key")

            if private_key is None:
                logger.error(f"[line {i + 2}] Private key is missing")
                continue

            try:
                wallet = Wallet.from_key(private_key)
            except (ValueError, TypeError) as e:
                logger.error(f"[line {i + 2}] Invalid private key: {e}")
                continue

            account = TaskonAccount(wallet, number=i+1)
            account.csv_filepath = csv_filepath

            proxy = row.get("(required) Proxy")
            if proxy: account.proxy = Proxy.from_str(proxy)

            invite_code = row.get("(optional) Invite code")
            account.invite_code = invite_code or CONFIG.DEFAULT_INVITE_CODE

            discord_token = row.get("(optional) Discord token")
            if discord_token:
                account.auth_tokens["discord"] = discord_token

            twitter_token = row.get("(optional) Twitter token")
            if twitter_token:
                account.auth_tokens["twitter"] = twitter_token

            ct0 = row.get("(auto) Twitter ct0")
            if ct0:
                account.auth_tokens["twitter_ct0"] = ct0

            site_auth_token = row.get("(auto) Site token")
            if site_auth_token:
                account.auth_tokens["taskon"] = site_auth_token

            account._discord_username = row.get("(auto) Discord username")
            account._twitter_username = row.get("(auto) Twitter username")

            accounts.append(account)
            print(account.info())

        return accounts

    @property
    def is_default_invite_code(self) -> bool:
        return self.invite_code == CONFIG.DEFAULT_INVITE_CODE

    def info(self) -> str:
        info = str(self)

        if not CONFIG.HIDE_SECRETS:
            info += f"\n\tInvite code: {self.invite_code}"
            if self.is_default_invite_code:
                info += " (default)"

            if self.user_info:
                info += f"\n\tInvite code (of this account): {self.user_info.invite_code}"

        if self.discord_username:
            if CONFIG.HIDE_SECRETS:
                info += f"\n\tDiscord is binded"
            else:
                info += f"\n\tBinded discord: @{self.discord_username}"
        if self.twitter_username:
            if CONFIG.HIDE_SECRETS:
                info += f"\n\tTwitter is binded"
            else:
                info += f"\n\tBinded twitter: @{self.twitter_username}"

        if CONFIG.HIDE_SECRETS:
            service_names = ', '.join(self.auth_tokens.keys())
            info += f"\n\tAuth tokens: {service_names}"
        else:
            for service_name, auth_token in self.auth_tokens.items():
                info += f'\n\tAuth token ({service_name}): {auth_token}'

        return info

    def tx_hash(self, chain: Chain, tx_hash: HexStr | str, value: Wei | int = None) -> str:
        tx_hash_link = chain.get_link_by_tx_hash(tx_hash)
        message = f"{self} {chain} {tx_hash_link}"
        if value is not None:
            message += f"\n\tSent: {from_wei(value, 'ether')} {chain.token.symbol}"
        return message

    def tx_receipt(self, chain: Chain, tx_receipt: TxReceipt | str, value: Wei | int = None) -> str:
        tx_hash = tx_receipt.transactionHash.hex()
        message = self.tx_hash(chain, tx_hash, value)
        tx_fee_wei = tx_receipt.gasUsed * tx_receipt.effectiveGasPrice
        tx_fee = from_wei(tx_fee_wei, "ether")
        message += f"\n\tFee: {tx_fee} {chain.token.symbol}"
        return message
