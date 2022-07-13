import logging
import concurrent.futures

from defi_sdk.util import read_abi, get_token_price, exec_concurrent
from defi_sdk.trade import Trade


class Staking(Trade):
    def __init__(self, staking_address, staking_type, **kwargs) -> None:
        Trade.__init__(self, **kwargs)

        self.staking_type = staking_type
        if self.staking_type == "quickswap_lp_staking":
            self.staking_contract = self.w3.eth.contract(
                staking_address,
                abi=read_abi(
                    staking_address, "quickswap_lp_staking", network="polygon"
                ),
            )
        else:
            raise ValueError("Staking type not implemented")

    def get_staked_balance(self):
        if self.staking_type == "quickswap_lp_staking":
            return self.staking_contract.functions.balanceOf(self.user).call()

    def get_rewards(self):
        if self.staking_type == "quickswap_lp_staking":
            functions = [
                self.staking_contract.functions.rewardsTokenA(),
                self.staking_contract.functions.rewardsTokenB(),
                self.staking_contract.functions.earnedA(self.user),
                self.staking_contract.functions.earnedB(self.user),
            ]
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(functions)
            ) as pool:
                rewards = [x for x in pool.map(exec_concurrent, functions)]

            token_a_info = get_token_price(rewards[0], chain=self.network)
            token_a_value = (
                token_a_info["price"] * rewards[2] / pow(10, token_a_info["decimals"])
            )

            token_b_info = get_token_price(rewards[1], chain=self.network)
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

    def unstake(self):
        if self.staking_type == "quickswap_lp_staking":
            tx = self.staking_contract.functions.withdraw(100)
            res = self.send_transaction_fireblocks(tx)
            if self.send_tx:
                logging.info("Sent quickswap unstake transaction")
            return True
