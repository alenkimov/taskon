from eth_typing import ChecksumAddress
from web3.contract.async_contract import AsyncContractFunction
from web3.types import HexStr

from better_web3 import Chain
from better_web3.contract import Contract

from .abi import CAP_MINTER_ABI


class CapMinter(Contract):
    def __init__(self, chain: Chain, address: ChecksumAddress | str, abi=CAP_MINTER_ABI):
        super().__init__(chain, address, abi)

    def mint_function(
            self,
            address: ChecksumAddress,
            campaign_id: int,
            token_uri: str,
            limit: int,
            unsigned: HexStr | str,
            signature: HexStr | str,
    ) -> AsyncContractFunction:
        unsigned = bytes.fromhex(unsigned[2:])
        signature = bytes.fromhex(signature[2:])
        return self.functions.mint(address, campaign_id, token_uri, limit, unsigned, signature)
