import os
import json
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from google.cloud import secretmanager
import logging

ETHERSCAN = "https://api.etherscan.io/api"
POLYGONSCAN = "https://api.polygonscan.com/api"
from google.cloud import storage

client = storage.Client()
bucket = client.get_bucket("smart-contract-abis")


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


abi_dict = {}


def read_abi(address: str = "", filename="", network="mainnet", cloud=False) -> dict:
    if filename in abi_dict:
        return abi_dict[filename]
    # If cloud, read from google storage
    if int(os.getenv("CLOUD", 0)) == 1 or cloud:
        blob = bucket.get_blob(f"{filename}.json")
        # if found it, everything is ok
        if blob:
            abi = blob.download_as_bytes().decode("utf-8")
            return abi
        # else try to read from etherscan
        else:
            logging.info(f"{filename} not found on Cloud storage")
            abi = get_abi_etherscan(address, network=network)
    else:
        if filename:
            file_path = os.path.join(os.getcwd(), "abi", f"{filename}.json")
            if os.path.exists(file_path):
                with open(file_path) as f:
                    abi = json.load(f)

            else:
                logging.info(f"{filename} not found on local storage")
                abi = get_abi_etherscan(address, network=network)
                with open(file_path, "w") as f:
                    f.write(abi)

    abi_dict[filename] = abi
    return abi


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
    res = r.json()
    try:
        if int(res["status"]) != 1:
            logging.error(f"Failed getting ABI for address: {address} {res['result']}")
            raise ValueError(
                f"Failed getting ABI for address: {address}, {network} {res['result']}"
            )
        else:
            abi = r.json()["result"]
            return abi
    except Exception as e:
        raise ValueError(
            f"Failed getting ABI for address: {address}, {network} {res}, Error: {e}"
        )


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


def get_google_secret(key_name):
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": key_name})
    key = response.payload.data.decode("UTF-8")
    return key
