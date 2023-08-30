import asyncio
from typing import Callable

import questionary
from better_automation.utils import load_toml

from bot.author import TG_LINK
from bot.input import select_accounts_csv
from bot.logger import logger
from bot.taskon.scripts.bind import bind_discords, bind_twitters
from bot.taskon.scripts.auth import auth_taskon_accounts
from bot.taskon.scripts.campaign import enter_campaign
from bot.taskon.account import TaskonAccount
from bot.taskon.scripts.check_winners import check_winners


PROJECT_INFO = load_toml('pyproject.toml')
PROJECT_VERSION = PROJECT_INFO['tool']['poetry']['version']


async def main():
    print(f'VERSION v{PROJECT_VERSION}')
    accounts_csv = await select_accounts_csv()
    accounts = TaskonAccount.from_csv(accounts_csv)

    if not accounts:
        logger.warning(f'Add accounts into {accounts_csv} before start')
        return

    modules = {
        'Auth and Invite': auth_taskon_accounts,
        'Bind Discords': bind_discords,
        'Bind Twitters': bind_twitters,
        'Enter campaign': enter_campaign,
        'Check winners': check_winners,
    }

    async def select_module() -> Callable:
        module_name = await questionary.select("Select module", choices=list(modules.keys())).ask_async()
        return modules[module_name]

    while True:
        print(f'VERSION v{PROJECT_VERSION}')
        print(f'Telegram: {TG_LINK}')
        module = await select_module()
        await module(accounts)


if __name__ == '__main__':
    asyncio.run(main())
