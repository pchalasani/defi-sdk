import logging
import time

from web3 import Web3
from fireblocks_sdk.api_types import (
    TRANSACTION_STATUS_CONFIRMING,
    TRANSACTION_STATUS_CANCELLED,
)

from fireblocks_sdk import (
    FireblocksSDK,
    TransferPeerPath,
    DestinationTransferPeerPath,
    ONE_TIME_ADDRESS,
    VAULT_ACCOUNT,
    EXTERNAL_WALLET,
    TRANSACTION_STATUS_BLOCKED,
    TRANSACTION_STATUS_COMPLETED,
    TRANSACTION_STATUS_FAILED,
    TRANSACTION_STATUS_BROADCASTING,
)
from defi_sdk.fireblocks_integration.chain import Chain, CHAIN_TO_ASSET_ID

SUBMIT_TIMEOUT = 180
STATUS_KEY = "status"

FAILED_STATUS = [
    TRANSACTION_STATUS_FAILED,
    TRANSACTION_STATUS_BLOCKED,
    TRANSACTION_STATUS_CANCELLED,
]
PENDING_STATUS_TX_HASH = [
    TRANSACTION_STATUS_BROADCASTING,
    TRANSACTION_STATUS_CONFIRMING,
]


class Web3Bridge:
    def __init__(
        self,
        fb_api_client: FireblocksSDK,
        vault_account_id: str,
        chain: Chain,
    ):
        """
        :param fb_api_client: Fireblocks API client.
        :param vault_account_id: The source vault which address will sign messages.
        :param chain: Object of type Chain to represent what network to work with.
        :param external_wallet_address: The address of the interacted *contract*.
        :param wl_uuid: (Optional) If the contract is whitelisted, it can be sent through the co-responding UUID.
        """
        self.fb_api_client = fb_api_client
        self.source_vault_id = vault_account_id
        self.chain = chain
        self.asset: str = CHAIN_TO_ASSET_ID[self.chain][0]
        self.web_provider = Web3(Web3.HTTPProvider(CHAIN_TO_ASSET_ID[self.chain][1]))

    def check_whitelisting(self, target_address: str):
        whitelist_address = False
        destination = None
        whitelisted_addresses = self.fb_api_client.get_external_wallets()
        target = target_address.lower()
        for address in whitelisted_addresses:
            for token in address["assets"]:
                if token["address"].lower() == target:
                    logging.debug("found address on whitelist")
                    whitelist_address == True
                    if self.asset == token["id"]:
                        logging.debug(f"found correct asset for whitelisted address")
                        return TransferPeerPath(EXTERNAL_WALLET, address["id"])

        if not destination:
            if whitelist_address:
                raise ValueError(
                    f"Address is whitelisted but not correct asset, address: {target}, asset: {self.asset}"
                )
            else:
                raise ValueError(
                    f"Address not whitelisted, address: {target}, asset: {self.asset}"
                )

    def send_transaction(self, transaction: dict, note="", test=False) -> dict:
        """
        Takes a ready transaction after being built (using web3 buildTransaction()) and transmits it to Fireblocks.
        :param transaction: A transaction object (dict) to submit to the blockchain.
        :param note: (Optional) A note to submit with the transaction.
        :return:
        """
        if not test:
            destination = self.check_whitelisting(transaction["to"])
        else:
            destination = DestinationTransferPeerPath(
                ONE_TIME_ADDRESS, one_time_address={"address": transaction["to"]}
            )
        logging.debug(f"TX DESTINATION: {destination}")

        return self.fb_api_client.create_transaction(
            tx_type="CONTRACT_CALL",
            asset_id=self.asset,
            source=TransferPeerPath(VAULT_ACCOUNT, self.source_vault_id),
            amount=str(int(transaction["value"])),
            destination=destination,
            note=note,
            extra_parameters={"contractCallData": transaction["data"]},
        )

    def check_tx_is_sent(self, tx_id):
        try:
            current_status = self.fb_api_client.get_transaction_by_id(tx_id)
            if current_status[STATUS_KEY] in ():
                return current_status
            else:
                time.sleep(1)
        except:
            return {}

    def check_tx_status_chain(self, tx_hash: str):
        logging.info("Checking on-chain status")
        try:
            receipt = self.web_provider.eth.wait_for_transaction_receipt(
                tx_hash, timeout=3, poll_latency=1
            )
        except Exception as e:
            logging.info("Failed getting the receipt")
            return False

        if "status" in receipt:
            if receipt["status"] == 0:
                logging.error("Transaction failed on chain")
                return False
            else:
                time.sleep(3)
                logging.info("Found succesful transaction on chain")
                return True
        else:
            logging.error(
                f"Transaction did not have a status: HASH: {tx_hash}, receipt: {receipt}"
            )
            return False

    def get_fireblocks_transaction(self, fireblocks_id):
        for i in range(3):
            try:
                tx = self.fb_api_client.get_transaction_by_id(fireblocks_id)
                return tx
            except Exception as e:
                logging.info(f"Failed getting {fireblocks_id}, {e}")
                time.sleep(5)
        else:
            raise ValueError(f"Failed getting {fireblocks_id}, ERROR: {e}")

    def check_tx_is_completed(self, tx_id) -> dict:
        """
        Check status of a transaction either from chain or Fireblocks, whichever is first to confirm
        """
        timeout = 0
        transaction_hash = False
        previous_status = False

        while True:
            fireblocks_transaction = self.get_fireblocks_transaction(tx_id)
            current_status = fireblocks_transaction[STATUS_KEY]
            # Logging if status has changed
            if current_status != previous_status:
                previous_status = current_status
                logging.info(f"Current Fireblocks status: {current_status}")

            # Transaction seemed to have failed
            # TODO: This assumes transaction is not sent, could be true
            if current_status in FAILED_STATUS:
                logging.error(
                    f"Fireblocks reports transaction failed: {current_status} because {fireblocks_transaction['subStatus']}"
                )
                return False

            # Fireblocks confirms that tx is finished
            if current_status == TRANSACTION_STATUS_COMPLETED:
                logging.info(f"Fireblocks reports transaction completed")
                # TODO: Naively assuming transaction is finished, should check
                return True

            if "txHash" in fireblocks_transaction:
                transaction_hash = fireblocks_transaction["txHash"]
                chain_status = self.check_tx_status_chain(transaction_hash)
                # Transaction finished on chain, return True
                if chain_status:
                    return True
                else:
                    # Not finished on chain or errored while searching
                    # Try again and confirm, if no on-chain or fireblocks confirmation, timeout and cancel
                    pass

            # timeout while not yet confirmed or failed
            if timeout > SUBMIT_TIMEOUT:
                logging.info(f"Timeout reached")
                # Cancel tx, caller should resend
                logging.error("Timeout while waiting for confirmation")
                self.fb_api_client.cancel_transaction_by_id(tx_id)
                return False

            logging.debug(f"STATUS: {current_status}")
            time.sleep(5)
            timeout += 5
