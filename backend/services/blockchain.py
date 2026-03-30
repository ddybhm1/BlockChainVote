"""区块链交互服务 - 使用管理员私钥授权匿名选民地址"""
import json
import os
from web3 import Web3
from config import SEPOLIA_RPC_URL, ADMIN_PRIVATE_KEY


# 自动从 artifacts 目录加载 VotingSystem ABI
def load_contract_abi():
    abi_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..", "artifacts", "contracts", "VotingSystem.sol", "VotingSystem.json"
    )
    abi_path = os.path.abspath(abi_path)
    with open(abi_path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
    return artifact["abi"]

CONTRACT_ABI = load_contract_abi()


def get_web3():
    w3 = Web3(Web3.HTTPProvider(
        SEPOLIA_RPC_URL,
        request_kwargs={"timeout": 30}
    ))
    # 用实际 RPC 调用验证连接
    try:
        w3.eth.block_number
    except Exception as e:
        raise ConnectionError(f"无法连接到 Sepolia 网络: {e}")
    return w3


def get_contract(w3: Web3, contract_address: str):
    return w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=CONTRACT_ABI,
    )


async def authorize_voter_on_chain(wallet_address: str, contract_address: str) -> str:
    """
    将匿名钱包地址加入指定投票项目合约的链上白名单。
    返回交易哈希。执行完毕后调用方应立即丢弃 wallet_address。
    """
    w3 = get_web3()
    contract = get_contract(w3, contract_address)
    admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
    checksum_addr = Web3.to_checksum_address(wallet_address)

    # 构建交易
    tx = contract.functions.authorizeVoter(checksum_addr).build_transaction(
        {
            "from": admin_account.address,
            "nonce": w3.eth.get_transaction_count(admin_account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    # 签名并发送
    signed = admin_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    # 等待确认
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("链上授权交易失败")

    return tx_hash.hex()
