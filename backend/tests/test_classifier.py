from app.config import KNOWN_FACTORIES, KNOWN_PAYMASTERS
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


def test_classify_pimlico_paymaster_verified_address() -> None:
    address = "0x777777777777AeC03fd955926DbF81597e66834C"
    assert classify_paymaster(address) == "Pimlico Paymaster"
    assert classify_paymaster(address.lower()) == "Pimlico Paymaster"


def test_classify_safe_factory_verified_address() -> None:
    address = "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67"
    assert classify_factory(address) == "Safe Factory"


def test_removed_unverified_addresses_are_other() -> None:
    assert classify_paymaster("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD") == "Other"
    assert classify_factory("0x5de4839a76cf55d0c90e2061ef4386d962E15ae3") == "Other"


def test_known_entries_record_source() -> None:
    from app import config

    for table in (KNOWN_PAYMASTERS, KNOWN_FACTORIES):
        for address in table:
            assert config.LABEL_SOURCES[address].startswith("http")
