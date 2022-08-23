import logging
import requests
import os
from defi_sdk.util import read_abi
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.lending.lending_generic import Lending


class AaveV3(Lending):
    def __init__(
        self,
        defi_trade: DeFiTrade,
        address_provider="0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    ) -> None:
        super().__init__()
        self.trade = defi_trade
        provider_contract = self.trade.w3.eth.contract(
            self.trade.w3.toChecksumAddress(address_provider),
            abi=read_abi(filename="aave_addressprovider_v3", cloud=True),
        )
        pool = provider_contract.functions.getPool().call()
        self.aave_lending_pool_v3 = self.trade.w3.eth.contract(
            pool,
            abi=read_abi(filename="aave_pool_v3", cloud=True),
        )

    def update_holdings(self, asset):
        address = self.trade.user.lower()
        if self.trade.network == "polygon":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon"
        elif self.trade.network == "arbitrum":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum"
        elif self.trade.network == "optimism":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-optimism"
        elif self.trade.network == "avalanche":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-avalanche"

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
            logging.info("Sent Aave v3 borrow transaction")
        return True

    def repay(self, amount: int, asset):
        self.trade.ensure_approval(
            self.trade.user, asset, self.aave_lending_pool_v3.address, amount
        )
        tx = self.aave_lending_pool_v3.functions.repay(
            asset, amount, 2, self.trade.user
        )
        self.trade.send_transaction_fireblocks(tx)
        if self.trade.send_tx:
            logging.info("Sent Aave v3 repay transaction")
        return True
