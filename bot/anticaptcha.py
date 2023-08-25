from aioanticaptcha.recaptchav2proxyless import recaptchaV2Proxyless
from bot.config import CONFIG
from bot.logger import logger
from bot.taskon import TaskonAccount


class AntiCaptchaError(Exception):
    pass


async def solve_recaptcha_v2(account: TaskonAccount, url: str, site_key: str) -> str:
    async with recaptchaV2Proxyless() as solver:
        solver.log = lambda msg: logger.debug(f"{account} {msg}")
        solver.set_verbose(1)
        solver.set_key(CONFIG.ANTICAPTCHA_API_KEY)
        solver.set_website_url(url)
        solver.set_website_key(site_key)

        g_response = await solver.solve_and_return_solution()
        if g_response == 0:
            raise AntiCaptchaError(solver.err_string)
        return g_response
