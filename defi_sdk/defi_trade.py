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
        vault_account_id: int = 0,
    ):
        if vault_account_id != 0:
            self.vault_account_id = str(vault_account_id)
        else:
            if test:
                self.vault_account_id = "1"
            else:
                self.vault_account_id = "4"
        self.network = network
        self.w3 = get_web3(network)
        self.user = user

        self.test = test
        self.send_tx = send_tx
        self.fb = self.setup_fireblocks()
        self.fb_bridge = self.get_fb_bridge()

    def setup_fireblocks(self):
        logging.debug("Getting fireblocks API key")
        client = secretmanager.SecretManagerServiceClient()
        logging.info("Got client")
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
        logging.debug("Got fireblocks API key")
        sdk = FireblocksSDK(fireblocks_secret_key, fireblocks_api_key)
        logging.debug("Got fireblocks API client")
        return sdk

    def get_fb_bridge(self):
        logging.debug("Getting fireblocks bridge")
        network = self.network
        if network == "polygon":
            chain = Chain.POLYGON
        elif network == "ropsten":
            chain = Chain.ROPSTEN
        elif network == "mainnet":
            chain = Chain.MAINNET
        else:
            raise ValueError(f"Unknown network: {network}")
        logging.debug("Creating fireblocks bridge")
        fb_bridge = Web3Bridge(
            fb_api_client=self.fb,
            vault_account_id=self.vault_account_id,
            chain=chain,
        )
        logging.debug("Got fireblocks bridge")
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

    def _send_transaction(self, tx, approval_tx=False):
        for i in range(4):
            try:
                tx_result = self.fb_bridge.send_transaction(
                    tx, test=self.test, approval_tx=approval_tx
                )
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
                time.sleep(2)
        else:
            logging.error(
                f"Retries exceeded while trying to send fireblocks transaction"
            )

    def send_transaction_fireblocks(self, tx, approval_tx=False):
        logging.debug(f"simulating transaction")
        sim_res = tx.call({"from": self.user})
        logging.debug(f"result: {sim_res}")
        logging.debug("sending transaction")
        if self.send_tx:
            tx_raw = self._build_transaction(tx)
            tx_result = self._send_transaction(tx_raw, approval_tx=approval_tx)
            self._check_transaction_retry(tx_result["id"])
        else:
            return sim_res

    def ensure_approval(self, user, token, spender, amount):
        contract = self.w3.eth.contract(
            token, abi=(read_abi(os.getenv("ERC20"), "token"))
        )
        allowance = contract.functions.allowance(user, spender).call()
        logging.info(f"Current allowance: {allowance}, required allowance: {amount}")
        if allowance > amount:
            logging.info("Allowance OK")
            return True
        else:
            logging.info(f"Not enough allowance")
            if self.send_tx:
                approval_tx = contract.functions.approve(
                    spender, int(amount) * pow(10, 5)
                )
                logging.info(f"Sending approval transaction")
                self.send_transaction_fireblocks(approval_tx, approval_tx=spender)
            else:
                logging.error(
                    f"Wallet: {user}, token: {token}, spender: {spender}, amount: {amount}"
                )
                raise ValueError(
                    f"Not Enough allowance for {user} to spend {token} at {spender}"
                )

    def get_current_balance(self, user, token):
        contract = self.w3.eth.contract(
            token, abi=read_abi(os.getenv("ERC20"), "token")
        )

        return contract.functions.balanceOf(user).call()

    def get_traded_balance(self, user, token):
        for attempt in range(4):
            balance = self.get_current_balance(user, token)
            if balance > 0:
                return balance
            else:
                time.sleep(2)
        else:
            logging.error(f"Found 0 balance for {token}")
            return 0
