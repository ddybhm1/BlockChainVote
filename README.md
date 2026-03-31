# BlockChainVote

一个基于 `FastAPI + Vue + Solidity` 的区块链投票系统，当前已经包含：

- 多选举工厂合约
- 链上实时投票大屏
- 投票成功后自动铸造的 SBT 纪念徽章

## 开发环境

- Ubuntu 20.04 / WSL2
- Node.js 22.x
- Python 3.12

## 首次准备

### 前端依赖

```bash
cd ~/BlockChainVote/frontend
npm install
```

### 后端虚拟环境

```bash
cd ~/BlockChainVote/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

### 环境变量

按需补齐这些文件：

- 根目录 `.env`
- `frontend/.env`
- `backend/.env`

常见变量包括：

- `SEPOLIA_RPC_URL`
- `DEPLOYER_PRIVATE_KEY`
- `FACTORY_ADDRESS`
- `VITE_FACTORY_ADDRESS`
- `VITE_SEPOLIA_RPC`
- `FRONTEND_ORIGIN`

## 手动启动

### 启动后端

```bash
cd ~/BlockChainVote/backend
source .venv/bin/activate
uvicorn main:app --reload
```

默认地址：

- `http://127.0.0.1:8000`

### 启动前端

```bash
cd ~/BlockChainVote/frontend
npm run dev -- --host --strictPort
```

默认地址：

- `http://localhost:5173`

## 常用命令

### 合约编译

```bash
cd ~/BlockChainVote
npx hardhat compile
```

### 合约测试

```bash
cd ~/BlockChainVote
npx hardhat test
```

### 前端构建

```bash
cd ~/BlockChainVote/frontend
npm run build
```

## 常见问题

### `vite: Permission denied`

通常是 WSL 里误用了 Windows 版 Node。确认：

```bash
which node
node -p "process.platform"
```

应优先看到 Linux 版 Node，例如：

- `/home/mike/.nvm/.../bin/node`
- `linux`

### `5173` 被占用

```bash
fuser -k 5173/tcp
cd ~/BlockChainVote/frontend
npm run dev -- --host --strictPort
```

### 后端依赖缺失

```bash
cd ~/BlockChainVote/backend
source .venv/bin/activate
pip install -r requirements.txt
```
