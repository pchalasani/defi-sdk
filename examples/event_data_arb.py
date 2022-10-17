# Do this to get this working:
# export GOOGLE_PROJECT=market-data-338801
# export GOOGLE_APPLICATION_CREDENTIALS=market-data-338801-ed2d2a7baa93.json
# have a .env file containing these API keys:
#infura=ac33...880a779e0dfbb5a6
#etherscan=6Y9FUYB...1Q5YD5UZWQKIWH34
#polygonscan=MG3SGYUY....M1A3V6YDH6UA
#arbiscan=1IXFCI6TE4Q2K4U...9DUZQSGQB

import sys
import os
from dotenv import load_dotenv



print(os.getcwd())
from defi_sdk.event_reader import EventReader

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "market-data-338801-ed2d2a7baa93.json"
from defi_sdk.util import get_google_secret, read_abi

# load vars from .env file in root dir
load_dotenv()

# get infura key from google secret manager
# Google secret manager access needs to be configured, alternatively can use own infura key as env variable
# os.environ["infura"] = get_google_secret(
#     "projects/712543440434/secrets/infura_key_prod/versions/latest"
# )

# setup the eventreader object and point it to correct network
# increasing threads makes reading faster but can lead to rate limiting in larger queries like all blocks
reader = EventReader("arbitrum", threads=10)


def get_single_address_single_event():
    contract_address = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
    # read contract abi using etherscan, filename or cloud storage
    # setting just address uses etherscan
    # setting filename uses local file under abi folder (do not include .json)
    # setting filename and cloud=True uses cloud storage with filename
    contract_abi = read_abi(address=contract_address)

    # setup a list of tuples for events you want to listen for
    # tuple contains event name (case sensitive) and abi that contains the event
    event_abis = [("Mint", contract_abi)]

    current_block = reader.w3.eth.block_number

    """
    Pass event abis list, list of addresses that we want the events for, start block, end block and block interval
    Higher block interval leads to more results per block but some endpoints limit max results per query
    Block interval should be adjusted based on what chain is queried
        Chains with large blocks produced rarely (Ethereum) should have lower interval
        Chains with small blocks produced frequently (Polygon) should have higher interval
    Events that trigger often (like Sync) should have lower block interval (around 2k)
    Events that trigger rarely (like Burn, Mint) should have higher block interval (arounf 10k) 
    """
    event_list = reader.get_events(
        event_abis, [contract_address], current_block - 10000, current_block, 1000
    )
    return event_list


def get_single_address_multiple_events():

    # arbitrum uniswap contract address??
    contract_address = "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0"
    #contract_address = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
    contract_abi = read_abi(address=contract_address)

    # add new elements to event_abis list
    event_abis = [("Mint", contract_abi), ("Burn", contract_abi)]

    current_block = reader.w3.eth.block_number
    event_list = reader.get_events(
        event_abis, [contract_address], current_block - 10000, current_block, 1000
    )
    return event_list


def get_multiple_addresses_multiple_events():
    # NOTE: this requires each address to have the same events
    # NOTE2: might also work with different events but not tested :D
    # NOTE3: If both addresses produce same events, it is not possible (so far)
    # to request only event A from address 1 and event B from address 2
    uniswap_usdc_eth = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
    uniswap_dai_usdc = "0xAE461cA67B15dc8dc81CE7615e0320dA1A9aB8D5"
    contract_abi = read_abi(address=uniswap_usdc_eth)

    event_abis = [("Mint", contract_abi), ("Burn", contract_abi)]

    current_block = reader.w3.eth.block_number
    event_list = reader.get_events(
        event_abis,
        [uniswap_usdc_eth, uniswap_dai_usdc],
        current_block - 10000,
        current_block,
        1000,
    )
    return event_list

def save_lp_events(event_list, filename):
    with open(os.path.join(os.getcwd(), "data", f"{filename}.csv"), "+w") as f:
        for i in event_list:
            block = i["blockNumber"]
            tx_hash = i["transactionHash"].hex()
            tx_index = i["transactionIndex"]
            log_index = i["logIndex"]
            event = i["event"]
            if event in ["Mint", "Burn"]:
                val_0 = i["args"]["amount0"]
                val_1 = i["args"]["amount1"]
            elif event == "Sync":
                val_0 = i["args"]["reserve0"]
                val_1 = i["args"]["reserve1"]
            f.write(
                f"{event},{block},{tx_hash},{tx_index},{log_index},{val_0},{val_1}\n"
            )

def get_lp_historical_prices():
    """ "
    Example for getting prices
    Spot price is defined as reserve / reserve
    """
    reader = EventReader("arbitrum", threads=10)

    contract_address = "0x905dfCD5649217c42684f23958568e533C711Aa3"
    contract_abi = read_abi(address=contract_address, network="arbitrum")
    event_abis = [("Sync", contract_abi),
                  ("Mint", contract_abi),
                  ("Burn", contract_abi)]
    current_block = reader.w3.eth.block_number
    event_list = reader.get_events(
        event_abis,
        [contract_address],
        current_block - 10000,
        current_block,
        block_interval=1000,
        event_filter=[],
    )

    save_lp_events(event_list, "lp_events.csv")

    # for i in event_list:
    #     print(
    #         "Price: ",
    #         (i["args"]["reserve0"] / pow(10, 18))
    #         / (i["args"]["reserve1"] / pow(10, 6)),
    #     )

    def get_amount_out(amount_in, token_in, reserve0, reserve1):
        """
        Define how much to get out of a swap with given reserves and amount in
        """
        amount_in_with_fee = amount_in * 0.997
        if token_in == 0:
            numerator = amount_in_with_fee * reserve1
            denominator = reserve0 + amount_in
        else:
            numerator = amount_in_with_fee * reserve0
            denominator = reserve1 + amount_in
        amount_out = numerator / denominator
        return amount_out


if __name__ == "__main__":
    get_lp_historical_prices()
