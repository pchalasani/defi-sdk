from dotenv import load_dotenv
from defi_sdk.defi_trade import DeFiTrade

load_dotenv(".env")
networks = ["mainnet", "polygon", "avalanche", "arbitrum", "optimism"]
trades = {}
for i in networks:
    trade = DeFiTrade(i, "0xa1BF30455Dc68807711612CD167450fCD0fde502", False, False)
    trades[i] = trade


def test_get_eth_feehistory():
    for network, trade in trades.items():
        current_block = trade.w3.eth.get_block_number()
        try:
            fee_hist = trade.w3.eth.fee_history(
                block_count=100, newest_block=current_block
            )
            print(f"{network}: OK")
        except Exception as e:
            print(e, network)
            raise ValueError(e)
