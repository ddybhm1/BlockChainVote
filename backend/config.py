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
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "blockchain-vote-dev-secret")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "12"))

# DB pool tuning
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

# API payload compression
GZIP_MINIMUM_SIZE = int(os.getenv("GZIP_MINIMUM_SIZE", "1024"))

# Auth catalog cache / timeout tuning
FACTORY_CATALOG_TTL_SECONDS = int(os.getenv("FACTORY_CATALOG_TTL_SECONDS", "30"))
FACTORY_CATALOG_TIMEOUT_SECONDS = float(os.getenv("FACTORY_CATALOG_TIMEOUT_SECONDS", "8"))

# Background indexer
INDEXER_SYNC_INTERVAL_SECONDS = int(os.getenv("INDEXER_SYNC_INTERVAL_SECONDS", "20"))
INDEXER_FETCH_TIMEOUT_SECONDS = float(os.getenv("INDEXER_FETCH_TIMEOUT_SECONDS", "12"))

# Realtime snapshot cache
REALTIME_SNAPSHOT_CACHE_SECONDS = int(os.getenv("REALTIME_SNAPSHOT_CACHE_SECONDS", "5"))
