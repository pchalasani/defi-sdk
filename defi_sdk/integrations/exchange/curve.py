import logging
from pytz import UTC

from defi_sdk.util import read_abi
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.exchange.exchange_generic import Exchange


class Curve(Exchange):
    def __init__(
        self,
        defi_trade: DeFiTrade,
        lp_address: str,
    ) -> None:
        super().__init__()
        self.trade: DeFiTrade = defi_trade
        self.lp_contract = self.trade.w3.eth.contract(
            lp_address, abi=read_abi(lp_address, "curve_pool")
        )

    def get_quote(self, amount: int, token_in: int, token_out: int):
        return self.lp_contract.functions.get_dy(token_in, token_out, amount).call()

    def swap(self, amount: int, token_in: int, max_slippage: float = 0.05):
        assert token_in in [0, 1], "token_in must be 0 or 1"
        token_in_address = self.lp_contract.functions.coins(token_in).call()
        assert (
            self.trade.get_current_balance(self.trade.user, token_in_address) >= amount
        ), "Not enough tokens to execute curve swap"
        token_out = int(abs(token_in - 1))
        expected_amount = self.get_quote(amount, token_in, token_out)
        minimum_amount = expected_amount * (1 - max_slippage)
        tx = self.lp_contract.functions.exchange(
            token_in, token_out, amount, minimum_amount
        )
        self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent swap transaction to Curve")
        return True
