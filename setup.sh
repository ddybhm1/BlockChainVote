#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install 20
nvm use 20

echo "=== Node 版本 ==="
node --version
echo "=== npm 路径 ==="
which npm

echo "=== 清理旧依赖 ==="
cd ~/BlockChainVote
rm -rf node_modules package-lock.json

echo "=== 安装依赖 ==="
npm install

echo "=== 完成 ==="
