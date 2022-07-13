import os
import concurrent.futures
import logging
from datetime import datetime


from pytz import UTC
from defi_sdk.util import read_abi, exec_concurrent
from defi_sdk.defi_trade import DeFiTrade


class LPTrade(DeFiTrade):
    def __init__(
        self,
        lp_address: str,
        exchange: str,
        token_info: dict = {},
        **kwargs,
    ) -> None:
        DeFiTrade.__init__(self, **kwargs)
        self.lp_contract = self.w3.eth.contract(
            lp_address, abi=read_abi(os.getenv("UNI-PAIR"), "pair")
        )
        self.exchange = exchange
        self.router = self.get_router()
        if token_info == {}:
            self.token_info = self.get_token_info()
        else:
            self.token_info = token_info

    def get_router(self):
        routers = {
            "polygon": {"quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"},
            "ropsten": {"uniswap": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"},
        }
        router_abi = read_abi(os.getenv("UNI-ROUTER"), "router")
        return self.w3.eth.contract(
            routers[self.network][self.exchange], abi=router_abi
        )

    def get_token_info(self):
        func = [
            self.lp_contract.functions.token0(),
            self.lp_contract.functions.token1(),
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(func)) as pool:
            token_addresses = [x for x in pool.map(exec_concurrent, func)]

        tok0 = self.w3.eth.contract(
            token_addresses[0], abi=read_abi(os.getenv("ERC20"), "token")
        )
        tok1 = self.w3.eth.contract(
            token_addresses[1], abi=read_abi(os.getenv("ERC20"), "token")
        )
        func_token = [
            tok0.functions.decimals(),
            tok0.functions.symbol(),
            tok1.functions.decimals(),
            tok1.functions.symbol(),
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(func_token)) as pool:
            token_info = [x for x in pool.map(exec_concurrent, func_token)]

        return {
            "token0": tok0.address,
            "token0_decimals": token_info[0],
            "token0_symbol": token_info[1],
            "token1": tok1.address,
            "token1_decimals": token_info[2],
            "token1_symbol": token_info[3],
        }

    def get_lp_amount(self):
        return self.lp_contract.functions.balanceOf(self.user).call()

    def get_lp_trade(self, lp_token_amount=False):
        if not lp_token_amount:
            lp_token_amount = self.get_lp_amount()

        functions = [
            self.lp_contract.functions.totalSupply(),
            self.lp_contract.functions.getReserves(),
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(functions)) as pool:
            info = [x for x in pool.map(exec_concurrent, functions)]

        share = lp_token_amount / info[0]
        token0_amount = int(share * info[1][0])
        token1_amount = int(share * info[1][1])

        return {
            "token0_amount": token0_amount,
            "token1_amount": token1_amount,
            "lp_tokens": lp_token_amount,
            "total_lp_tokens": info[0],
        }

    def get_quote(self, amount: int, path: list):
        return self.router.functions.getAmountsOut(amount, path).call()

    def execute_conversion_in(
        self, amount: int, path: list, max_slippage: float = 0.05
    ):
        expected_amount_out = self.get_quote(amount, path)[-1]
        logging.info(f"Expected out: {expected_amount_out}")
        min_amount_out = int(expected_amount_out * (1 - max_slippage))
        current_ts = int(datetime.timestamp(datetime.now(UTC)))
        lag = 60 * 5

        self.ensure_approval(self.user, path[0], self.router.address, amount)
        assert self.get_current_balance(self.user, path[0]) >= amount
        swap_tx = self.router.functions.swapExactTokensForTokens(
            amount, min_amount_out, path, self.user, current_ts + lag
        )
        self.send_transaction_fireblocks(swap_tx)
        if self.send_tx:
            logging.info(f"Sent {self.exchange} convert amountIn transaction")
        return True

    def add_liquidity(
        self, token0_amount: int, token1_amount: int, max_slippage: float = 0.02
    ):
        """
        params:
            - quote: amount of quote assets to provide (or current balance if max)
            - base: amount of base assets to provide
            - max slippage allowed for providing liquidity
                - price can move out of balance which then would revert transaction if 0
        """
        current_ts = int(datetime.timestamp(datetime.now(UTC)))
        lag = 60 * 5
        res0, res1, ts = self.lp_contract.functions.getReserves().call()
        p = res0 / res1

        token1_as_token0 = p * token1_amount

        if token0_amount <= token1_as_token0:
            # add liquidity based on token0 amount
            token0_liquidity = token0_amount
            token1_liquidity = int(token0_amount / p)
        else:
            # add liquidity based on token1 amount
            token1_liquidity = token1_amount
            token0_liquidity = int(token1_amount * p)

        token0_minimum = int(token0_liquidity * (1 - max_slippage))
        token1_minimum = int(token1_liquidity * (1 - max_slippage))

        self.ensure_approval(
            self.user,
            self.token_info["token0"],
            self.router.address,
            token0_liquidity,
        )
        self.ensure_approval(
            self.user,
            self.token_info["token1"],
            self.router.address,
            token1_liquidity,
        )

        tx = self.router.functions.addLiquidity(
            self.token_info["token0"],
            self.token_info["token1"],
            token0_liquidity,
            token1_liquidity,
            token0_minimum,
            token1_minimum,
            self.user,
            current_ts + lag,
        )
        self.send_transaction_fireblocks(
            tx,
        )
        if self.send_tx:
            logging.info(f"Sent {self.exchange} add liquidity transaction")
        return True

    def remove_liquidity(self, lp_tokens: int, max_slippage: float = 0.02):
        """
        params:
            - lp_tokens: how many LP tokens to withdraw
            - quote_min: minimum amount of quote tokens to receive
            - base_min: minimum amount of base tokens to receive
        """
        current_ts = int(datetime.timestamp(datetime.now(UTC)))
        lag = 60 * 5

        functions = [
            self.lp_contract.functions.totalSupply(),
            self.lp_contract.functions.getReserves(),
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(functions)) as pool:
            pool = [x for x in pool.map(exec_concurrent, functions)]

        total_lp = pool[0]
        reserve0, reserve1, ts = pool[1]

        share = lp_tokens / total_lp
        token0_minimum = int(share * reserve0 * (1 - max_slippage))
        token1_minimum = int(share * reserve1 * (1 - max_slippage))

        self.ensure_approval(
            self.user, self.lp_contract.address, self.router.address, lp_tokens
        )
        tx = self.router.functions.removeLiquidity(
            self.token_info["token0"],
            self.token_info["token1"],
            lp_tokens,
            token0_minimum,
            token1_minimum,
            self.user,
            current_ts + lag,
        )

        self.send_transaction_fireblocks(tx)
        if self.send_tx:
            logging.info(f"Sent {self.exchange} remove liquidity transaction")
        return True
