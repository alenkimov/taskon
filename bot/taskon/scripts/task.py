import json
from typing import Callable

import aiohttp
from better_automation.twitter.errors import HTTPException

from bot.logger import logger
from bot.taskon import TaskonAccount, TaskonAPI
from bot.taskon.models import TaskInfo
from .auth import authenticated_twitter
from .user import _request_and_set_user_info


async def follow_twitter(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        task_params: dict,
):
    async with authenticated_twitter(session, account) as twitter:
        user_id = task_params["user_to_follow_id"]
        username = task_params["user_to_follow"]
        await twitter.follow(user_id)
        logger.debug(f"{account} (user_id={user_id}) Followed user @{username}")


async def like_tweet(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        task_params: dict,
):
    async with authenticated_twitter(session, account) as twitter:
        tweet_id = task_params["tweet_id"]
        tweet_link = task_params["twitter_link"]
        await twitter.like(tweet_id)
        logger.debug(f"{account} (tweet_id={tweet_id}) Liked tweet {tweet_link}")


async def retweet_tweet(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        task_params: dict,
):
    async with authenticated_twitter(session, account) as twitter:
        tweet_id = task_params["tweet_id"]
        retweet_of = task_params["retweet_of"]
        project_name = task_params["project_name"]
        try:
            await twitter.repost(tweet_id)
        except HTTPException as e:
            if 327 in e.api_codes:
                pass
            else:
                raise
        logger.debug(f"{account} (tweet_id={tweet_id}) Retweeted tweet of user @{retweet_of}")


async def quote_tweet_with_friends_tags(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        task_params: dict,
):
    async with authenticated_twitter(session, account) as twitter:
        tweet_id = task_params["tweet_id"]
        tags_users = task_params["tags_users"]
        friends_count = task_params["friends_count"]
        twitter_handle = task_params["twitter_handle"]
        text = " ".join(["@elonmusk" for _ in range(friends_count)])
        tweet_url = f'https://twitter.com/{twitter_handle}/status/{tweet_id}'
        try:
            await twitter.quote(tweet_url, text)
        except HTTPException as e:
            if 327 in e.api_codes:
                pass
            else:
                raise
        logger.debug(f"{account} (tweet_id={tweet_id}) Quoted tweet of user @{twitter_handle} with text: '{text}'")


async def quote_tweet_with_hashtags(
        session: aiohttp.ClientSession,
        account: TaskonAccount,
        task_params: dict,
):
    async with authenticated_twitter(session, account) as twitter:
        tweet_id = task_params["tweet_id"]
        twitter_handle = task_params["twitter_handle"]
        hashtags = task_params["hash_tag"]
        text = " ".join([f"#{hashtag}" for hashtag in hashtags.split(',')])
        tweet_url = f'https://twitter.com/{twitter_handle}/status/{tweet_id}'
        try:
            await twitter.quote(tweet_url, text)
        except HTTPException as e:
            if 327 in e.api_codes:
                pass
            else:
                raise
        logger.debug(f"{account} (tweet_id={tweet_id}) Quoted tweet of user @{twitter_handle} with text: '{text}'")


class TaskSolver:
    def __init__(
            self,
            template_id: str,
            solver: Callable or None,
            twitter_is_required: bool = False,
            discord_is_required: bool = False,
    ):
        self.template_id = template_id
        self._solver = solver
        self.twitter_is_required = twitter_is_required
        self.discord_is_required = discord_is_required

    async def solve(
            self,
            session: aiohttp.ClientSession,
            taskon: TaskonAPI,
            account: TaskonAccount,
            task_info: TaskInfo,
    ) -> str | None:
        if self._solver is None:
            return

        task_params = json.loads(task_info.params)

        if not account.user_info:
            await _request_and_set_user_info(taskon, account)

        await self._solver(session, account, task_params)


TEMPLATE_ID_TO_TASK_SOLVER = {
    'FollowTwitter': TaskSolver('FollowTwitter', follow_twitter, twitter_is_required=True),
    'RetweetTwitter': TaskSolver('RetweetTwitter', retweet_tweet, twitter_is_required=True),
    'QuoteTweetAndTag': TaskSolver('QuoteTweetAndTag', quote_tweet_with_friends_tags, twitter_is_required=True),
    'QuoteTweetAndHashTag': TaskSolver('QuoteTweetAndHashTag', quote_tweet_with_hashtags, twitter_is_required=True),
    'LikeATweet': TaskSolver('LikeATweet', like_tweet, twitter_is_required=True),
    'JoinDiscord': TaskSolver('JoinDiscord', None, discord_is_required=True),
    'PowTask': TaskSolver('PowTask', None),
    'PowQa': TaskSolver('PowQa', None),
    'PowQaWithAnswer': TaskSolver('PowQaWithAnswer', None),
    'LinkTask': TaskSolver('LinkTask', None),
    'JoinTelegram': TaskSolver('JoinTelegram', None),
    'OuterAPI': TaskSolver('OuterAPI', None),
    'Youtube': TaskSolver('Youtube', None),
    'QuizChoose': TaskSolver('QuizChoose', None),
    'SurveyChoose': TaskSolver('SurveyChoose', None),
    'TokenBalance': TaskSolver('TokenBalance', None),
    'NftHolder': TaskSolver('NftHolder', None),
}
