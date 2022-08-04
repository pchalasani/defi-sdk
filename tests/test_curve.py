from dotenv import load_dotenv

load_dotenv(".env")
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.exchange.curve import Curve


trade = DeFiTrade(
    network="mainnet",
    user="0xEA9edA51A472E2C48973245C5bDB79FD32A14089",
    test=False,
    send_tx=False,
)

curve = Curve(trade, "0x9D0464996170c6B9e75eED71c68B99dDEDf279e8")


def test_get_quote():
    res = curve.get_quote(10, 0, 1)
    assert res != 0
