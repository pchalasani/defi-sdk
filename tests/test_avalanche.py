import logging
import os
from dotenv import load_dotenv
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.util import read_abi

load_dotenv()


def test_create_trade():
    avalanche_trade = DeFiTrade(
        network="avalanche",
        user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
        test=False,
        send_tx=False,
    )


trade = DeFiTrade(
    network="avalanche",
    user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
    test=False,
    send_tx=True,
)
joe_lp = "0xf4003F4efBE8691B60249E6afbD307aBE7758adb"
joe_router = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"


def test_send_avalanche_approval(caplog):
    caplog.set_level(logging.DEBUG)
    token_contract = trade.w3.eth.contract(
        address=joe_lp, abi=read_abi(address=os.getenv("ERC20"), cloud=True)
    )
    func = token_contract.functions.approve(joe_router, 100)
    trade.send_transaction_fireblocks(func)
