import logging
import os
import requests
from enum import Enum
from defi_sdk.util import read_abi
from defi_sdk.integrations.staking.staking_generic import Staking
from defi_sdk.integrations.exchange.uniswap_v2 import UniswapV2
from defi_sdk.defi_trade import DeFiTrade

from web3.constants import MAX_INT


class HomoraExchange(Enum):
    TraderJoe = "traderjoe"


class AlphaHomoraStaking(Staking):
    def __init__(
        self,
        defi_trade: DeFiTrade,
        exchange: HomoraExchange,
        lp_token_address: str,
        bank_address: str,
        spell_address: str,
        staking_address: str,
        wrapper_address: str,
    ) -> None:
        super().__init__()
        self.trade = defi_trade
        self.pool_id = 0
        if self.trade.network == "avalanche":
            # bank is the contract that manages most of the staking
            self.bank = self.trade.w3.eth.contract(
                self.trade.w3.toChecksumAddress(bank_address),
                abi=read_abi(filename="homora_bank", network="avalanche"),
            )

            if exchange == HomoraExchange.TraderJoe:
                # represents the liquidity pool
                self.lp = UniswapV2(
                    self.trade,
                    self.trade.w3.toChecksumAddress(lp_token_address),
                    "traderjoe",
                )
                self.spell = self.trade.w3.eth.contract(
                    self.trade.w3.toChecksumAddress(spell_address),
                    abi=read_abi(filename="homora_spell"),
                )
                self.wrapper = self.trade.w3.eth.contract(
                    self.trade.w3.toChecksumAddress(wrapper_address),
                    abi=read_abi(filename="homoraboostedmasterchef"),
                )
                self.staking = self.trade.w3.eth.contract(
                    self.trade.w3.toChecksumAddress(staking_address),
                    abi=read_abi(filename="homorastaking"),
                )
            else:
                raise ValueError(
                    f"Exchange {exchange} of type {type(exchange)} not supported"
                )
            self.position_id = self.get_position_id()
            self.pool_id, _ = self.decode_collid(self.position_id)
        else:
            raise ValueError(f"{self.trade.network} not supported for AlphaHomora")

    # Duplicates get_position_info
    def get_position(self):
        url = "https://api.thegraph.com/subgraphs/name/alphafinancelab/alpha-homora-v2-avax"
        query = """
            query ($owner: String!) {
                positions(where: {owner: $owner}) {
                    owner
                    pid
                    collateralSize
                    collateralToken {
                        amount
                        token
                    }
                }
                }
        """

        variables = {"owner": self.trade.user.lower()}
        header = {"Content-Type": "application/json"}

        r = requests.post(
            url,
            headers=header,
            json={"query": query, "variables": variables},
        )
        return r.json()

    def get_position_id(self) -> int:
        res = self.get_position()
        print(res)
        for i in res["data"]["positions"]:
            if (
                int(i["collateralSize"]) != 0
                and i["collateralToken"]["token"].lower()
                == self.wrapper.address.lower()
            ):
                return int(i["pid"])
        raise ValueError(
            f"No position found for wrapper address {self.wrapper.address}: {res}"
        )

    def get_pos(self):
        """
        Returns:
             {
                'color': '#3a71be',
                'exchange': {
                        'logo': '/static/logos/exchange/traderjoe.png',
                        'name': 'Trader Joe',
                        'reward': {
                                'rewardTokenAddress': '0x6e84a6216ea6dacc71ee8e6b0a5b7322eebc0fdd',
                                'tokenName': 'JOE'
                            },
                        'stakingAddress': '0x4483f0b6e2f5486d06958c20f8c39a7abe87bf8f'
                    },
                'key': 'wchef-0xab80758cec0a69a49ed1c9b3f114cf98118643f0-0',
                'lpTokenAddress': '0xf4003f4efbe8691b60249e6afbd307abe7758adb',
                'name': 'AVAX/USDC',
                'pid': 0,
                'spellAddress': '0x28f1bdbc52ad1aaab71660f4b33179335054be6a',
                'tokens': [
                    '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7',
                    '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e'
                    ],
                'type': 'Yield Farming',
                'wTokenAddress': '0xab80758cec0a69a49ed1c9b3f114cf98118643f0',
                'wTokenType': 'WBoostedMasterChefJoe'},
        """

        r = requests.get("https://homora-api.alphafinance.io/v2/43114/pools")
        if r.status_code != 200:
            raise Exception(f"Could not fetch position: {r.status_code, r.text}")
        else:
            print(r.json())

    def get_rewards(self):
        print(self.wrapper.all_functions())
        pid, entryRewardPerShare = self.decode_collid(self.position_id)
        print(pid, entryRewardPerShare)
        pool_info = self.staking.functions.poolInfo(pid).call()
        print(pool_info)

    def get_principal(self):
        position_info = self.bank.functions.getPositionInfo(self.position_id).call()
        current_lp_balance = position_info[-1]
        # Use the uniswapv2 integration to get LP status using position holdings
        holdings = self.lp.get_trade(current_lp_balance)
        for i in ["token0", "token1"]:
            # find how much debt this position has in both assets
            borrowed_amount = self.bank.functions.borrowBalanceCurrent(
                self.position_id, self.lp.token_info[i]
            ).call()
            holdings[f"{i}_borrow"] = borrowed_amount
        return holdings

    def decode_collid(self, position_id: int) -> list:
        return self.wrapper.functions.decodeId(position_id).call()

    def _encode_removal(
        self,
        fn_name,
        token0,
        token1,
        amtLPTake,
        amtLPWithdraw,
        amtARepay,
        amtBRepay,
        amtLPRepay,
        amtAMin,
        amtBMin,
    ):
        return self.spell.encodeABI(
            fn_name=fn_name,
            args=[
                token0,
                token1,
                (
                    amtLPTake,
                    amtLPWithdraw,
                    amtARepay,
                    amtBRepay,
                    amtLPRepay,
                    amtAMin,
                    amtBMin,
                ),
            ],
        )

    def _encode_increase(
        self,
        fn_name,
        token0,
        token1,
        amtAUser,
        amtBUser,
        amtLPUser,
        amtABorrow,
        amtBBorrow,
        amtLPBorrow,
        amtAMin,
        amtBMin,
        pool_id,
    ):
        return self.spell.encodeABI(
            fn_name=fn_name,
            args=[
                token0,
                token1,
                (
                    amtAUser,
                    amtBUser,
                    amtLPUser,
                    amtABorrow,
                    amtBBorrow,
                    amtLPBorrow,
                    amtAMin,
                    amtBMin,
                ),
                pool_id,
            ],
        )

    def unstake(self, position_update):
        token0 = self.lp.token_info["token0"]
        token1 = self.lp.token_info["token1"]

        # set amount to take to maximum
        amtLPTake = int(MAX_INT, 16)
        amtLPWithdraw = 0

        # if there is debt, repay all
        amtARepay = position_update["token0_borrow"]
        if amtARepay > 0:
            amtARepay = int(MAX_INT, 16)
        amtBRepay = position_update["token1_borrow"]
        if amtBRepay > 0:
            amtBRepay = int(MAX_INT, 16)
        amtLPRepay = 0

        amtAMin = 0
        amtBMin = 0
        param = self._encode_removal(
            fn_name="removeLiquidityWMasterChef",
            token0=token0,
            token1=token1,
            amtLPTake=amtLPTake,
            amtLPWithdraw=amtLPWithdraw,
            amtARepay=amtARepay,
            amtBRepay=amtBRepay,
            amtLPRepay=amtLPRepay,
            amtAMin=amtAMin,
            amtBMin=amtBMin,
        )
        tx = self.bank.functions.execute(self.position_id, self.spell.address, param)
        self.trade.send_transaction_fireblocks(tx)

    def calculate_leverage_amounts(
        self, quote_balance, current_price, leverage, slippage=0.05
    ):
        # price is main token / other token
        expected_lp_value = quote_balance * leverage
        required_borrow_value = expected_lp_value - quote_balance

        # for leverage <= 2, only borrow in base token
        if leverage < 2:
            base_borrow = required_borrow_value / current_price
            quote_borrow = 0
        else:
            quote_share = expected_lp_value / 2
            quote_borrow = quote_share - quote_balance
            base_borrow = quote_share / current_price

        quote_min = (quote_borrow + quote_balance) * (1 - slippage)
        base_min = (base_borrow + quote_balance) * (1 - slippage)

        return {
            "amount_quote": quote_balance,
            "amount_base": 0,
            "borrow_quote": quote_borrow,
            "borrow_base": base_borrow,
            "quote_min": quote_min,
            "base_min": base_min,
        }

    def stake(self, token0_amount, token1_amount, leverage, slippage=0.05):
        # At this time only supplying the quote token (stablecoin)
        # Leverage is used to detemine how much of the risky asset (and stablecoin when leverage > 2) to borrow
        pid = 0
        token0 = self.lp.token_info["token0"]
        token1 = self.lp.token_info["token1"]
        if token0_amount != 0:
            quote = self.lp.get_quote(token0_amount, [token0, token1])
            price = quote[1] / quote[0]
            amounts = self.calculate_leverage_amounts(
                token0_amount, price, leverage, slippage
            )
            amtAUser = token0_amount
            amtBUser = 0
            amtLPUser = 0
            amtABorrow = int(amounts["borrow_quote"])
            amtBBorrow = int(amounts["borrow_base"])
            amtLPBorrow = 0
            amtAMin = int(amounts["quote_min"])
            amtBMin = int(amounts["base_min"])
        else:
            quote = self.lp.get_quote(token1_amount, [token1, token0])
            price = quote[0] / quote[1]
            amounts = self.calculate_leverage_amounts(
                token1_amount, price, leverage, slippage
            )
            amtAUser = 0
            amtBUser = token1_amount
            amtLPUser = 0
            amtABorrow = int(amounts["borrow_base"])
            amtBBorrow = int(amounts["borrow_quote"])
            amtLPBorrow = 0
            amtAMin = int(amounts["base_min"])
            amtBMin = int(amounts["quote_min"])

        amtAMin = 0
        amtBMin = 0
        param = self._encode_increase(
            fn_name="addLiquidityWMasterChef",
            token0=token0,
            token1=token1,
            amtAUser=amtAUser,
            amtBUser=amtBUser,
            amtLPUser=amtLPUser,
            amtABorrow=amtABorrow,
            amtBBorrow=amtBBorrow,
            amtLPBorrow=amtLPBorrow,
            amtAMin=amtAMin,
            amtBMin=amtBMin,
            pool_id=pid,
        )
        tx = self.bank.functions.execute(pid, self.spell.address, param)
        self.trade.send_transaction_fireblocks(tx)

    def calculate_adjustment_old(
        self, lp_quote, lp_base, borrow_quote, borrow_base, target_leverage
    ):
        """
        Based on current holdings calculate how borrow and LP must be adjusted to reach target leverage.
        quote is neutral asset (USDC), base is risky asset which we want to have hedged
        """
        price = lp_quote / lp_base

        # calculate how much borrowing of base must be adjusted
        borrow_adjustment = lp_base - borrow_base
        new_borrow = borrow_base + borrow_adjustment
        adjusted_position_value = (lp_quote - borrow_quote) + (
            lp_base - new_borrow
        ) * price

        # calculate what is the leverage after position is hedged
        # leverage is defined as LP value / net position value
        adjusted_leverage = (lp_quote + lp_base * price) / adjusted_position_value
        # how far away are we from the target leverage
        # target 3, current 2 = 1.5, we must increase LP size by 1.5
        leverage_ratio = target_leverage / adjusted_leverage

        # adjust lp based on the ratio
        new_lp_quote = lp_quote * leverage_ratio
        new_lp_base = lp_base * leverage_ratio
        lp_quote_adjustment = new_lp_quote - lp_quote
        lp_base_adjustment = new_lp_base - lp_base

        # quote borrow needs to be adjusted as much as LP
        borrow_quote_adjustment = lp_quote_adjustment
        # risky borrow needs to be also adjusted as much as LP + adjustment on
        borrow_base_adjustment = lp_base_adjustment + borrow_adjustment

        return {
            "borrow_quote": borrow_quote_adjustment,
            "borrow_base": borrow_base_adjustment,
            "lp_quote": lp_quote_adjustment,
            "lp_base": lp_base_adjustment,
        }

    def calculate_adjustment(
        self, lp_quote, lp_base, borrow_quote, borrow_base, target_leverage
    ):
        """
        updated version of the above function
        Instead of deriving amounts by starting from rebalancing borrow, calculate it from net value
        """
        price = lp_quote / lp_base
        lp_value = lp_quote + lp_base * price
        borrow_value = borrow_quote + borrow_base * price
        net_value = lp_value - borrow_value
        logging.debug(f"VALUE BEFORE: {net_value}")
        # As leverage = LP value / net value, we calculate what is our goal LP
        target_lp_value = net_value * target_leverage
        target_lp_quote = target_lp_value / 2
        target_lp_base = target_lp_quote / price

        # borrowing base should equal base in LP
        target_borrow_base = target_lp_base
        # borrowing quote is how much we need to add to reach LP
        target_borrow_quote = target_lp_quote - net_value

        borrow_quote_adjustment = target_borrow_quote - borrow_quote
        borrow_base_adjustment = target_borrow_base - borrow_base
        lp_quote_adjustment = target_lp_quote - lp_quote
        lp_base_adjustment = target_lp_base - lp_base

        value_after = (
            target_lp_quote
            + target_lp_base * price
            - target_borrow_quote
            - target_borrow_base * price
        )
        logging.debug(f"VALUE AFTER: {value_after}")

        if value_after - 1 > net_value:
            logging.error(
                f"ERROR: value after is higher than before, before: {net_value} after: {value_after}"
            )

        return {
            "borrow_quote": borrow_quote_adjustment,
            "borrow_base": borrow_base_adjustment,
            "lp_quote": lp_quote_adjustment,
            "lp_base": lp_base_adjustment,
        }

    def increase_borrow(self, borrowAAdjustment, borrowBAdjustment):
        token0 = self.lp.token_info["token0"]
        token1 = self.lp.token_info["token1"]
        param = self._encode_increase(
            fn_name="addLiquidityWMasterChef",
            token0=token0,
            token1=token1,
            amtAUser=0,
            amtBUser=0,
            amtLPUser=0,
            amtABorrow=borrowAAdjustment,
            amtBBorrow=borrowBAdjustment,
            amtLPBorrow=0,
            amtAMin=0,
            amtBMin=0,
            pool_id=self.pool_id,
        )
        tx = self.bank.functions.execute(self.position_id, self.spell.address, param)
        self.trade.send_transaction_fireblocks(tx)

    def decrease_borrow(
        self, lpAAdjustment, lpBAdjustment, borrowAAdjustment, borrowBAdjustment
    ):
        current_holdings = self.get_principal()
        share_of_lp_a = abs(lpAAdjustment) / current_holdings["token0"]
        share_of_lp_b = abs(lpBAdjustment) / current_holdings["token1"]
        average_share_lp = (share_of_lp_a + share_of_lp_b) / 2
        lp_withdrawal = int(average_share_lp * current_holdings["lp_tokens"])

        token0 = self.lp.token_info["token0"]
        token1 = self.lp.token_info["token1"]

        print("lp_withdrawal", lp_withdrawal)
        print("borrowAAdjustment", borrowAAdjustment)
        print("borrowBAdjustment", borrowBAdjustment)

        price = current_holdings["token1"] / current_holdings["token0"]
        lp_adjustment_value = lpAAdjustment * price + lpBAdjustment
        borrow_adjustment_value = borrowAAdjustment * price + borrowBAdjustment
        print("lp_adjustment_value", lp_adjustment_value)
        print("borrow_adjustment_value", borrow_adjustment_value)

        param = self._encode_removal(
            fn_name="removeLiquidityWMasterChef",
            token0=token0,
            token1=token1,
            amtLPTake=lp_withdrawal,
            amtLPWithdraw=0,
            amtARepay=-borrowAAdjustment,
            amtBRepay=-borrowBAdjustment,
            amtLPRepay=0,
            amtAMin=0,
            amtBMin=0,
        )
        tx = self.bank.functions.execute(self.position_id, self.spell.address, param)
        self.trade.send_transaction_fireblocks(tx)

    def adjust_position(
        self, lpAAdjustment, lpBAdjustment, borrowAAdjustment, borrowBAdjustment
    ):

        if borrowAAdjustment < 0 and borrowBAdjustment < 0:
            self.decrease_borrow(
                lpAAdjustment, lpBAdjustment, borrowAAdjustment, borrowBAdjustment
            )
        elif borrowAAdjustment > 0 and borrowBAdjustment > 0:
            self.increase_borrow(borrowAAdjustment, borrowBAdjustment)

        else:
            raise Exception(
                "Invalid borrow adjustment, both must be positive or negative"
            )
