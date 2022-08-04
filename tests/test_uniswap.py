from defi_sdk.integrations.exchange.uniswap_v2 import UniswapV2
from defi_sdk.defi_trade import DeFiTrade
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

trade_polygon = DeFiTrade(
    network="polygon",
    user=FIREBLOCKS_VAULT,
    test=False,
    send_tx=False,
)
trade_ropsten = DeFiTrade(
    network="ropsten",
    user=FIREBLOCKS_ROPSTEN,
    test=True,
    send_tx=False,
)

lp_polygon = UniswapV2(
    lp_address=POLYGON_USDC_WETH_LP,
    exchange="quickswap",
    defi_trade=trade_polygon,
)

lp_ropsten = UniswapV2(
    lp_address=ROPSTEN_DAI_WETH_LP,
    exchange="uniswap",
    defi_trade=trade_ropsten,
)


def test_get_router():
    res = lp_polygon.get_router()
    assert res.address == "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"


def get_token_info():
    res = lp_polygon.get_token_info()
    assert res["token1"] == POLYGON_USDC
    assert res["token0"] == POLYGON_WETH


def test_get_lp_amount():
    res = lp_polygon.get_lp_amount()
    assert res != 0


def test_conversion():
    res = lp_ropsten.swap(100, [ROPSTEN_DAI, ROPSTEN_WETH])
    assert res == True


def test_add_liquidity():
    res = lp_ropsten.add_liquidity(10, 10)
    assert res == True


def test_remove_liquidity():
    res = lp_ropsten.remove_liquidity(100)
    assert res == True
