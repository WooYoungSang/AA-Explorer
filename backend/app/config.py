from pathlib import Path

BASE_CHAIN = "base"
BASE_CHAIN_ID = 8453
ENTRYPOINT_V07 = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
BASE_RPC_WSS = "wss://base-mainnet.g.alchemy.com/v2/{API_KEY}"
BASE_RPC_HTTPS = "https://base-mainnet.g.alchemy.com/v2/{API_KEY}"
DB_PATH = Path("data") / "aa_explorer.db"
KNOWN_PAYMASTERS = {
    "0x2FAEB0760D4230Ef2aC21496Bb4F0b47D634FD4c": "Coinbase Paymaster",
    # Pimlico singleton paymaster, EntryPoint v0.7 (same address on every chain).
    "0x777777777777AeC03fd955926DbF81597e66834C": "Pimlico Paymaster",
}
KNOWN_FACTORIES = {
    "0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a": "Coinbase Smart Wallet Factory",
    # Safe SafeProxyFactory v1.4.1, canonical deployment (listed for chain 8453 Base).
    "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67": "Safe Factory",
}
# Source of each label above, checked 2026-11-12.
LABEL_SOURCES = {
    # CDP docs use this address as paymasterAddress in Coinbase paymaster examples.
    "0x2FAEB0760D4230Ef2aC21496Bb4F0b47D634FD4c": "https://docs.cdp.coinbase.com/",
    # v0.7 row of Pimlico's paymaster contract address table.
    "0x777777777777AeC03fd955926DbF81597e66834C": (
        "https://docs.pimlico.io/infra/paymaster/erc20-paymaster/contract-addresses"
    ),
    # Deployment table in the coinbase/smart-wallet README.
    "0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a": "https://github.com/coinbase/smart-wallet",
    # safe_proxy_factory.json v1.4.1: networkAddresses["8453"] is "canonical".
    "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67": (
        "https://github.com/safe-global/safe-deployments/blob/main/"
        "src/assets/v1.4.1/safe_proxy_factory.json"
    ),
}
