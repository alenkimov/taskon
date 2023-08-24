from pathlib import Path

import questionary

from bot.paths import INPUT_DIR
from bot.taskon.account import TABLE_COLUMNS as ACCOUNTS_TABLE_COLUMNS
from bot.utils import get_csv_filenames, create_csv_table, file_count

INPUT_DIR.mkdir(exist_ok=True)
DEFAULT_ACCOUNTS_CSV = INPUT_DIR / "accounts.csv"

if file_count(INPUT_DIR) == 0:
    create_csv_table(DEFAULT_ACCOUNTS_CSV, ACCOUNTS_TABLE_COLUMNS)


async def select_accounts_csv() -> Path:
    csv_filenames = get_csv_filenames(INPUT_DIR)
    filename = csv_filenames[0]
    if len(csv_filenames) > 1:
        filename = await questionary.select("Which file?", choices=csv_filenames).ask_async()
    return INPUT_DIR / filename
