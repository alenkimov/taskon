from better_automation.utils import copy_file, load_toml
from better_web3 import Chain
from eth_utils import to_wei
from web3.types import Wei

from bot.paths import CONFIG_DIR, DEFAULT_CONFIG_DIR


DEFAULT_CHAINS_TOML = DEFAULT_CONFIG_DIR / "chains.toml"
CHAINS_TOML = CONFIG_DIR / "chains.toml"
copy_file(DEFAULT_CHAINS_TOML, CHAINS_TOML)


def load_chains(chains_data: dict, ensure_chain_id=False, **chain_kwargs) -> dict[int: Chain]:
    chains: dict[int: Chain] = {}
    minimal_balances: dict[int: Wei] = {}
    for chain_id, chain_data in chains_data.items():
        chain_id = int(chain_id)
        if "minimal_balance" in chain_data:
            minimal_balances[chain_id] = to_wei(chain_data.pop("minimal_balance"), "ether")
        if "gas_price" in chain_data:
            chain_data["gas_price"] = to_wei(chain_data["gas_price"], "gwei")
        if "max_fee_per_gas" in chain_data:
            chain_data["max_fee_per_gas"] = to_wei(chain_data["max_fee_per_gas"], "gwei")
        if "max_priority_fee_per_gas" in chain_data:
            chain_data["max_priority_fee_per_gas"] = to_wei(chain_data["max_priority_fee_per_gas"], "gwei")
        chain = Chain(**chain_data, **chain_kwargs)
        if ensure_chain_id and chain.chain_id == chain_id or not ensure_chain_id:
            chains[chain_id] = chain
    return chains, minimal_balances


CHAINS, MINIMAL_BALANCES = load_chains(load_toml(CHAINS_TOML))
