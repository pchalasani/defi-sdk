from defi_sdk.integrations.staking import Staking
from tests.addresses import FIREBLOCKS_VAULT, POLYGON_QUICKSWAP_STAKING
from dotenv import load_dotenv

load_dotenv(".env")


def test_get_balance():
    stake = Staking(
        staking_address=POLYGON_QUICKSWAP_STAKING,
        staking_type="quickswap_lp_staking",
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )

    res = stake.get_staked_balance()
    assert res != 0


def test_get_rewards():
    stake = Staking(
        staking_address=POLYGON_QUICKSWAP_STAKING,
        staking_type="quickswap_lp_staking",
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )

    res = stake.get_rewards()
    print(res)
    assert res["reward_value"] != 0


def test_unstake():
    stake = Staking(
        staking_address=POLYGON_QUICKSWAP_STAKING,
        staking_type="quickswap_lp_staking",
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )

    res = stake.unstake(10)

    assert res == True
