CONVEX_STAKING = "0x3Fe65692bfCD0e6CF84cB1E7d24108E434A7587e"

from dotenv import load_dotenv

load_dotenv(".env")
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.staking.convex import ConvexStaking


trade = DeFiTrade(
    network="mainnet",
    user="0xEA9edA51A472E2C48973245C5bDB79FD32A14089",
    test=False,
    send_tx=False,
)

stake = ConvexStaking(trade, CONVEX_STAKING)


def test_get_balance():
    res = stake.get_staked_balance()
    assert res != 0


def test_unstake():
    res = stake.unstake(10)
    assert res == True


def test_unstake_claim():
    res = stake.unstake(10, True)
    assert res == True
