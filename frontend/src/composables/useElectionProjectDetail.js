import { computed, reactive, ref, unref, watch } from "vue";
import { useRouter } from "vue-router";
import { authorizeTicket, markVoteComplete } from "../services/api.js";
import { useAuthStore } from "../stores/auth.js";
import { useVotingStore } from "../stores/voting.js";
import { useWalletStore } from "../stores/wallet.js";

function normalizeElectionAddress(value) {
  return (value || "").trim().toLowerCase();
}

export function useElectionProjectDetail(electionAddressRef) {
  const auth = useAuthStore();
  const voting = useVotingStore();
  const wallet = useWalletStore();
  const router = useRouter();

  const authorizeLoading = ref(false);
  const detailLoading = ref(false);
  const voteTxHash = ref("");
  const voteError = ref("");
  const pageMessage = reactive({
    type: "success",
    text: "",
  });

  const electionAddress = computed(() => normalizeElectionAddress(unref(electionAddressRef)));
  const selectedDashboardItem = computed(
    () =>
      auth.myElections.find((item) => normalizeElectionAddress(item.election_address) === electionAddress.value) || null
  );
  const missingElection = computed(
    () => auth.sessionReady && auth.isAuthenticated && Boolean(electionAddress.value) && !selectedDashboardItem.value
  );

  const canVote = computed(() =>
    Boolean(
      auth.isAuthenticated &&
        wallet.address &&
        selectedDashboardItem.value?.eligible &&
        selectedDashboardItem.value?.status !== "VOTED" &&
        selectedDashboardItem.value?.phase === "ACTIVE" &&
        voting.isAuthorized &&
        !voting.hasVoted &&
        voting.votingStarted &&
        !voting.votingEnded
    )
  );

  function scrollToAnchor(id) {
    const node = window.document.getElementById(id);
    if (!node) return;
    node.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function copyAddress(address) {
    try {
      await navigator.clipboard.writeText(address);
      pageMessage.type = "success";
      pageMessage.text = "合约地址已复制到剪贴板";
    } catch {
      pageMessage.type = "error";
      pageMessage.text = "复制失败，请稍后重试";
    }
  }

  async function refreshChainStatus() {
    if (!electionAddress.value) return;

    if (!wallet.address) {
      voting.isAuthorized = false;
      voting.hasVoted = false;
      await voting.loadBadge("");
      return;
    }

    await voting.checkVoterStatus(wallet.address);
    await voting.loadBadge(wallet.address);
  }

  async function loadElectionData({ reloadDashboard = false } = {}) {
    if (!auth.isAuthenticated || !electionAddress.value) return;

    detailLoading.value = true;

    try {
      if (reloadDashboard || !auth.myElections.length || !selectedDashboardItem.value) {
        await auth.loadMyElections();
      }

      if (!selectedDashboardItem.value) {
        await voting.selectElection("");
        return;
      }

      await voting.selectElection(selectedDashboardItem.value.election_address);
      await voting.loadCandidates();
      await refreshChainStatus();
    } finally {
      detailLoading.value = false;
    }
  }

  function goToResults() {
    if (!electionAddress.value) return;
    router.push({ name: "Results", query: { election: electionAddress.value } });
  }

  function goBackToDashboard() {
    router.push({ name: "Dashboard" });
  }

  async function handleAuthorize() {
    if (!selectedDashboardItem.value || !wallet.address) return;

    authorizeLoading.value = true;
    pageMessage.text = "";

    try {
      const data = await authorizeTicket(selectedDashboardItem.value.election_address, wallet.address);
      pageMessage.type = "success";
      pageMessage.text = data.message;
      await loadElectionData({ reloadDashboard: true });
    } catch (err) {
      pageMessage.type = "error";
      pageMessage.text = err.response?.data?.detail || err.message || "领票失败";
    } finally {
      authorizeLoading.value = false;
    }
  }

  async function handleVote(candidateId) {
    if (!selectedDashboardItem.value) return;

    voteError.value = "";
    voteTxHash.value = "";

    try {
      const txHash = await voting.castVote(candidateId);
      voteTxHash.value = txHash;

      await markVoteComplete(selectedDashboardItem.value.election_address, wallet.address, txHash);
      await loadElectionData({ reloadDashboard: true });
    } catch (err) {
      voteError.value = err.response?.data?.detail || err.message || "投票失败";
    }
  }

  watch(
    () => [auth.sessionReady, auth.isAuthenticated, electionAddress.value],
    async ([ready, isAuthenticated, currentAddress], previous = []) => {
      const previousAddress = previous[2];
      if (!ready) return;

      if (!isAuthenticated || !currentAddress) {
        return;
      }

      if (currentAddress !== previousAddress) {
        voteTxHash.value = "";
        voteError.value = "";
        pageMessage.text = "";
      }

      await loadElectionData();
    },
    { immediate: true }
  );

  watch(
    () => wallet.address,
    async () => {
      if (!selectedDashboardItem.value) return;
      await refreshChainStatus();
    }
  );

  return {
    auth,
    wallet,
    voting,
    authorizeLoading,
    detailLoading,
    voteTxHash,
    voteError,
    pageMessage,
    selectedDashboardItem,
    missingElection,
    canVote,
    scrollToAnchor,
    copyAddress,
    refreshChainStatus,
    loadElectionData,
    goToResults,
    goBackToDashboard,
    handleAuthorize,
    handleVote,
  };
}
