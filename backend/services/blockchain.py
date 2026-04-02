"""Blockchain interaction helpers."""
import json
import os

from web3 import Web3
from web3.middleware import geth_poa_middleware

from config import ADMIN_PRIVATE_KEY, FACTORY_ADDRESS, SEPOLIA_RPC_URL


def load_contract_abi():
    abi_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "artifacts",
        "contracts",
        "VotingSystem.sol",
        "VotingSystem.json",
    )
    abi_path = os.path.abspath(abi_path)
    with open(abi_path, "r", encoding="utf-8") as file:
        artifact = json.load(file)
    return artifact["abi"]


CONTRACT_ABI = load_contract_abi()
FACTORY_ABI = [
    {
        "inputs": [],
        "name": "getAllElections",
        "outputs": [
            {"internalType": "address[]", "name": "addrs", "type": "address[]"},
            {"internalType": "string[]", "name": "titles", "type": "string[]"},
            {"internalType": "address[]", "name": "creators", "type": "address[]"},
            {"internalType": "uint256[]", "name": "createdAts", "type": "uint256[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def get_web3():
    w3 = Web3(
        Web3.HTTPProvider(
            SEPOLIA_RPC_URL,
            request_kwargs={"timeout": 30},
        )
    )
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    try:
        w3.eth.block_number
    except Exception as exc:
        raise ConnectionError(f"无法连接到 Sepolia 网络: {exc}")

    return w3


def get_contract(w3: Web3, contract_address: str):
    return w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=CONTRACT_ABI,
    )


def get_factory_contract(w3: Web3):
    if not FACTORY_ADDRESS:
        return None
    return w3.eth.contract(
        address=Web3.to_checksum_address(FACTORY_ADDRESS),
        abi=FACTORY_ABI,
    )


def fetch_factory_elections():
    if not FACTORY_ADDRESS:
        return []

    w3 = get_web3()
    factory = get_factory_contract(w3)
    if factory is None:
        return []

    addrs, titles, creators, created_ats = factory.functions.getAllElections().call()
    items = []
    for index in range(len(addrs)):
        address = addrs[index].lower()
        start_time = 0
        end_time = 0

        try:
            election_contract = get_contract(w3, address)
            start_time = int(election_contract.functions.votingStartTime().call())
            end_time = int(election_contract.functions.votingEndTime().call())
        except Exception:
            # Keep the catalog usable even if some legacy contracts cannot provide timing info.
            start_time = 0
            end_time = 0

        items.append(
            {
                "address": address,
                "title": (titles[index] or "").strip(),
                "creator": creators[index],
                "created_at": int(created_ats[index]),
                "start_time": start_time,
                "end_time": end_time,
            }
        )

    return items


async def authorize_voter_on_chain(wallet_address: str, contract_address: str) -> str:
    """
    Add the anonymous wallet address to the on-chain whitelist of the given election contract.
    """
    w3 = get_web3()
    contract = get_contract(w3, contract_address)
    admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
    checksum_addr = Web3.to_checksum_address(wallet_address)

    tx = contract.functions.authorizeVoter(checksum_addr).build_transaction(
        {
            "from": admin_account.address,
            "nonce": w3.eth.get_transaction_count(admin_account.address, "pending"),
            "gas": 150000,
            "gasPrice": int(w3.eth.gas_price * 1.2),
        }
    )

    signed = admin_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("链上授权交易失败")

    return tx_hash.hex()
