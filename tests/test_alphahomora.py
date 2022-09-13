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


def test_calculate_adjustment_decrease_leverage(caplog):
    caplog.set_level(logging.DEBUG)
    adjustment = stake.calculate_adjustment(
        lp_quote=500,
        lp_base=10,
        borrow_quote=250,
        borrow_base=10,
        target_leverage=2,
    )
    print("Adjustment", adjustment)
    assert adjustment["borrow_quote"] == -250
    assert adjustment["borrow_base"] == -5
    assert adjustment["lp_quote"] == -250
    assert adjustment["lp_base"] == -5


def test_calculate_adjustment_increase_leverage():
    adjustment = stake.calculate_adjustment(
        lp_quote=500,
        lp_base=10,
        borrow_quote=0,
        borrow_base=5,
        target_leverage=3,
    )
    print("Adjustment", adjustment)
    assert adjustment["borrow_quote"] == 375
    assert adjustment["borrow_base"] == 17.5
    assert adjustment["lp_quote"] == 625
    assert adjustment["lp_base"] == 12.5


def test_calculate_adjustment_live():
    res = stake.get_principal()
    print(res)
    adjustment = stake.calculate_adjustment(
        lp_quote=res["token1"],
        lp_base=res["token0"],
        borrow_quote=res["token1_borrow"],
        borrow_base=res["token0_borrow"],
        target_leverage=2.7,
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


def test_get_rewards(caplog):
    # caplog.set_level(logging.DEBUG)
    print(stake.get_rewards())


def test_get_pool_info():
    print(stake.get_pool_info_api(0))


def test_get_accumulated_reward():
    print(stake.get_accumulated_rewards(18))


def test_get_harvested_rewards():
    print(stake.get_harvested_rewards())


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


# def test_adjust_position_leverage_2_7(caplog):
#     caplog.set_level(logging.INFO)
#     res = stake.get_principal()
#     adjustment = stake.calculate_adjustment(
#         lp_quote=res["token1"],
#         lp_base=res["token0"],
#         borrow_quote=res["token1_borrow"],
#         borrow_base=res["token0_borrow"],
#         target_leverage=2.7,
#     )
#     print(adjustment)

#     lp_base = round(res["token0"] / pow(10, 18), 3)
#     lp_quote = round(res["token1"] / pow(10, 6), 3)

#     borrow_base = round(res["token0_borrow"] / pow(10, 18), 3)
#     borrow_quote = round(res["token1_borrow"] / pow(10, 6), 3)

#     print(f"LP, Base: {lp_base} Quote: {lp_quote}")
#     print(f"Borrow, Base: {borrow_base} Quote: {borrow_quote}")

#     lp_base_adjustment = round(adjustment["lp_base"] / pow(10, 18), 3)
#     lp_quote_adjustment = round(adjustment["lp_quote"] / pow(10, 6), 3)
#     borrow_base_adjustment = round(adjustment["borrow_base"] / pow(10, 18), 3)
#     borrow_quote_adjustment = round(adjustment["borrow_quote"] / pow(10, 6), 3)

#     print(f"LP Adjustment, Base: {lp_base_adjustment} Quote: {lp_quote_adjustment}")
#     print(
#         f"Borrow Adjustment, Base: {borrow_base_adjustment} Quote: {borrow_quote_adjustment}"
#     )

#     adjustment = stake.calculate_adjustment_v2(
#         lp_quote=res["token1"],
#         lp_base=res["token0"],
#         borrow_quote=res["token1_borrow"],
#         borrow_base=res["token0_borrow"],
#         target_leverage=2.7,
#     )

#     lp_base_adjustment = round(adjustment["lp_base"] / pow(10, 18), 3)
#     lp_quote_adjustment = round(adjustment["lp_quote"] / pow(10, 6), 3)
#     borrow_base_adjustment = round(adjustment["borrow_base"] / pow(10, 18), 3)
#     borrow_quote_adjustment = round(adjustment["borrow_quote"] / pow(10, 6), 3)

#     stake.adjust_position(
#         lpAAdjustment=int(adjustment["lp_base"]),
#         lpBAdjustment=int(adjustment["lp_quote"]),
#         borrowAAdjustment=int(adjustment["borrow_base"] * 0.99),
#         borrowBAdjustment=int(adjustment["borrow_quote"] * 0.99),
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
