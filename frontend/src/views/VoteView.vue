<template>
  <div class="vote-view">
    <div class="card">
      <ElectionSelector v-model="selectedElection" />
    </div>

    <template v-if="selectedElection">
      <div class="card status-bar">
        <div class="status-item">
          <span class="status-label">投票状态</span>
          <span :class="['status-badge', statusClass]">{{ statusText }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">候选人</span>
          <span class="status-value">{{ voting.candidates.length }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">已投票</span>
          <span class="status-value">{{ voting.totalVotes }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">我的状态</span>
          <span :class="['status-badge', myStatusClass]">{{ myStatusText }}</span>
        </div>
        <button class="btn btn-primary" @click="refreshData" :disabled="voting.loading" style="padding:6px 14px;font-size:13px">
          🔄 刷新
        </button>
      </div>

      <div v-if="voting.error" class="alert alert-error">{{ voting.error }}</div>

      <div v-if="voteTxHash" class="alert alert-success">
        投票成功！交易哈希:
        <a :href="`https://sepolia.etherscan.io/tx/${voteTxHash}`" target="_blank">
          {{ voteTxHash.slice(0, 22) }}...
        </a>
      </div>

      <div v-if="voteError" class="alert alert-error">{{ voteError }}</div>

      <div v-if="voting.loading" class="loading-text">正在从区块链读取数据...</div>

      <div v-else class="candidates-grid">
        <CandidateCard
          v-for="(c, i) in voting.candidates"
          :key="i"
          :candidateId="i"
          :name="c.name"
          :cid="c.cid"
          :votes="c.votes"
          :photoUrl="c.photoUrl"
          :manifesto="c.manifesto"
          :canVote="canVote"
          :hasVoted="voting.hasVoted"
          :votingActive="voting.votingStarted && !voting.votingEnded"
          :votingEnded="voting.votingEnded"
          @vote="handleVote"
        />
      </div>

      <div v-if="!voting.loading && voting.candidates.length === 0" class="card" style="text-align:center;padding:40px">
        <p style="font-size:18px;margin-bottom:8px">暂无候选人</p>
        <p style="color:var(--text-secondary)">管理员尚未添加候选人信息</p>
      </div>
    </template>

    <div v-else class="card" style="text-align:center;padding:40px">
      <p style="font-size:18px;margin-bottom:8px">请先选择投票项目</p>
      <p style="color:var(--text-secondary)">在上方下拉框中选择要参与投票的项目</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useWalletStore } from "../stores/wallet.js";
import { useVotingStore } from "../stores/voting.js";
import CandidateCard from "../components/CandidateCard.vue";
import ElectionSelector from "../components/ElectionSelector.vue";

const wallet = useWalletStore();
const voting = useVotingStore();
const voteTxHash = ref("");
const voteError = ref("");
const selectedElection = ref("");

// 切换项目时加载数据
watch(selectedElection, async (addr) => {
  if (!addr) return;
  voteTxHash.value = "";
  voteError.value = "";
  voting.selectElection(addr);
  await voting.loadCandidates();
  if (wallet.address) {
    await voting.checkVoterStatus(wallet.address);
  }
});

const canVote = computed(() => {
  return (
    wallet.address &&
    voting.isAuthorized &&
    !voting.hasVoted &&
    voting.votingStarted &&
    !voting.votingEnded
  );
});

const statusText = computed(() => {
  if (!voting.votingStarted) return "未开始";
  if (voting.votingEnded) return "投票已经结束";
  return "进行中";
});

const statusClass = computed(() => {
  if (!voting.votingStarted) return "badge-warning";
  if (voting.votingEnded) return "badge-danger";
  return "badge-success";
});

const myStatusText = computed(() => {
  if (!wallet.address) return "未连接钱包";
  if (voting.hasVoted) return "已投票";
  if (voting.isAuthorized) return "有投票权";
  return "未授权";
});

const myStatusClass = computed(() => {
  if (voting.hasVoted) return "badge-success";
  if (voting.isAuthorized) return "badge-info";
  return "badge-warning";
});

async function handleVote(candidateId) {
  voteError.value = "";
  voteTxHash.value = "";
  try {
    const txHash = await voting.castVote(candidateId);
    voteTxHash.value = txHash;
    await voting.loadCandidates();
    await voting.checkVoterStatus(wallet.address);
  } catch (err) {
    voteError.value = err.message || "投票失败";
  }
}

async function refreshData() {
  await voting.loadCandidates();
  if (wallet.address) {
    await voting.checkVoterStatus(wallet.address);
  }
}
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.status-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.status-label {
  font-size: 12px;
  color: var(--text-secondary);
}
.status-value {
  font-size: 18px;
  font-weight: 700;
}
.status-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}
.badge-success {
  background: #ecfdf5;
  color: #059669;
}
.badge-warning {
  background: #fffbeb;
  color: #d97706;
}
.badge-danger {
  background: #fef2f2;
  color: #dc2626;
}
.badge-info {
  background: #eff6ff;
  color: #2563eb;
}
.candidates-grid {
  display: grid;
  gap: 16px;
}
.loading-text {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}
</style>
