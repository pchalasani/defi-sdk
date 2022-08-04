import logging
import concurrent.futures

from defi_sdk.util import read_abi, get_token_price, exec_concurrent
from defi_sdk.integrations.staking.staking_generic import Staking
from defi_sdk.defi_trade import DeFiTrade


class ConvexStaking(Staking):
    def __init__(self, defi_trade: DeFiTrade, staking_address: str) -> None:
        super().__init__()
        self.trade = defi_trade
        self.staking_contract = self.trade.w3.eth.contract(
            staking_address,
            abi=read_abi(staking_address, "convex_staking", network="mainnet"),
        )

    def get_staked_balance(self):
        return self.staking_contract.functions.balanceOf(self.trade.user).call()

    def stake(self, amount: int):
        tx = self.staking_contract.functions.stake(amount)
        res = self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent convex stake transaction")
        return True

    def unstake(self, amount: int, claim_rewards: bool = False):
        assert (
            amount <= self.get_staked_balance()
        ), "Amount to unstake is greater than staked balance"
        tx = self.staking_contract.functions.withdraw(amount, claim_rewards)
        res = self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent convex unstake transaction")
        return True
