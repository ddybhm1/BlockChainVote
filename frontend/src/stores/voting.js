import { defineStore } from "pinia";
import { ref } from "vue";
import { ethers } from "ethers";
import { useWalletStore } from "./wallet.js";
import { ELECTION_ABI, FACTORY_ABI, FACTORY_ADDRESS, IPFS_GATEWAY } from "../services/contract.js";

export const useVotingStore = defineStore("voting", () => {
  const candidates = ref([]);
  const votingStarted = ref(false);
  const votingEnded = ref(false);
  const totalVoters = ref(0);
  const totalVotes = ref(0);
  const isAuthorized = ref(false);
  const hasVoted = ref(false);
  const loading = ref(false);
  const error = ref("");

  // 多项目相关
  const currentElection = ref(""); // 当前选中的投票项目合约地址
  const elections = ref([]);       // 所有投票项目列表
  const startTime = ref(0);        // 当前投票项目的开始时间（秒）
  const endTime = ref(0);          // 当前投票项目的截止时间（秒）

  function getProvider() {
    return new ethers.JsonRpcProvider(
      import.meta.env.VITE_SEPOLIA_RPC || "https://rpc.sepolia.org"
    );
  }

  /**
   * 获取工厂合约只读实例
   */
  function getFactoryReadContract() {
    return new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, getProvider());
  }

  /**
   * 获取工厂合约可写实例
   */
  async function getFactoryWriteContract() {
    const wallet = useWalletStore();
    const signer = await wallet.getSigner();
    if (!signer) throw new Error("请先连接 MetaMask 钱包");
    return new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, signer);
  }

  /**
   * 获取指定投票合约的只读实例
   */
  function getElectionReadContract(addr) {
    const address = addr || currentElection.value;
    if (!address) throw new Error("未选择投票项目");
    return new ethers.Contract(address, ELECTION_ABI, getProvider());
  }

  /**
   * 获取指定投票合约的可写实例
   */
  async function getElectionWriteContract(addr) {
    const address = addr || currentElection.value;
    if (!address) throw new Error("未选择投票项目");
    const wallet = useWalletStore();
    const signer = await wallet.getSigner();
    if (!signer) throw new Error("请先连接 MetaMask 钱包");
    return new ethers.Contract(address, ELECTION_ABI, signer);
  }

  /**
   * 从工厂合约加载所有投票项目
   */
  async function loadElections() {
    if (!FACTORY_ADDRESS) {
      error.value = "工厂合约地址未配置";
      return;
    }
    try {
      const factory = getFactoryReadContract();
      const result = await factory.getAllElections();
      const [addrs, titles, creators, createdAts] = result;
      const list = [];
      for (let i = 0; i < addrs.length; i++) {
        list.push({
          address: addrs[i],
          title: titles[i],
          creator: creators[i],
          createdAt: Number(createdAts[i]),
        });
      }
      elections.value = list;
    } catch (err) {
      console.error("加载投票项目列表失败:", err);
      error.value = "加载项目列表失败: " + (err.message || err);
    }
  }

  /**
   * 选择投票项目
   */
  async function selectElection(addr) {
    currentElection.value = addr;
    // 重置当前状态
    candidates.value = [];
    votingStarted.value = false;
    votingEnded.value = false;
    totalVoters.value = 0;
    totalVotes.value = 0;
    isAuthorized.value = false;
    hasVoted.value = false;
    startTime.value = 0;
    endTime.value = 0;
    if (addr) {
      try {
        const contract = getElectionReadContract(addr);
        startTime.value = Number(await contract.votingStartTime());
        endTime.value = Number(await contract.votingEndTime());
      } catch (e) {
        // 忽略错误
      }
    }
  }

  /**
   * 从链上加载当前投票项目的所有候选人及投票状态
   */
  async function loadCandidates() {
    if (!currentElection.value) {
      error.value = "请先选择投票项目";
      return;
    }

    // 每次加载候选人时也同步刷新投票时间
    try {
      const contract = getElectionReadContract();
      startTime.value = Number(await contract.votingStartTime());
      endTime.value = Number(await contract.votingEndTime());
    } catch (e) {}

    loading.value = true;
    error.value = "";

    try {
      const contract = getElectionReadContract();

      const [status, allCandidates] = await Promise.all([
        contract.getVotingStatus(),
        contract.getAllCandidates(),
      ]);

      votingStarted.value = status[0];
      votingEnded.value = status[1];
      totalVoters.value = Number(status[3]);
      totalVotes.value = Number(status[4]);

      const [names, cids, votes] = allCandidates;
      const list = [];

      for (let i = 0; i < names.length; i++) {
        const item = {
          name: names[i],
          cid: cids[i],
          votes: Number(votes[i]),
          photoUrl: "",
          manifesto: "",
        };

        if (cids[i]) {
          try {
            const res = await fetch(`${IPFS_GATEWAY}${cids[i]}`);
            if (res.ok) {
              const data = await res.json();
              item.photoUrl = data.photo
                ? `${IPFS_GATEWAY}${data.photo}`
                : "";
              item.manifesto = data.manifesto || "";
            }
          } catch {
            // IPFS 加载失败不阻塞渲染
          }
        }

        list.push(item);
      }

      candidates.value = list;
    } catch (err) {
      error.value = "加载候选人失败: " + (err.message || err);
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 检查当前地址的授权和投票状态
   */
  async function checkVoterStatus(address) {
    if (!currentElection.value || !address) return;

    try {
      const contract = getElectionReadContract();
      const [auth, voted] = await Promise.all([
        contract.isAuthorized(address),
        contract.hasVoted(address),
      ]);
      isAuthorized.value = auth;
      hasVoted.value = voted;
    } catch (err) {
      console.error("检查选民状态失败:", err);
    }
  }

  /**
   * 投票 - 直接通过 MetaMask 签名发送至区块链
   */
  async function castVote(candidateId) {
    const contract = await getElectionWriteContract();
    const tx = await contract.vote(candidateId);
    const receipt = await tx.wait();

    if (receipt.status !== 1) {
      throw new Error("投票交易失败");
    }

    hasVoted.value = true;
    return receipt.hash;
  }

  return {
    candidates,
    votingStarted,
    votingEnded,
    totalVoters,
    totalVotes,
    isAuthorized,
    hasVoted,
    loading,
    error,
    currentElection,
    elections,
    startTime,
    endTime,
    loadElections,
    selectElection,
    loadCandidates,
    checkVoterStatus,
    castVote,
    getFactoryReadContract,
    getFactoryWriteContract,
    getElectionReadContract,
    getElectionWriteContract,
  };
});
