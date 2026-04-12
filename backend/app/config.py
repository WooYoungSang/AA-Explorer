from pathlib import Path

BASE_CHAIN = "base"
BASE_CHAIN_ID = 8453
ENTRYPOINT_V07 = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
BASE_RPC_WSS = "wss://base-mainnet.g.alchemy.com/v2/{API_KEY}"
BASE_RPC_HTTPS = "https://base-mainnet.g.alchemy.com/v2/{API_KEY}"
DB_PATH = Path("data") / "aa_explorer.db"
KNOWN_PAYMASTERS = {
    "0x2FAEB0760D4230Ef2aC21496Bb4F0b47D634FD4c": "Coinbase Paymaster",
    "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD": "Pimlico Paymaster",
}
KNOWN_FACTORIES = {
    "0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a": "Coinbase Smart Wallet Factory",
    "0x5de4839a76cf55d0c90e2061ef4386d962E15ae3": "Safe Factory",
}
