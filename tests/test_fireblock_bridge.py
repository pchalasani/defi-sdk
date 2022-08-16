import pytest
from defi_sdk.fireblocks_integration.web3_bridge import Web3Bridge, TransferPeerPath
from defi_sdk.defi_trade import DeFiTrade

test_trade = DeFiTrade(
    network="mainnet",
    user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
    test=False,
    send_tx=False,
)

bridge = test_trade.fb_bridge


def test_whitelisting_success():
    whitelisted = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
    res = bridge.check_whitelisting(whitelisted)
    assert res != None
    assert type(res) == TransferPeerPath


def test_whitelisting_failure():
    not_whitelisted = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    with pytest.raises(ValueError):
        bridge.check_whitelisting(not_whitelisted)


def test_whitelisting_approval_tx():
    pass


def test_get_tx_status():
    tx_hash = "0x091d798c91fd1ddc5e14ac49d053dc1bb12dc21adf9a99d309f6e3c5617ee816"
    assert bridge.check_tx_status_chain(tx_hash) == True


def test_fireblocks_completed_tx():
    fireblocks_id = "379822f6-2f88-47e8-9c4d-3031abec837d"
    assert bridge.check_tx_is_completed(fireblocks_id) == True


def test_fireblocks_cancelled():
    fireblocks_id = "b3ec88cb-1151-47f0-8fcc-592c4d7275bf"
    assert bridge.check_tx_is_completed(fireblocks_id) == False
