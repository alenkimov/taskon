from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


def get_csv_filenames(path: Path | str) -> list[str]:
    path = Path(path)
    csv_filepath_generator = path.glob("*.csv")
    return [csv_filepath.name for csv_filepath in csv_filepath_generator]


def create_csv_table(filepath: Path | str, columns: Iterable[str]):
    df = pd.DataFrame(columns=columns)
    df.to_csv(filepath, index=False)


def file_count(path: Path | str) -> int:
    path = Path(path)
    return len(list(path.iterdir()))


def convert_to_human_readable(unix_time):
    return datetime.fromtimestamp(unix_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
