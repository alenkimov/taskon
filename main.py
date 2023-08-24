import asyncio
from typing import Callable

import questionary

from bot.author import TG_LINK
from bot.input import select_accounts_csv
from bot.logger import logger
from bot.scripts.bind import bind_discords, bind_twitters
from bot.scripts.campaign import enter_campaign
from bot.taskon.account import TaskonAccount


async def main():
    accounts_csv = await select_accounts_csv()
    accounts = TaskonAccount.from_csv(accounts_csv)

    if not accounts:
        logger.warning(f'Add accounts into {accounts_csv} before start')
        return

    modules = {
        'Bind Discords': bind_discords,
        'Bind Twitters': bind_twitters,
        'Enter campaign': enter_campaign,
    }

    async def select_module() -> Callable:
        module_name = await questionary.select("Select module", choices=list(modules.keys())).ask_async()
        return modules[module_name]

    while True:
        print(f'Telegram: {TG_LINK}')
        module = await select_module()
        await module(accounts)


if __name__ == '__main__':
    asyncio.run(main())
