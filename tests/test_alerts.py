import logging
from dotenv import load_dotenv
from defi_sdk.util import send_alert, resolve_alert, Severity, Urgency

load_dotenv(".env")


def test_simple_alert(caplog):
    caplog.set_level(logging.DEBUG)
    assert send_alert(
        title="Test Alert",
        message="This is a test alert.",
        dedup_key="test_dedup_key_test",
        severity=Severity("info"),
        urgency=Urgency("low"),
    )


def test_find_alert():
    resolve_alert("test_dedup_key_test")
