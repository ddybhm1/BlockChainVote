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

  // 为了自动认证 Factory 部署的子合约，我们在主脚本里先单独部署一个 VotingSystem 用来向 Etherscan 上传源码
  console.log("\n正在部署占位子合约 (仅用于 Etherscan 源码自动验证匹配)...");
  const VotingSystem = await hre.ethers.getContractFactory("VotingSystem");
  const dummySystem = await VotingSystem.deploy(deployer.address, "Dummy");
  await dummySystem.waitForDeployment();
  const dummyAddress = await dummySystem.getAddress();
  console.log(`占位 VotingSystem 已部署到: ${dummyAddress}`);

  console.log("\n等待 6 个区块确认以进行 Etherscan 验证...");
  await dummySystem.deploymentTransaction().wait(6);

  console.log("正在验证 Factory...");
  try {
    await hre.run("verify:verify", {
      address: address,
      constructorArguments: [],
    });
  } catch (error) {
    console.error("Factory 验证失败 (可能已被验证):", error.message);
  }

  console.log("正在验证占位子合约...");
  try {
    await hre.run("verify:verify", {
      address: dummyAddress,
      constructorArguments: [deployer.address, "Dummy"],
    });
    console.log("占位子合约验证成功！在此之后工厂合约生成的任何子合约都可以被 Etherscan 自动识别出源码了。");
  } catch (error) {
    console.error("占位子合约验证失败 (可能已被验证):", error.message);
  }

  console.log("\n[提示] 请将上述工厂合约地址更新至 backend/.env 的 FACTORY_ADDRESS 和 frontend/.env 的 VITE_FACTORY_ADDRESS 中。");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});