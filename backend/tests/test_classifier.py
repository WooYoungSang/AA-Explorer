from app.services.pipeline import classify_factory, classify_paymaster
from web3 import Web3


def test_classify_known_paymaster_is_case_insensitive() -> None:
    label = classify_paymaster("0x2faeb0760d4230ef2ac21496bb4f0b47d634fd4c")
    assert label == "Coinbase Paymaster"


def test_classify_unknown_paymaster_returns_other() -> None:
    label = classify_paymaster("0x" + "99" * 20)
    assert label == "Other"


def test_classify_known_factory_returns_expected_label() -> None:
    label = classify_factory(Web3.to_checksum_address("0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a"))
    assert label == "Coinbase Smart Wallet Factory"


def test_classify_missing_factory_returns_other() -> None:
    assert classify_factory(None) == "Other"
