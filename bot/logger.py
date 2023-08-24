from bot.paths import LOG_DIR
from bot.config import CONFIG
from bot._logger import logger, setup_logger, LoggingLevel

setup_logger(LOG_DIR, CONFIG.LOGGING_LEVEL)
