import os
from dotenv import load_dotenv
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.util import read_abi

load_dotenv(".env")

networks = ["mainnet", "polygon", "avalanche", "arbitrum", "optimism"]
trades = {}
for i in networks:
    trade = DeFiTrade(i, "0xa1BF30455Dc68807711612CD167450fCD0fde502", False, False)
    trades[i] = trade


def test_read_abi_cloud():
    abi = read_abi(filename="aave_addressprovider_v3", cloud=True)
    assert type(abi) == str


def test_build_approval_tx():
    trade = DeFiTrade(
        "mainnet",
        "0xa1BF30455Dc68807711612CD167450fCD0fde502",
        test=False,
        send_tx=False,
    )
    dai = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    spender = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    contract = trade.w3.eth.contract(dai, abi=(read_abi(os.getenv("ERC20"), "token")))
    tx = contract.functions.approve(spender, int(1000))

    built_tx = tx.build_transaction({"from": trade.user})
    print(built_tx)
    print(trade.w3.eth.gas_price)


def test_build_tx_arbitrum():
    trade = trades["arbitrum"]
    token = "0x905dfCD5649217c42684f23958568e533C711Aa3"
    spender = "0xa1BF30455Dc68807711612CD167450fCD0fde502"
    contract = trade.w3.eth.contract(token, abi=(read_abi(os.getenv("ERC20"), "token")))
    tx = contract.functions.approve(spender, int(1000))

    res = trade._build_transaction(tx)
    print(res)
