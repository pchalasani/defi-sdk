import logging
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

test_trade_polygon = DeFiTrade(
    network="polygon",
    user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
    test=False,
    send_tx=False,
)

bridge_polygon = test_trade_polygon.fb_bridge


test_trade_avax = DeFiTrade(
    network="avalanche",
    user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
    test=False,
    send_tx=False,
)
bridge_avax = test_trade_avax.fb_bridge


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


failed_transaction_hash = (
    "0x0fca503da2ae2393d95fb5f3202e2298b3664f0ba851cfb6d3596346b240f37a"
)


# def test_failed_transaction_fireblocks():
#     fb_id = "af888954-2736-4b7f-9ff0-fe6c98b63b7c"
#     res = bridge_polygon.get_fireblocks_transaction(fb_id)
#     print(res["txHash"])
#     assert bridge_polygon.check_tx_status_chain(res["txHash"]) == False


# success_ui = "e2709c61-9950-4d98-902d-4c99aae7d3d5"
# failed_ui = "4911e433-7b69-47c4-9510-2840f0b59d90"
# failed_target_approval_target = "ea78af8c-f286-44e4-a44d-2bd36f8408e6"
# failed_target_token = "31af87fc-2af1-491e-b611-f921d58bb3de"
# pending = "4fbdb452-e14c-4838-afce-9058cebb0aa3"


# def test_failed_2():
#     for i in [
#         success_ui,
#         failed_ui,
#         failed_target_approval_target,
#         failed_target_token,
#         pending,
#     ]:
#         res = bridge_avax.get_fireblocks_transaction(i)
#         print(i)
#         print(res)


# def test_build_approve_transaction(caplog):
#     caplog.set_level(logging.DEBUG)
#     trade = DeFiTrade(
#         network="avalanche",
#         user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
#         test=False,
#         send_tx=True,
#     )
#     joe_lp = "0xf4003F4efBE8691B60249E6afbD307aBE7758adb"
#     joe_router = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
