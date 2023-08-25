from better_automation.utils import copy_file, load_toml
from pydantic import BaseModel

from bot._logger import LoggingLevel
from bot.paths import CONFIG_DIR


DEFAULT_CONFIG_DIR = CONFIG_DIR / ".default"
DEFAULT_CONFIG_TOML = DEFAULT_CONFIG_DIR / "config.toml"
CONFIG_TOML = CONFIG_DIR / "config.toml"
copy_file(DEFAULT_CONFIG_TOML, CONFIG_TOML)


class Config(BaseModel):
    LOGGING_LEVEL: LoggingLevel = "INFO"
    DEFAULT_INVITE_CODE: str
    ANTICAPTCHA_API_KEY: str
    MAX_DELAY: int = 0
    MAX_TASKS: int = 100
    IGNORE_ERRORS: bool = True
    HIDE_SECRETS: bool = True


CONFIG = Config(**load_toml(CONFIG_TOML))
