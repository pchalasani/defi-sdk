from defi_sdk.integrations.aave_v3 import AaveTrade
from tests.addresses import (
    FIREBLOCKS_VAULT,
    POLYGON_USDC,
    POLYGON_WETH,
)
from dotenv import load_dotenv

load_dotenv(".env")


def test_get_holdings_collateral():

    aave = AaveTrade(
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )
    res = aave.update_holdings(asset=POLYGON_USDC)
    assert res["side"] == "collateral"


def test_get_holdings_debt():
    aave = AaveTrade(
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )
    res = aave.update_holdings(asset=POLYGON_WETH)
    assert res["side"] == "borrow"


def test_borrow_aave_not_send():
    aave = AaveTrade(
        network="polygon",
        user=FIREBLOCKS_VAULT,
        test=False,
        send_tx=False,
    )
    aave.borrow_aave_v3(amount=100, asset=POLYGON_WETH)
