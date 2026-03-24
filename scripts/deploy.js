const hre = require("hardhat");

async function main() {
  console.log("正在部署 ElectionFactory...");

  const [deployer] = await hre.ethers.getSigners();
  console.log(`部署账户: ${deployer.address}`);

  const ElectionFactory = await hre.ethers.getContractFactory("ElectionFactory");
  const factory = await ElectionFactory.deploy();
  await factory.waitForDeployment();

  const address = await factory.getAddress();
  console.log(`ElectionFactory 已部署到: ${address}`);
  console.log(`工厂拥有者 (Owner) 地址: ${deployer.address}`);
  console.log("\n[提示] 请将上述工厂合约地址更新至 backend/.env 的 FACTORY_ADDRESS 和 frontend/.env 的 VITE_FACTORY_ADDRESS 中。");
  console.log("[提示] 单个投票项目的合约地址将在创建投票项目时由工厂合约自动分配。");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});