import logging
import requests
import os
from defi_sdk.util import read_abi
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.lending.lending_generic import Lending


class AaveV2(Lending):
    def __init__(
        self,
        defi_trade: DeFiTrade,
        address_provider="0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5",
    ) -> None:
        super().__init__()
        self.trade = defi_trade
        provider_contract = self.trade.w3.eth.contract(
            self.trade.w3.toChecksumAddress(address_provider),
            abi=read_abi(address_provider, filename="aave_addressprovider_v2"),
        )
        pool = provider_contract.functions.getLendingPool().call()
        self.aave_lending_pool = self.trade.w3.eth.contract(
            pool,
            abi=read_abi(pool, filename="aave_pool_v3"),
        )

    def update_holdings(self, asset):
        address = self.trade.user.lower()
        if self.trade.network == "polygon":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon"
        else:
            raise ValueError(
                f"Aave subgraph not defined for this network: {self.trade.network}"
            )
        query = """
        query ($user: String!)
            {
                userReserves(where: {user: $user}) {
                    id
                    currentATokenBalance
                    currentVariableDebt
                    currentStableDebt
                    reserve {
                        id
                        underlyingAsset
                        name
                        decimals
                        symbol
                    vToken {
                        id
                    }
                    sToken {
                            id
                    }
                    aToken {
                        id
                    }
                    }
                }
            }
        """

        variables = {"user": address}
        header = {"Content-Type": "application/json"}

        r = requests.post(
            url,
            headers=header,
            json={"query": query, "variables": variables},
        )
        for i in r.json()["data"]["userReserves"]:
            if asset.lower() == i["reserve"]["underlyingAsset"]:
                val = {
                    "address": self.trade.w3.toChecksumAddress(
                        i["reserve"]["underlyingAsset"]
                    ),
                    "name": i["reserve"]["name"],
                    "symbol": i["reserve"]["symbol"],
                    "decimals": int(i["reserve"]["decimals"]),
                }

                if int(i["currentStableDebt"]) != 0:
                    cont = self.trade.w3.eth.contract(
                        self.trade.w3.toChecksumAddress(i["reserve"]["sToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "borrow"
                if int(i["currentVariableDebt"]) != 0:
                    cont = self.trade.w3.eth.contract(
                        self.trade.w3.toChecksumAddress(i["reserve"]["vToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "borrow"
                if int(i["currentATokenBalance"]) != 0:
                    cont = self.trade.w3.eth.contract(
                        self.trade.w3.toChecksumAddress(i["reserve"]["aToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "collateral"
                val["amount"] = cont.functions.balanceOf(self.trade.user).call()
                return val

    def borrow(self, amount: int, asset):
        tx = self.aave_lending_pool_v3.functions.borrow(
            asset, amount, 2, 0, self.trade.user
        )
        self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent Aave v2 borrow transaction")
        return True

    def repay(self, amount: int, asset: str):
        assert (
            self.trade.get_traded_balance(self.trade.user, asset) >= amount
        ), "Not enough balance to repay"
        self.trade.ensure_approval(
            self.trade.user, asset, self.aave_lending_pool, amount
        )
        tx = self.aave_lending_pool.functions.repay(asset, amount, 2, self.trade.user)
        self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent Aave v2 repay transaction")
        return True
