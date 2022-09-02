import logging
from dotenv import load_dotenv

from defi_sdk.util import get_web3

load_dotenv(".env")
from defi_sdk.defi_trade import DeFiTrade
from defi_sdk.integrations.staking.alphahomora import AlphaHomoraStaking, HomoraExchange


trade = DeFiTrade(
    network="avalanche",
    user="0xa1BF30455Dc68807711612CD167450fCD0fde502",
    test=False,
    send_tx=True,
    vault_account_id=4,
)

stake = AlphaHomoraStaking(
    trade,
    exchange=HomoraExchange.TraderJoe,
    bank_address="0x376d16C7dE138B01455a51dA79AD65806E9cd694",
    spell_address="0x28F1BdBc52Ad1aAab71660f4B33179335054BE6A",
    lp_token_address="0xf4003f4efbe8691b60249e6afbd307abe7758adb",
    wrapper_address="0xAb80758cEC0A69a49Ed1c9B3F114cF98118643f0",
    staking_address="0x4483f0b6e2f5486d06958c20f8c39a7abe87bf8f",
)


def test_get_position_id():
    assert stake.position_id == 11984


def test_get_pool_id():
    assert stake.pool_id == 0


def test_calculate_adjustment_positive_exposure_too_little_leverage():
    adjustment = stake.calculate_adjustment(
        lp_quote=200, lp_base=10, borrow_quote=0, borrow_base=9, target_leverage=3
    )
    assert adjustment["borrow_quote"] == 100
    assert adjustment["borrow_base"] == 6
    assert adjustment["lp_quote"] == 100
    assert adjustment["lp_base"] == 5


def test_calculate_adjustment_negative_exposure_too_little_leverage():
    adjustment = stake.calculate_adjustment(
        lp_quote=200, lp_base=10, borrow_quote=0, borrow_base=11, target_leverage=3
    )
    assert adjustment["borrow_quote"] == 100
    assert adjustment["borrow_base"] == 4
    assert adjustment["lp_quote"] == 100
    assert adjustment["lp_base"] == 5


def test_calculate_adjustment_negative_exposure_too_much_leverage():
    adjustment = stake.calculate_adjustment(
        lp_quote=400, lp_base=20, borrow_quote=200, borrow_base=22, target_leverage=3
    )
    assert adjustment["borrow_quote"] == -100
    assert adjustment["borrow_base"] == -7
    assert adjustment["lp_quote"] == -100
    assert adjustment["lp_base"] == -5


def test_calculate_adjustment_positive_exposure_too_much_leverage():
    adjustment = stake.calculate_adjustment(
        lp_quote=400, lp_base=20, borrow_quote=200, borrow_base=18, target_leverage=3
    )
    assert adjustment["borrow_quote"] == -100
    assert adjustment["borrow_base"] == -3
    assert adjustment["lp_quote"] == -100
    assert adjustment["lp_base"] == -5


def test_calculate_adjustment_live():
    res = stake.get_principal()
    print(res)
    adjustment = stake.calculate_adjustment(
        lp_quote=res["token1"],
        lp_base=res["token0"],
        borrow_quote=res["token1_borrow"],
        borrow_base=res["token0_borrow"],
        target_leverage=3,
    )
    print(
        adjustment["borrow_quote"] / pow(10, 6),
        adjustment["borrow_base"] / pow(10, 18),
        adjustment["lp_quote"] / pow(10, 6),
        adjustment["lp_base"] / pow(10, 18),
    )


def test_calculate_imbalance():
    res = stake.get_principal()
    base_lp = res["token0"]
    base_borrow = res["token0_borrow"]
    print(f"Imbalance: {base_lp / base_borrow - 1}")


def test_calculate_leverage():
    res = stake.get_principal()
    quote = f"token1"
    base = f"token0"

    price = (res["reserve1"] / pow(10, 6)) / (res["reserve0"] / pow(10, 18))

    lp_value = res[quote] / pow(10, 6) + res[base] / pow(10, 18) * price
    borrow_value = (
        res[f"{quote}_borrow"] / pow(10, 6)
        + res[f"{base}_borrow"] / pow(10, 18) * price
    )
    print(f"Leverage: {lp_value / (lp_value - borrow_value)}")


# def test_adjust_position_leverage_3():
#     res = stake.get_principal()
#     adjustment = stake.calculate_adjustment(
#         lp_quote=res["token1"],
#         lp_base=res["token0"],
#         borrow_quote=res["token1_borrow"],
#         borrow_base=res["token0_borrow"],
#         target_leverage=3,
#     )

#     stake.adjust_position(
#         lpAAdjustment=int(adjustment["lp_base"]),
#         lpBAdjustment=int(adjustment["lp_quote"]),
#         borrowAAdjustment=int(adjustment["borrow_base"]),
#         borrowBAdjustment=int(adjustment["borrow_quote"]),
#     )


# def test_adjust_position_leverage_2():
#     res = stake.get_principal()
#     adjustment = stake.calculate_adjustment(
#         lp_quote=res["token1"],
#         lp_base=res["token0"],
#         borrow_quote=res["token1_borrow"],
#         borrow_base=res["token0_borrow"],
#         target_leverage=2,
#     )

#     stake.adjust_position(
#         lpAAdjustment=int(adjustment["lp_base"]),
#         lpBAdjustment=int(adjustment["lp_quote"]),
#         borrowAAdjustment=int(adjustment["borrow_base"]),
#         borrowBAdjustment=int(adjustment["borrow_quote"]),
#     )

# def test_unstake(caplog):
#     caplog.set_level(logging.DEBUG)
#     res = stake.get_principal()
#     print(res)
#     res = stake.unstake(res)
#     print(res)


# def test_stake(caplog):
#     # caplog.set_level(logging.INFO)
#     quote_balance = stake.trade.get_traded_balance(
#         stake.trade.user, stake.lp.token_info["token1"]
#     )
#     print(quote_balance)

#     stake.stake(token0_amount=0, token1_amount=quote_balance, leverage=2)
