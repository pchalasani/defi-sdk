import requests
import os
from defi_sdk.util import read_abi
from defi_sdk.trade import Trade


class AaveTrade(Trade):
    def __init__(
        self, address_provider="0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb", **kwargs
    ) -> None:
        Trade.__init__(self, **kwargs)
        provider_contract = self.w3.eth.contract(
            self.w3.toChecksumAddress(address_provider),
            abi=read_abi(
                address_provider, "aave_addressprovider_v3", network="polygon"
            ),
        )
        pool = provider_contract.functions.getPool().call()
        self.aave_lending_pool_v3 = self.w3.eth.contract(
            pool,
            abi=read_abi(
                # pool implementation, can change...
                "0xDF9e4ABdbd94107932265319479643D3B05809dc",
                "aave_pool_v3",
                network="polygon",
            ),
        )

    def update_holdings(self, asset):
        address = self.user.lower()
        if self.network == "polygon":
            url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon"
        else:
            raise ValueError(
                f"Aave subgraph not defined for this network: {self.network}"
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
                    "address": self.w3.toChecksumAddress(
                        i["reserve"]["underlyingAsset"]
                    ),
                    "name": i["reserve"]["name"],
                    "symbol": i["reserve"]["symbol"],
                    "decimals": int(i["reserve"]["decimals"]),
                }

                if int(i["currentStableDebt"]) != 0:
                    cont = self.w3.eth.contract(
                        self.w3.toChecksumAddress(i["reserve"]["sToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "borrow"
                if int(i["currentVariableDebt"]) != 0:
                    cont = self.w3.eth.contract(
                        self.w3.toChecksumAddress(i["reserve"]["vToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "borrow"
                if int(i["currentATokenBalance"]) != 0:
                    cont = self.w3.eth.contract(
                        self.w3.toChecksumAddress(i["reserve"]["aToken"]["id"]),
                        abi=read_abi(os.getenv("UNI-PAIR"), "pair"),
                    )
                    val["side"] = "collateral"
                balance = cont.functions.balanceOf(self.user).call()
                val["amount"] = balance / pow(10, val["decimals"])
                return val

    def borrow_aave_v3(self, amount: int, asset):
        tx = self.aave_lending_pool_v3.functions.borrow(asset, amount, 2, 0, self.user)
        self.send_transaction_fireblocks(tx)
        return True

    def repay_aave_v3(self, amount: int, asset):
        tx = self.aave_lending_pool_v3.functions.repay(asset, amount, 2, self.user)
        self.send_transaction_fireblocks(tx)
        return True
