from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.staking.quickswap import QuickswapLPStaking

from tests.addresses import FIREBLOCKS_VAULT, POLYGON_QUICKSWAP_STAKING
from dotenv import load_dotenv

load_dotenv(".env")


trade = DeFiTrade(
    network="polygon",
    user=FIREBLOCKS_VAULT,
    test=False,
    send_tx=False,
)

stake = QuickswapLPStaking(trade, POLYGON_QUICKSWAP_STAKING)


def test_get_balance():

    res = stake.get_staked_balance()
    assert res != 0


def test_get_rewards():

    res = stake.get_rewards()
    print(res)
    assert res["reward_value"] != 0


def test_unstake():

    res = stake.unstake(10)

    assert res == True
