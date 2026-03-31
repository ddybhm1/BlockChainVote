import { defineStore } from "pinia";
import { ref } from "vue";
import { ethers } from "ethers";
import { useWalletStore } from "./wallet.js";
import { ELECTION_ABI, FACTORY_ABI, FACTORY_ADDRESS, IPFS_GATEWAY } from "../services/contract.js";

function decodeBase64Utf8(value) {
  const binary = window.atob(value);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function parseTokenMetadata(tokenUri) {
  if (!tokenUri) return null;

  if (tokenUri.startsWith("data:application/json;base64,")) {
    const encoded = tokenUri.slice("data:application/json;base64,".length);
    return JSON.parse(decodeBase64Utf8(encoded));
  }

  if (tokenUri.startsWith("data:application/json;utf8,")) {
    const encoded = tokenUri.slice("data:application/json;utf8,".length);
    return JSON.parse(decodeURIComponent(encoded));
  }

  return {
    name: "Vote Badge",
    description: "",
    image: "",
    external_url: tokenUri,
  };
}

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

  const currentElection = ref("");
  const elections = ref([]);
  const startTime = ref(0);
  const endTime = ref(0);
  const badge = ref(null);

  function getProvider() {
    return new ethers.JsonRpcProvider(
      import.meta.env.VITE_SEPOLIA_RPC || "https://rpc.sepolia.org"
    );
  }

  function getFactoryReadContract() {
    return new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, getProvider());
  }

  async function getFactoryWriteContract() {
    const wallet = useWalletStore();
    const signer = await wallet.getSigner();
    if (!signer) throw new Error("请先连接 MetaMask 钱包");
    return new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, signer);
  }

  function getElectionReadContract(addr) {
    const address = addr || currentElection.value;
    if (!address) throw new Error("未选择投票项目");
    return new ethers.Contract(address, ELECTION_ABI, getProvider());
  }

  async function getElectionWriteContract(addr) {
    const address = addr || currentElection.value;
    if (!address) throw new Error("未选择投票项目");

    const wallet = useWalletStore();
    const signer = await wallet.getSigner();
    if (!signer) throw new Error("请先连接 MetaMask 钱包");

    return new ethers.Contract(address, ELECTION_ABI, signer);
  }

  async function loadElections() {
    if (!FACTORY_ADDRESS) {
      error.value = "工厂合约地址未配置";
      return;
    }

    try {
      const factory = getFactoryReadContract();
      const [addrs, titles, creators, createdAts] = await factory.getAllElections();

      elections.value = addrs.map((address, index) => ({
        address,
        title: titles[index],
        creator: creators[index],
        createdAt: Number(createdAts[index]),
      }));
    } catch (err) {
      console.error("加载投票项目列表失败:", err);
      error.value = "加载项目列表失败: " + (err.message || err);
    }
  }

  async function selectElection(addr) {
    currentElection.value = addr;
    candidates.value = [];
    votingStarted.value = false;
    votingEnded.value = false;
    totalVoters.value = 0;
    totalVotes.value = 0;
    isAuthorized.value = false;
    hasVoted.value = false;
    startTime.value = 0;
    endTime.value = 0;
    badge.value = null;

    if (!addr) return;

    try {
      const contract = getElectionReadContract(addr);
      startTime.value = Number(await contract.votingStartTime());
      endTime.value = Number(await contract.votingEndTime());
    } catch {
      // ignore
    }
  }

  async function loadCandidates() {
    if (!currentElection.value) {
      error.value = "请先选择投票项目";
      return;
    }

    loading.value = true;
    error.value = "";

    try {
      const contract = getElectionReadContract();
      const [status, allCandidates, chainStartTime, chainEndTime] = await Promise.all([
        contract.getVotingStatus(),
        contract.getAllCandidates(),
        contract.votingStartTime(),
        contract.votingEndTime(),
      ]);

      votingStarted.value = status[0];
      votingEnded.value = status[1];
      totalVoters.value = Number(status[3]);
      totalVotes.value = Number(status[4]);
      startTime.value = Number(chainStartTime);
      endTime.value = Number(chainEndTime);

      const [names, cids, votes] = allCandidates;
      const list = [];

      for (let i = 0; i < names.length; i += 1) {
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
              item.photoUrl = data.photo ? `${IPFS_GATEWAY}${data.photo}` : "";
              item.manifesto = data.manifesto || "";
            }
          } catch {
            // IPFS failures should not block the ballot view.
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

  async function checkVoterStatus(address) {
    if (!currentElection.value || !address) return;

    try {
      const contract = getElectionReadContract();
      const [authorized, voted] = await Promise.all([
        contract.isAuthorized(address),
        contract.hasVoted(address),
      ]);

      isAuthorized.value = authorized;
      hasVoted.value = voted;
    } catch (err) {
      console.error("检查选民状态失败:", err);
    }
  }

  async function loadBadge(holderAddress) {
    if (!currentElection.value || !holderAddress) {
      badge.value = null;
      return null;
    }

    try {
      const contract = getElectionReadContract();
      const ownsBadge = await contract.hasBadge(holderAddress);

      if (!ownsBadge) {
        badge.value = null;
        return null;
      }

      const tokenId = Number(await contract.badgeTokenOf(holderAddress));
      const [tokenUri, badgeName, badgeDescription] = await Promise.all([
        contract.tokenURI(tokenId),
        contract.badgeDisplayName(),
        contract.badgeDescription(),
      ]);

      const metadata = parseTokenMetadata(tokenUri) || {};
      badge.value = {
        tokenId,
        tokenUri,
        name: metadata.name || badgeName,
        description: metadata.description || badgeDescription,
        image: metadata.image || "",
        attributes: metadata.attributes || [],
      };

      return badge.value;
    } catch (err) {
      console.error("加载投票徽章失败:", err);
      badge.value = null;
      return null;
    }
  }

  async function castVote(candidateId) {
    const contract = await getElectionWriteContract();
    const tx = await contract.vote(candidateId);
    const receipt = await tx.wait();

    if (receipt.status !== 1) {
      throw new Error("投票交易失败");
    }

    hasVoted.value = true;
    return tx.hash;
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
    badge,
    loadElections,
    selectElection,
    loadCandidates,
    checkVoterStatus,
    loadBadge,
    castVote,
    getFactoryReadContract,
    getFactoryWriteContract,
    getElectionReadContract,
    getElectionWriteContract,
  };
});
