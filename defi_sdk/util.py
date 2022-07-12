import os
import json
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging

ETHERSCAN = "https://api.etherscan.io/api"
POLYGONSCAN = "https://api.polygonscan.com/api"


def get_web3(network="mainnet") -> Web3:
    if network == "mainnet":
        return Web3(
            Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.getenv('infura')}")
        )
    elif network == "polygon":
        w3 = Web3(
            Web3.HTTPProvider(
                f"https://polygon-mainnet.infura.io/v3/{os.getenv('infura')}"
            )
        )
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3
    elif network == "ropsten":
        return Web3(
            Web3.HTTPProvider(f"https://ropsten.infura.io/v3/{os.getenv('infura')}")
        )


def read_abi(address: str, filename: str = False, network="mainnet") -> dict:
    # try reading file if exists
    if filename:
        file_path = os.path.join(os.getcwd(), "abi", f"{filename}.json")
        if os.path.exists(file_path):
            with open(file_path) as f:
                abi = json.load(f)
                return abi
        else:
            abi = get_abi_etherscan(address, network=network)
            with open(file_path, "w") as f:
                f.write(abi)
            return abi
    else:
        return get_abi_etherscan(address)


def get_abi_etherscan(address, network="mainnet"):
    # lag to not exceed rate limit by accident
    time.sleep(0.3)

    # save as address if not found
    params = {
        "module": "contract",
        "action": "getabi",
        "address": address,
    }
    if network == "mainnet":
        params["apikey"] = os.environ.get("etherscan")
        r = requests.get(ETHERSCAN, params=params)
    elif network == "polygon":
        params["apikey"] = os.environ.get("polygonscan")
        r = requests.get(POLYGONSCAN, params=params)
    abi = r.json()["result"]
    if abi == "Invalid Address format":
        raise ValueError("Invalid address for getting ABI")
    return abi


def get_router(network, exchange):
    routers = {
        "polygon": {"quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"},
        "ropsten": {"uniswap": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"},
    }

    w3 = get_web3(network)
    router_abi = read_abi(os.getenv("UNI-ROUTER"), "router")
    return w3.eth.contract(routers[network][exchange], abi=router_abi)


def exec_concurrent(function):
    return function.call()


def get_token_price(address: str, chain: str):
    TOKEN_SERVICE_URL = "https://price-service-ec7oliozzq-ue.a.run.app/"
    # TOKEN_SERVICE_URL = "http://127.0.0.1:8080/"

    r = requests.post(
        TOKEN_SERVICE_URL + "get_token_address",
        data={"address": address, "chain": chain},
    )
    logging.debug(r)
    return r.json()
