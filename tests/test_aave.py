from defi_sdk.integrations.lending.aave_v3 import AaveV3
from defi_sdk.defi_trade import DeFiTrade
from tests.addresses import (
    FIREBLOCKS_VAULT,
    POLYGON_USDC,
    POLYGON_WETH,
)
from dotenv import load_dotenv

load_dotenv(".env")


trade_polygon = DeFiTrade(
    network="polygon",
    user=FIREBLOCKS_VAULT,
    test=False,
    send_tx=False,
)

aave = AaveV3(trade_polygon)


def test_get_holdings_collateral():
    res = aave.update_holdings(asset=POLYGON_USDC)
    assert res["side"] == "collateral"


def test_get_holdings_debt():

    res = aave.update_holdings(asset=POLYGON_WETH)
    assert res["side"] == "borrow"


def test_borrow_aave_not_send():
    aave.borrow(amount=100, asset=POLYGON_WETH)


def test_aave_get_data():
    from tests.addresses import FIREBLOCKS_FUND

    aave = AaveV3(
        DeFiTrade(network="arbitrum", user=FIREBLOCKS_FUND, test=False, send_tx=False)
    )
    ret = aave.get_health_factor()
    print(ret / pow(10, 18))
    assert ret > 0
