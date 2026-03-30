import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/blockchain_vote")
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "")
SEPOLIA_RPC = SEPOLIA_RPC_URL or "https://rpc.sepolia.org"  # å¤ç¨RPC
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY", "")
ADMIN_WALLET_ADDRESS = os.getenv("ADMIN_WALLET_ADDRESS", "")  # 管理员钱包地址
FACTORY_ADDRESS = os.getenv("FACTORY_ADDRESS", "")
IPFS_GATEWAY = os.getenv("IPFS_GATEWAY", "https://ipfs.io/ipfs/")
PINATA_API_KEY = os.getenv("PINATA_API_KEY", "")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY", "")
PINATA_TIMEOUT_SECONDS = int(os.getenv("PINATA_TIMEOUT_SECONDS", "120"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
