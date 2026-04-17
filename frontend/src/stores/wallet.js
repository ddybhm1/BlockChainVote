import { defineStore } from "pinia";
import { ref } from "vue";
import { ethers } from "ethers";
import { FACTORY_ABI, FACTORY_ADDRESS } from "../services/contract.js";
import { checkBlacklistWallet, setAuthToken, setStoredStudentId } from "../services/api.js";

export const useWalletStore = defineStore("wallet", () => {
    function clearStudentSessionForWalletChange() {
      setAuthToken("");
      setStoredStudentId("");
      window.localStorage.removeItem("userToken");
      window.localStorage.removeItem("walletAddress");
    }

  const address = ref("");
  const loading = ref(false);
  const chainId = ref(null);
  const isFactoryOwner = ref(false); // 是否是工厂合约的 owner

  /**
   * 检查当前钱包是否是工厂合约的 owner
   */
  async function checkFactoryOwner() {
    if (!address.value || !FACTORY_ADDRESS) {
      isFactoryOwner.value = false;
      return;
    }
    try {
      const provider = new ethers.JsonRpcProvider(
        import.meta.env.VITE_SEPOLIA_RPC || "https://rpc.sepolia.org"
      );
      const factory = new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, provider);
      const ownerAddr = await factory.owner();
      isFactoryOwner.value = ownerAddr.toLowerCase() === address.value.toLowerCase();
    } catch (err) {
      console.error("检查工厂合约 owner 失败:", err);
      isFactoryOwner.value = false;
    }
  }

  /**
   * 连接 MetaMask 钱包
   */
  async function connect() {
    if (!window.ethereum) {
      alert("请安装 MetaMask 钱包扩展");
      return;
    }

    loading.value = true;
    try {
      const provider = new ethers.BrowserProvider(window.ethereum);
      const accounts = await provider.send("eth_requestAccounts", []);
      if (accounts.length > 0) {
        const previousAddress = address.value;
        const nextAddress = ethers.getAddress(accounts[0]);
        const blacklist = await checkBlacklistWallet(nextAddress);
        if (blacklist?.blacklisted) {
          alert(blacklist.reason || "该钱包地址已被平台封禁");
          disconnect();
          return;
        }

        if (previousAddress && previousAddress.toLowerCase() !== nextAddress.toLowerCase()) {
          clearStudentSessionForWalletChange();
          alert("检测到钱包地址切换，已退出当前登录状态。");
          address.value = nextAddress;
          await checkFactoryOwner();
          window.location.reload();
          return;
        }

        address.value = nextAddress;
      }

      const network = await provider.getNetwork();
      chainId.value = Number(network.chainId);

      // Sepolia chainId = 11155111
      if (chainId.value !== 11155111) {
        alert("请将 MetaMask 切换到 Sepolia 测试网络");
      }

      // 连接成功后检查是否是工厂合约 owner
      await checkFactoryOwner();
    } catch (err) {
      console.error("连接钱包失败:", err);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 断开钱包
   */
  function disconnect() {
    address.value = "";
    chainId.value = null;
    isFactoryOwner.value = false;
  }

  /**
   * 获取 Ethers Provider
   */
  function getProvider() {
    if (!window.ethereum) return null;
    return new ethers.BrowserProvider(window.ethereum);
  }

  /**
   * 获取 Signer（用于签名交易）
   */
  async function getSigner() {
    const provider = getProvider();
    if (!provider) return null;
    return await provider.getSigner();
  }

  // 监听 MetaMask 账户切换
  if (window.ethereum) {
    window.ethereum.on("accountsChanged", async (accounts) => {
      if (accounts.length > 0) {
        const previousAddress = address.value;
        const nextAddress = ethers.getAddress(accounts[0]);
        try {
          const blacklist = await checkBlacklistWallet(nextAddress);
          if (blacklist?.blacklisted) {
            alert(blacklist.reason || "该钱包地址已被平台封禁");
            disconnect();
            return;
          }
        } catch (err) {
          console.warn("黑名单检查失败，保留当前连接", err);
        }

        if (previousAddress && previousAddress.toLowerCase() !== nextAddress.toLowerCase()) {
          clearStudentSessionForWalletChange();
          alert("检测到钱包地址切换，已退出当前登录状态。");
          address.value = nextAddress;
          await checkFactoryOwner();
          window.location.reload();
          return;
        }

        address.value = nextAddress;
        // 账户切换时重新检查 owner 权限
        await checkFactoryOwner();
      } else {
        disconnect();
      }
    });

    window.ethereum.on("chainChanged", () => {
      window.location.reload();
    });
  }

  return { address, loading, chainId, isFactoryOwner, connect, disconnect, getProvider, getSigner, checkFactoryOwner };
});
