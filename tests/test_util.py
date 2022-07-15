from dotenv import load_dotenv
from defi_sdk.util import read_abi

load_dotenv(".env")


def test_read_abi_cloudl():
    abi = read_abi(filename="aave_addressprovider_v3", cloud=True)
    assert type(abi) == str
