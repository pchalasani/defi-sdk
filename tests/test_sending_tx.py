from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.uniswap_v2 import LPTrade
import logging
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

import os

lp_2 = LPTrade(
    lp_address=ROPSTEN_DAI_WETH_LP,
    exchange="uniswap",
    network="ropsten",
    user=FIREBLOCKS_ROPSTEN,
    test=True,
    send_tx=True,
)


def test_uniswap_tx(caplog):
    caplog.set_level(logging.INFO)
    res = lp_2.execute_conversion_in(100, [ROPSTEN_DAI, ROPSTEN_WETH])
    print(res)
