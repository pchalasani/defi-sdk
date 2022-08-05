import logging
from functools import partial
from multiprocessing import Pool

from defi_sdk.util import get_web3
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data


def parse_events(topic_dict, log):
    topic = log["topics"][0].hex()
    parse = get_event_data(
        abi_codec=topic_dict[topic]["codec"],
        event_abi=topic_dict[topic]["abi"],
        log_entry=log,
    )
    return parse


def read_single_interval(filter, network, interval):
    from_block, to_block = interval
    filter["fromBlock"] = from_block
    filter["toBlock"] = to_block
    w3 = get_web3(network)
    try:
        for i in range(3):
            try:
                logs = w3.eth.get_logs(filter)
                break
            except ValueError as e:
                if e.args[0].get("code") == -32605:
                    logging.info("Splitting log...")
                    mid = int((from_block + to_block) / 2)
                    log_start = read_single_interval(filter, network, (from_block, mid))
                    log_end = read_single_interval(filter, network, (mid + 1, to_block))
                    logs = log_start + log_end
                    break
            except Exception as e:
                logging.error(f"Exception in reading single interval: {interval}")
                logging.error(e)
        else:
            logging.error(f"returned empty logs: {interval}")
            return []

    except Exception as e:
        logging.error(f"failed to read interval: {interval}")
        logging.error(e)
        return []
    logging.info(f"Finished interval with {len(logs)} logs")
    return logs


class EventReader:
    def __init__(self, network, threads=5) -> None:
        self.network = network
        self.w3 = get_web3(network)
        self.threads = int(threads)

    def create_interval_list(self, from_block, to_block, interval=10000):
        """
        Creates even intervals where last one is cut to match total blocks
        """
        # Infura polygon only accepts max 3500 range
        if self.network == "polygon":
            interval = 3499
        intervals = []
        current_block = from_block
        if to_block - current_block < interval:
            return [(current_block, to_block)]
        while current_block < to_block:
            intervals.append(
                (int(current_block), int(min(current_block + interval, to_block)))
            )
            current_block += interval + 1

        return intervals

    def get_events(
        self,
        event_abi_pairs: list,
        address_list: list,
        from_block,
        to_block,
        block_interval=10_000,
    ):
        """
        params:
        event_abi_pairs: list of tuples (event name, case sensitive, event abi)
        address_list: list of addresses to listen for events
        from_block: block number to start listening from
        to_block: block number to stop listening at
        block_interval: parameter on how many blocks at once, affects only speed
        """
        topic_dict = {}
        topic_list = []
        for i in event_abi_pairs:
            contract = self.w3.eth.contract(abi=i[1])
            event = contract.events[i[0]]
            event_abi = event._get_event_abi()
            event_abi_codec = event.web3.codec
            _, topics = construct_event_filter_params(event_abi, event_abi_codec)
            topic = topics["topics"][0]
            topic_list.append(topic)
            topic_dict[topic] = {"abi": event_abi, "codec": event_abi_codec}

        intervals = self.create_interval_list(from_block, to_block, block_interval)
        logging.info(f"{len(intervals)} intervals")

        filter_args = {
            "address": address_list,
            "topics": [topic_list],
        }

        with Pool(self.threads) as p:
            log_lists = p.map(
                partial(read_single_interval, filter_args, self.network),
                intervals,
            )

        all_logs = []
        for log_list in log_lists:
            if type(log_list) == list:
                all_logs += log_list

        logging.info(f"Found total: {len(all_logs)} logs")
        logging.info(f"parsing events...")
        with Pool(self.threads) as p:
            parsed_logs = p.map(
                partial(parse_events, topic_dict),
                all_logs,
            )

        return parsed_logs
