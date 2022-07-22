import os
import logging
import time
from fireblocks_defi_sdk_py.web3_bridge import Web3Bridge
from fireblocks_defi_sdk_py.chain import Chain
from fireblocks_sdk import FireblocksSDK
from google.cloud import secretmanager

from defi_sdk.util import get_web3, read_abi


class DeFiTrade:
    def __init__(
        self,
        network: str,
        user: str,
        test: bool = False,
        send_tx: bool = False,
    ):
        self.network = network
        self.w3 = get_web3(network)
        self.user = user

        self.test = test
        self.send_tx = send_tx
        self.fb = self.setup_fireblocks()
        self.fb_bridge = self.get_fb_bridge()

    def setup_fireblocks(self):
        client = secretmanager.SecretManagerServiceClient()

        if self.test:
            secret_key_id = "projects/712543440434/secrets/fireblocks_secret_key_test/versions/latest"
            secret_api_id = (
                "projects/712543440434/secrets/fireblocks_api_key_test/versions/latest"
            )
        else:
            secret_key_id = (
                "projects/712543440434/secrets/fireblocks_secret_key/versions/latest"
            )
            secret_api_id = (
                "projects/712543440434/secrets/fireblocks_api_key/versions/latest"
            )

        response = client.access_secret_version(request={"name": secret_key_id})
        fireblocks_secret_key = response.payload.data.decode("UTF-8")

        response = client.access_secret_version(request={"name": secret_api_id})
        fireblocks_api_key = response.payload.data.decode("UTF-8")
        return FireblocksSDK(fireblocks_secret_key, fireblocks_api_key)

    def get_fb_bridge(self):
        network = self.network
        if network == "polygon":
            chain = Chain.POLYGON
            vault_account_id = "4"
        elif network == "ropsten":
            chain = Chain.ROPSTEN
            vault_account_id = "1"
        fb_bridge = Web3Bridge(
            fb_api_client=self.fb,
            vault_account_id=vault_account_id,  # os.environ.get("FIREBLOCKS_SOURCE_VAULT_ACCOUNT"),
            chain=chain,
        )
        return fb_bridge

    def _build_transaction(self, tx):
        for attempt in range(4):
            try:
                tx_raw = tx.build_transaction({"from": self.user})
                return tx_raw
            except Exception as e:
                logging.error(f"Failed building tx: {e}")
                time.sleep(2)
        else:
            logging.error(f"Retries exceeded while building TX")
            raise e

    def _send_transaction(self, tx):
        for i in range(4):
            try:
                tx_result = self.fb_bridge.send_transaction(tx, test=self.test)
                return tx_result
            except:
                logging.error("Failed sending transaction to fireblocks")
                time.sleep(2)
        else:
            raise ValueError(f"Failed sending transaction: {tx}")

    def _check_transaction_retry(self, tx_id):
        for attempt in range(2):
            if self.fb_bridge.check_tx_is_completed(tx_id):
                return True
            else:
                logging.error(f"Fireblocks reports transaction failed: {tx_id}")
        else:
            logging.error(
                f"Retries exceeded while trying to send fireblocks transaction"
            )

    def send_transaction_fireblocks(self, tx):
        logging.debug(f"simulating transaction")
        sim_res = tx.call({"from": self.user})
        logging.debug(f"result: {sim_res}")
        logging.debug("sending transaction")
        if self.send_tx:
            tx_raw = self._build_transaction(tx)
            tx_result = self._send_transaction(tx_raw)
            self._check_transaction_retry(tx_result["id"])
        else:
            return sim_res

    def ensure_approval(self, user, token, target, amount):
        contract = self.w3.eth.contract(
            token, abi=(read_abi(os.getenv("ERC20"), "token"))
        )
        allowance = contract.functions.allowance(user, target).call()
        logging.info(f"Current allowance: {allowance}, required allowance: {amount}")
        if allowance > amount:
            logging.info("Allowance OK")
            return True
        else:
            logging.info(f"Not enough allowance")
            if self.send_tx:
                approval_tx = contract.functions.approve(
                    target, int(amount) * pow(10, 5)
                )
                logging.info(f"Sending approval transaction")
                self.send_transaction_fireblocks(approval_tx)
            else:
                logging.error(f"Wallet: {user}")
                logging.error(f"token: {token}")
                logging.error(f"target: {target}")
                raise ValueError(
                    f"Not Enough allowance for {user} to spend {token} at {target}"
                )

    def get_current_balance(self, user, token):
        contract = self.w3.eth.contract(
            token, abi=read_abi(os.getenv("ERC20"), "token")
        )

        return contract.functions.balanceOf(user).call()
