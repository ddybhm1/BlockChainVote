<template>
  <div class="election-detail-view">
    <div v-if="!auth.sessionReady" class="card empty-card">
      <p class="empty-title">正在恢复登录会话</p>
      <p class="empty-desc">稍等一下，我们正在读取你的身份状态。</p>
    </div>

    <div v-else-if="!auth.isAuthenticated" class="card empty-card">
      <p class="empty-title">请先登录学号身份</p>
      <p class="empty-desc">登录后才能查看项目详情，并在项目里按需连接钱包完成投票。</p>
      <router-link to="/auth" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else-if="selectedDashboardItem">
      <section class="card intro-card">
        <button class="back-btn" type="button" @click="goBackToDashboard">返回我的项目</button>
        <p class="detail-kicker">Project Workspace</p>
        <h2>{{ selectedDashboardItem.title || "未命名投票项目" }}</h2>
        <p class="intro-desc">
          这里展示当前项目的具体信息、钱包状态、候选人列表和投票入口。你可以先核对项目信息，再决定是否申请投票权或立即投票。
        </p>
      </section>

      <div v-if="pageMessage.text" :class="['alert', pageMessage.type === 'success' ? 'alert-success' : 'alert-error']">
        {{ pageMessage.text }}
      </div>

      <div v-if="!selectedDashboardItem.eligible" class="alert alert-info">
        当前学号还没有被加入这个投票项目的选民名单，所以你现在可以查看项目详情，但不能申请票权或投票。
      </div>

      <ElectionDetailCard
        :item="selectedDashboardItem"
        :start-time="voting.startTime"
        :end-time="voting.endTime"
        :total-votes="voting.totalVotes"
        :candidate-count="voting.candidates.length"
        :wallet-address="wallet.address"
        :wallet-loading="wallet.loading"
        :is-authorized="voting.isAuthorized"
        :has-voted="voting.hasVoted"
        :authorize-loading="authorizeLoading"
        @copy-address="copyAddress"
        @connect-wallet="wallet.connect()"
        @refresh-status="refreshChainStatus"
        @authorize="handleAuthorize"
        @vote-now="scrollToAnchor('candidate-list')"
        @view-results="goToResults"
      />

      <div v-if="voting.error" class="alert alert-error">{{ voting.error }}</div>

      <div v-if="voteTxHash" class="alert alert-success">
        {{ voteSuccessMessage || "操作成功，链上交易已确认。" }}
        <a :href="`https://sepolia.etherscan.io/tx/${voteTxHash}`" target="_blank" rel="noreferrer">
          {{ voteTxHash.slice(0, 22) }}...
        </a>
      </div>

      <div v-if="voteError" class="alert alert-error">{{ voteError }}</div>

      <div v-if="detailLoading || voting.loading" class="loading-text">正在从区块链读取候选人与投票数据...</div>

      <div v-else id="candidate-list" class="candidates-grid">
        <CandidateCard
          v-for="(candidate, index) in voting.candidates"
          :key="index"
          :candidate-id="index"
          :name="candidate.name"
          :cid="candidate.cid"
          :votes="candidate.votes"
          :photo-url="candidate.photoUrl"
          :manifesto="candidate.manifesto"
          :can-vote="canVote"
          :has-voted="voting.hasVoted"
          :has-abstained="voting.hasAbstained"
          :voting-active="voting.votingStarted && !voting.votingEnded"
          :voting-ended="voting.votingEnded"
          @vote="handleVote"
        />
      </div>

      <section
        v-if="!detailLoading && !voting.loading && voting.candidates.length > 0 && !voting.votingEnded"
        class="card abstain-panel"
      >
        <p class="abstain-title">不支持任何候选人？</p>
        <p class="abstain-desc">你可以选择弃票，本次投票资格会被视为已使用，且不会计入任一候选人。</p>
        <button class="btn abstain-btn" type="button" :disabled="!canVote" @click="handleAbstain">
          我不支持任何候选人，选择弃票
        </button>
      </section>

      <div v-if="!detailLoading && !voting.loading && voting.candidates.length === 0" class="card empty-card">
        <p class="empty-title">暂无候选人</p>
        <p class="empty-desc">管理员尚未为这个项目添加候选人。</p>
      </div>
    </template>

    <div v-else class="card empty-card">
      <p class="empty-title">{{ missingElection ? "找不到这个投票项目" : "正在准备项目详情" }}</p>
      <p class="empty-desc">
        <template v-if="missingElection">
          你当前没有该项目的投票权限，或这个项目地址不在你的个人项目列表中。
        </template>
        <template v-else>
          我们正在同步这个项目的状态，请稍后再试。
        </template>
      </p>
      <button class="btn btn-secondary" type="button" @click="goBackToDashboard">返回我的项目</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import CandidateCard from "../components/CandidateCard.vue";
import ElectionDetailCard from "../components/dashboard/ElectionDetailCard.vue";
import { useElectionProjectDetail } from "../composables/useElectionProjectDetail.js";

const route = useRoute();
const electionAddress = computed(() => String(route.params.electionAddress || ""));

const {
  auth,
  wallet,
  voting,
  authorizeLoading,
  detailLoading,
  voteTxHash,
  voteSuccessMessage,
  voteError,
  pageMessage,
  selectedDashboardItem,
  missingElection,
  canVote,
  scrollToAnchor,
  copyAddress,
  refreshChainStatus,
  goToResults,
  goBackToDashboard,
  handleAuthorize,
  handleVote,
  handleAbstain,
} = useElectionProjectDetail(electionAddress);
</script>

<style scoped>
.election-detail-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro-card {
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.12), transparent 28%),
    radial-gradient(circle at bottom right, rgba(37, 99, 235, 0.12), transparent 32%),
    #ffffff;
}

.back-btn {
  border: 1px solid var(--border);
  background: #ffffff;
  color: #0f172a;
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.back-btn:hover {
  background: #f8fafc;
}

.detail-kicker {
  margin: 18px 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 11px;
  color: #0f766e;
  font-weight: 700;
}

.intro-card h2,
.empty-title {
  margin: 0;
}

.intro-desc,
.empty-desc,
.loading-text {
  color: var(--text-secondary);
}

.loading-text {
  text-align: center;
  padding: 24px 10px;
}

.candidates-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.abstain-panel {
  border: 1px solid rgba(180, 83, 9, 0.35);
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.92) 100%);
}

.abstain-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 800;
  color: #78350f;
}

.abstain-desc {
  margin: 0 0 14px;
  color: #92400e;
}

.abstain-btn {
  width: 100%;
  border: 1px solid rgba(113, 63, 18, 0.55);
  background: linear-gradient(135deg, #78716c 0%, #57534e 100%);
  color: #fef3c7;
  font-weight: 700;
}

.abstain-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #6b7280 0%, #44403c 100%);
}

.abstain-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-card {
  text-align: center;
  padding: 48px 24px;
}

.empty-title {
  font-size: 22px;
  font-weight: 700;
}
</style>
