from typing import Any

from pydantic import BaseModel, Field


class Sns(BaseModel):
    sns_type: str
    sns_id: str
    sns_user_name: str
    bind_time: int


class BUser(BaseModel):
    verified: bool
    registered: bool
    user_name: str


class Address(BaseModel):
    chain_type: str
    address: str
    bind_time: int


class Domains(BaseModel):
    jaz: str
    bit: str
    spaceid: str


class LandingStatus(BaseModel):
    completed_common_campaign: bool
    completed_landing_task: bool
    completed_landing_campaign: bool
    completed_exclusive_campaign: bool
    exclusive_campaign_expired: bool


class UserInfo(BaseModel):
    id: int
    avatar: str
    user_name: str
    sns: list[Sns]
    b_user: BUser
    address: list[Address]
    roles: list[str]
    domains: Domains
    register_time: int
    landing_status: LandingStatus
    bound_google_auth: bool
    invite_code: str
    exp: int
    next_level_exp: int
    invited_user_num: int
    next_level_invited_user_num: int
    submitted_campaign_count: int
    next_level_submitted_campaign_count: int
    user_level: int
    is_operator: bool
    operator_account_id_type: str
    operator_account_id: str
    operator_account_name: str


class Audit(BaseModel):
    result: str
    comment: str


class TaskInfo(BaseModel):
    id: int
    template_id: str
    params: str


class RewardParams(BaseModel):
    per_amount: int


class QualifierReward(BaseModel):
    reward_type: str
    reward_params: RewardParams
    reward_distribute_type: str
    reward_distributed_by_type: str
    reward_desc: str


class WinnerReward(BaseModel):
    reward_type: str
    reward_params: dict
    reward_distribute_type: str
    reward_distributed_by_type: str
    reward_desc: str
    chain_types: list[str]


class CampaignInfo(BaseModel):
    id: int
    name: str
    desc: str
    owner_id: int
    owner_name: str
    owner_avatar: str
    owner_address: str
    owner_verified: bool
    image: str
    recaptcha: bool
    eligibility_express: str
    is_draft: bool
    is_removed: bool
    is_end: bool
    campaign_level: int
    start_time: int
    end_time: int
    max_winners: int
    winner_draw_type: str
    automatically_winner_draw_type: str
    audit: Audit
    eligs: list
    tasks: list[TaskInfo]
    qualifier_rewards: list[QualifierReward]
    winner_rewards: list[WinnerReward]
    from_supported_country: bool
    is_landing_campaign: bool
    is_exclusive_campaign: bool
    share_url: str


class Statistics(BaseModel):
    visitor_number: int
    participant_number: int
    submitter_number: int
    qualifier_number: int
    winner_number: int


class Generated(BaseModel):
    winner_generated: bool
    reward_generated: bool
    all_task_qualifier_generated: bool


class CampaignStatusInfo(BaseModel):
    statistics: Statistics
    generated: Generated


class UserStatus(BaseModel):
    is_visitor: bool
    is_participant: bool
    is_submitter: bool
    is_qualifier: bool
    is_winner: bool
    submit_failed: bool


class TaskStatusDetail(BaseModel):
    is_submitter: bool


class UserCampaignStatus(BaseModel):
    user_status: UserStatus
    task_status_details: list[TaskStatusDetail]
    campaign_eligible: str
    campaign_eligible_details: Any
    winner_rewards: Any
    qualifier_rewards: Any


class WinnerInfo(BaseModel):
    user_id: int
    user_address: str
    user_name: str
    avatar: str
    amount: str


class MintData(BaseModel):
    hash: str
    token_uri: str
    signature: str
    campaign_id: int
    contract_address: str
    total: int
