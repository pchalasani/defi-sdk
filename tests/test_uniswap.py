import re
from defi_sdk.integrations.uniswap_v2 import LPTrade
from tests.addresses import (
    FIREBLOCKS_VAULT,
    FIREBLOCKS_ROPSTEN,
    POLYGON_USDC_WETH_LP,
    POLYGON_USDC,
    POLYGON_WETH,
    ROPSTEN_DAI,
    ROPSTEN_DAI_WETH_LP,
    ROPSTEN_WETH,
)
from dotenv import load_dotenv

load_dotenv(".env")
lp_1 = LPTrade(
    lp_address=POLYGON_USDC_WETH_LP,
    exchange="quickswap",
    trade_id="test",
    network="polygon",
    user=FIREBLOCKS_VAULT,
    test=False,
    send_tx=False,
)

lp_2 = LPTrade(
    lp_address=ROPSTEN_DAI_WETH_LP,
    exchange="uniswap",
    trade_id="test",
    network="ropsten",
    user=FIREBLOCKS_ROPSTEN,
    test=True,
    send_tx=False,
)


def test_get_router():
    res = lp_1.get_router()
    assert res.address == "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"


def get_token_info():
    res = lp_1.get_token_info()
    assert res["token1"] == POLYGON_USDC
    assert res["token0"] == POLYGON_WETH


def test_get_lp_amount():
    res = lp_1.get_lp_amount()
    assert res != 0


def test_conversion():
    res = lp_2.execute_conversion_in(100, [ROPSTEN_DAI, ROPSTEN_WETH])
    assert res == True


def test_add_liquidity():
    res = lp_2.add_liquidity(10, 10)
    assert res == True


def test_remove_liquidity():
    res = lp_1.remove_liquidity(100)
    assert res == True
