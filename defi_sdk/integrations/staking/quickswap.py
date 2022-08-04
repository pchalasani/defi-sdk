import logging
import concurrent.futures

from defi_sdk.util import read_abi, get_token_price, exec_concurrent
from defi_sdk.integrations.staking.staking_generic import Staking
from defi_sdk.defi_trade import DeFiTrade


class QuickswapLPStaking(Staking):
    def __init__(self, defi_trade: DeFiTrade, staking_address: str) -> None:
        super().__init__()
        self.trade = defi_trade
        self.staking_contract = self.trade.w3.eth.contract(
            staking_address,
            abi=read_abi(staking_address, "quickswap_lp_staking", network="polygon"),
        )

    def get_staked_balance(self):
        return self.staking_contract.functions.balanceOf(self.trade.user).call()

    def get_rewards(self):

        functions = [
            self.staking_contract.functions.rewardsTokenA(),
            self.staking_contract.functions.rewardsTokenB(),
            self.staking_contract.functions.earnedA(self.trade.user),
            self.staking_contract.functions.earnedB(self.trade.user),
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(functions)) as pool:
            rewards = [x for x in pool.map(exec_concurrent, functions)]

        token_a_info = get_token_price(rewards[0], chain=self.trade.network)
        token_a_value = (
            token_a_info["price"] * rewards[2] / pow(10, token_a_info["decimals"])
        )

        token_b_info = get_token_price(rewards[1], chain=self.trade.network)
        token_b_value = (
            token_b_info["price"] * rewards[3] / pow(10, token_b_info["decimals"])
        )

        return {
            f"{token_a_info['symbol']}_amount": rewards[2]
            / pow(10, token_a_info["decimals"]),
            f"{token_b_info['symbol']}_amount": rewards[3]
            / pow(10, token_b_info["decimals"]),
            f"{token_a_info['symbol']}_value": token_a_value,
            f"{token_b_info['symbol']}_value": token_b_value,
            "reward_value": token_a_value + token_b_value,
        }

    def unstake(self, amount: int):
        tx = self.staking_contract.functions.withdraw(amount)
        res = self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent quickswap unstake transaction")
        return True

    def stake(self, amount: int):
        tx = self.staking_contract.functions.stake(amount)
        res = self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent quickswap staking transaction")
        return True
