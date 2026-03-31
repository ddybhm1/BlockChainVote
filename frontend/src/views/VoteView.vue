<template>
  <div class="vote-view">
    <div v-if="!auth.sessionReady" class="card empty-card">
      <p class="empty-title">正在恢复登录会话</p>
      <p class="empty-desc">稍等一下，我们正在读取你的身份状态。</p>
    </div>

    <div v-else-if="!auth.isAuthenticated" class="card empty-card">
      <p class="empty-title">请先登录学号身份</p>
      <p class="empty-desc">登录后才能查看你拥有哪些项目的投票权，并在每个项目里按需连接不同钱包地址。</p>
      <router-link to="/auth" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <section class="card dashboard-hero">
        <div class="hero-main">
          <p class="hero-kicker">My Voting</p>
          <h2>欢迎回来，优先处理待办投票项目</h2>
          <p class="hero-desc">你可以在这里查看所有可参与项目，并根据当前状态直接申请投票权、立即投票，或查看历史结果。</p>

          <div class="hero-actions">
            <button class="btn btn-help" type="button" @click="showHelp = !showHelp">
              {{ showHelp ? "收起说明" : "ℹ 使用说明" }}
            </button>
            <button class="btn btn-secondary" type="button" @click="refreshDashboard" :disabled="dashboardLoading">
              {{ dashboardLoading ? "刷新中..." : "刷新项目状态" }}
            </button>
          </div>

          <div v-if="showHelp" class="help-panel">
            <p>系统先用学号会话确认你的身份，再由 MySQL 记录每个项目的未领票、已领票、已投票状态。</p>
            <p>钱包地址只会在具体项目点击“申请投票权”或“立即投票”时介入，因此你可以在不同项目中切换不同地址保护匿名性。</p>
          </div>
        </div>

        <div class="hero-stats">
          <div class="stat-box">
            <span>全部项目</span>
            <strong>{{ dashboardItems.length }}</strong>
          </div>
          <div class="stat-box">
            <span>待办事项</span>
            <strong>{{ todoCount }}</strong>
          </div>
          <div class="stat-box">
            <span>已领票待投</span>
            <strong>{{ claimedPendingCount }}</strong>
          </div>
          <div class="stat-box">
            <span>已完成</span>
            <strong>{{ votedCount }}</strong>
          </div>
        </div>
      </section>

      <div v-if="pageMessage.text" :class="['alert', pageMessage.type === 'success' ? 'alert-success' : 'alert-error']">
        {{ pageMessage.text }}
      </div>

      <section class="card">
        <div class="section-head">
          <h3>我的项目列表</h3>
          <div class="tabs">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              :class="['tab-btn', { active: activeTab === tab.key }]"
              type="button"
              @click="activeTab = tab.key"
            >
              {{ tab.label }} ({{ tab.count }})
            </button>
          </div>
        </div>

        <div v-if="!filteredDashboardItems.length" class="empty-inline">
          当前筛选条件下暂无项目。
        </div>

        <div v-else class="election-grid">
          <article
            v-for="item in filteredDashboardItems"
            :key="item.election_address"
            :class="['election-card', { active: selectedElection === item.election_address }]"
            @click="handleSelectElection(item.election_address)"
          >
            <div class="card-top">
              <div class="title-stack">
                <h4>{{ displayTitle(item.title) }}</h4>
                <div class="address-line">
                  <span>{{ shortAddress(item.election_address) }}</span>
                  <button class="copy-btn" type="button" @click.stop="copyAddress(item.election_address)">复制</button>
                </div>
              </div>
              <span :class="['badge', phaseBadgeClass(item.phase)]">{{ phaseLabel(item.phase) }}</span>
            </div>

            <div class="ticket-row">
              <span class="ticket-caption">票权状态</span>
              <span :class="['badge', ticketBadgeClass(item.status)]">{{ ticketLabel(item.status) }}</span>
            </div>

            <p class="time-range">{{ formatRangeCompact(item.start_time, item.end_time) }}</p>

            <button
              :class="['card-cta', cardCta(item).className]"
              :disabled="cardCta(item).disabled"
              type="button"
              @click.stop="handleCardAction(item)"
            >
              {{ cardCta(item).label }}
            </button>
          </article>
        </div>
      </section>

      <template v-if="selectedDashboardItem">
        <section id="election-detail" class="card detail-card">
          <div class="detail-head">
            <div>
              <p class="detail-kicker">当前项目</p>
              <h3>{{ displayTitle(selectedDashboardItem.title) }}</h3>
              <div class="detail-address-row">
                <span>{{ shortAddress(selectedDashboardItem.election_address) }}</span>
                <button class="copy-btn" type="button" @click="copyAddress(selectedDashboardItem.election_address)">复制地址</button>
              </div>
            </div>

            <div class="detail-badges">
              <span :class="['badge', phaseBadgeClass(selectedDashboardItem.phase)]">{{ phaseLabel(selectedDashboardItem.phase) }}</span>
              <span :class="['badge', ticketBadgeClass(selectedDashboardItem.status)]">{{ ticketLabel(selectedDashboardItem.status) }}</span>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-panel">
              <h4>项目概览</h4>
              <p><strong>投票时间：</strong>{{ formatRangeFull(voting.startTime || selectedDashboardItem.start_time, voting.endTime || selectedDashboardItem.end_time) }}</p>
              <p><strong>链上已投票数：</strong>{{ voting.totalVotes }}</p>
              <p><strong>候选人数：</strong>{{ voting.candidates.length }}</p>
            </div>

            <div id="wallet-operation" class="detail-panel wallet-panel">
              <h4>钱包操作</h4>
              <p class="wallet-copy">
                <template v-if="wallet.address">
                  当前钱包：<strong>{{ shortAddress(wallet.address) }}</strong>
                </template>
                <template v-else>
                  当前未连接钱包，请在需要操作的项目里临时连接。
                </template>
              </p>

              <div class="wallet-actions">
                <button class="btn btn-primary" type="button" @click="wallet.connect()" :disabled="wallet.loading">
                  {{ wallet.loading ? "连接中..." : wallet.address ? "切换钱包" : "连接钱包" }}
                </button>
                <button v-if="wallet.address" class="btn btn-secondary" type="button" @click="refreshChainStatus">
                  检查当前地址状态
                </button>
              </div>

              <div class="wallet-state">
                <span class="mini-state">链上授权：{{ wallet.address ? (voting.isAuthorized ? "是" : "否") : "-" }}</span>
                <span class="mini-state">链上已投：{{ wallet.address ? (voting.hasVoted ? "是" : "否") : "-" }}</span>
              </div>

              <p class="wallet-hint">
                <template v-if="selectedDashboardItem.status === 'AVAILABLE'">
                  这是你当前最需要处理的项目。连接一个钱包后点击“申请投票权”，系统就会为这个项目授予该地址投票资格。
                </template>
                <template v-else-if="selectedDashboardItem.status === 'CLAIMED'">
                  这个项目已经领票，请切换到当时授权的钱包地址后直接投票。
                </template>
                <template v-else>
                  这个项目已经完成或结束，现在更适合查看结果和留档。
                </template>
              </p>

              <div class="wallet-cta-row">
                <button
                  v-if="selectedDashboardItem.status === 'AVAILABLE' && selectedDashboardItem.phase === 'ACTIVE'"
                  class="btn btn-claim"
                  type="button"
                  :disabled="authorizeLoading || !wallet.address"
                  @click="handleAuthorize"
                >
                  {{ authorizeLoading ? "申请中..." : "申请投票权" }}
                </button>
                <button
                  v-else-if="selectedDashboardItem.status === 'CLAIMED' && selectedDashboardItem.phase === 'ACTIVE'"
                  class="btn btn-primary"
                  type="button"
                  @click="scrollToAnchor('candidate-list')"
                >
                  立即投票
                </button>
                <button
                  v-else-if="selectedDashboardItem.phase === 'PENDING'"
                  class="btn btn-disabled"
                  type="button"
                  disabled
                >
                  敬请期待
                </button>
                <button
                  v-else
                  class="btn btn-secondary"
                  type="button"
                  @click="goToResults(selectedDashboardItem.election_address)"
                >
                  查看结果
                </button>
              </div>
            </div>
          </div>
        </section>

        <div v-if="voting.error" class="alert alert-error">{{ voting.error }}</div>

        <div v-if="voteTxHash" class="alert alert-success">
          投票成功，链上交易已确认，SBT 纪念徽章也已铸造。
          <a :href="`https://sepolia.etherscan.io/tx/${voteTxHash}`" target="_blank" rel="noreferrer">
            {{ voteTxHash.slice(0, 22) }}...
          </a>
        </div>

        <div v-if="voteError" class="alert alert-error">{{ voteError }}</div>

        <section v-if="wallet.address && voting.badge" class="card badge-showcase">
          <div class="badge-copy">
            <p class="detail-kicker">Soulbound Token</p>
            <h3>我的投票纪念徽章</h3>
            <p class="badge-desc">只有成功完成投票的钱包才能领取，适合作为本次参与的链上纪念。</p>

            <div class="badge-meta">
              <div class="meta-chip">
                <span>徽章名称</span>
                <strong>{{ voting.badge.name }}</strong>
              </div>
              <div class="meta-chip">
                <span>Token ID</span>
                <strong>#{{ voting.badge.tokenId }}</strong>
              </div>
              <div class="meta-chip">
                <span>绑定地址</span>
                <strong>{{ shortAddress(wallet.address) }}</strong>
              </div>
            </div>

            <p class="badge-detail">{{ voting.badge.description }}</p>
          </div>

          <div class="badge-card">
            <img
              v-if="voting.badge.image"
              :src="voting.badge.image"
              :alt="voting.badge.name"
              class="badge-image"
            />
            <div class="badge-footer">
              <span class="badge-pill">SBT · Non-transferable</span>
              <span class="badge-pill">{{ displayTitle(selectedDashboardItem.title) }}</span>
            </div>
          </div>
        </section>

        <div v-if="voting.loading" class="loading-text">正在从区块链读取候选人与投票数据...</div>

        <div v-else id="candidate-list" class="candidates-grid">
          <CandidateCard
            v-for="(candidate, index) in voting.candidates"
            :key="index"
            :candidateId="index"
            :name="candidate.name"
            :cid="candidate.cid"
            :votes="candidate.votes"
            :photoUrl="candidate.photoUrl"
            :manifesto="candidate.manifesto"
            :canVote="canVote"
            :hasVoted="selectedDashboardItem.status === 'VOTED' || voting.hasVoted"
            :votingActive="voting.votingStarted && !voting.votingEnded"
            :votingEnded="voting.votingEnded"
            @vote="handleVote"
          />
        </div>

        <div v-if="!voting.loading && voting.candidates.length === 0" class="card empty-card">
          <p class="empty-title">暂无候选人</p>
          <p class="empty-desc">管理员尚未为这个项目添加候选人。</p>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import CandidateCard from "../components/CandidateCard.vue";
import { authorizeTicket, markVoteComplete } from "../services/api.js";
import { useAuthStore } from "../stores/auth.js";
import { useVotingStore } from "../stores/voting.js";
import { useWalletStore } from "../stores/wallet.js";

const auth = useAuthStore();
const voting = useVotingStore();
const wallet = useWalletStore();
const router = useRouter();

const dashboardLoading = ref(false);
const authorizeLoading = ref(false);
const selectedElection = ref("");
const activeTab = ref("todo");
const showHelp = ref(false);
const voteTxHash = ref("");
const voteError = ref("");
const pageMessage = reactive({
  type: "success",
  text: "",
});

const dashboardItems = computed(() => auth.myElections.map((item) => ({ ...item })));
const todoCount = computed(() => dashboardItems.value.filter(isTodoItem).length);
const claimedPendingCount = computed(() => dashboardItems.value.filter((item) => item.phase === "ACTIVE" && item.status === "CLAIMED").length);
const votedCount = computed(() => dashboardItems.value.filter((item) => item.status === "VOTED").length);

const tabs = computed(() => [
  { key: "todo", label: "待办事项", count: todoCount.value },
  { key: "all", label: "全部项目", count: dashboardItems.value.length },
  { key: "history", label: "已参与/历史", count: dashboardItems.value.filter(isHistoryItem).length },
]);

const filteredDashboardItems = computed(() => {
  const items = [...dashboardItems.value];
  const rank = { ACTIVE: 0, PENDING: 1, ENDED: 2 };
  items.sort((left, right) => {
    const phaseGap = (rank[left.phase] ?? 9) - (rank[right.phase] ?? 9);
    if (phaseGap !== 0) return phaseGap;
    return (left.start_time || 0) - (right.start_time || 0);
  });

  if (activeTab.value === "todo") {
    return items.filter(isTodoItem);
  }
  if (activeTab.value === "history") {
    return items.filter(isHistoryItem);
  }
  return items;
});

const selectedDashboardItem = computed(() => {
  return dashboardItems.value.find((item) => item.election_address === selectedElection.value) || null;
});

const canVote = computed(() => {
  return Boolean(
    auth.isAuthenticated &&
    wallet.address &&
    selectedDashboardItem.value?.status !== "VOTED" &&
    selectedDashboardItem.value?.phase === "ACTIVE" &&
    voting.isAuthorized &&
    !voting.hasVoted &&
    voting.votingStarted &&
    !voting.votingEnded
  );
});

function isTodoItem(item) {
  return item.phase === "ACTIVE" && item.status !== "VOTED";
}

function isHistoryItem(item) {
  return item.phase === "ENDED" || item.status === "VOTED";
}

function displayTitle(title) {
  return title?.trim() || "未命名投票项目";
}

function shortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function formatDateTime(timestamp) {
  if (!timestamp) return "待公布";
  const date = new Date(Number(timestamp) * 1000);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${month}-${day} ${hours}:${minutes}`;
}

function formatRangeCompact(startTime, endTime) {
  if (!startTime || !endTime) return "时间待公布";
  return `${formatDateTime(startTime)} 至 ${formatDateTime(endTime)}`;
}

function formatRangeFull(startTime, endTime) {
  if (!startTime || !endTime) return "时间待公布";
  return `${new Date(Number(startTime) * 1000).toLocaleString()} 至 ${new Date(Number(endTime) * 1000).toLocaleString()}`;
}

function phaseLabel(phase) {
  if (phase === "ACTIVE") return "进行中";
  if (phase === "PENDING") return "未开始";
  return "已结束";
}

function phaseBadgeClass(phase) {
  if (phase === "ACTIVE") return "badge-phase-active";
  if (phase === "PENDING") return "badge-phase-pending";
  return "badge-phase-ended";
}

function ticketLabel(status) {
  if (status === "AVAILABLE") return "未领票";
  if (status === "CLAIMED") return "已领票";
  return "已投票";
}

function ticketBadgeClass(status) {
  if (status === "AVAILABLE") return "badge-ticket-available";
  if (status === "CLAIMED") return "badge-ticket-claimed";
  return "badge-ticket-voted";
}

function cardCta(item) {
  if (item.phase === "ACTIVE" && item.status === "AVAILABLE") {
    return { label: "申请投票权", className: "cta-claim", disabled: false, action: "claim" };
  }
  if (item.phase === "ACTIVE" && item.status === "CLAIMED") {
    return { label: "立即投票", className: "cta-vote", disabled: false, action: "vote" };
  }
  if (item.phase === "PENDING") {
    return { label: "敬请期待", className: "cta-disabled", disabled: true, action: "pending" };
  }
  return { label: "查看结果", className: "cta-result", disabled: false, action: "results" };
}

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

function ensureSelectedElection() {
  if (!filteredDashboardItems.value.length) {
    selectedElection.value = "";
    return;
  }

  const stillVisible = filteredDashboardItems.value.some((item) => item.election_address === selectedElection.value);
  if (!stillVisible) {
    selectedElection.value = filteredDashboardItems.value[0].election_address;
  }
}

async function loadSelectedElectionData() {
  if (!selectedElection.value) return;

  voteTxHash.value = "";
  voteError.value = "";

  await voting.selectElection(selectedElection.value);
  await voting.loadCandidates();
  await refreshChainStatus();
}

async function refreshChainStatus() {
  if (!selectedElection.value) return;

  if (!wallet.address) {
    voting.isAuthorized = false;
    voting.hasVoted = false;
    await voting.loadBadge("");
    return;
  }

  await voting.checkVoterStatus(wallet.address);
  await voting.loadBadge(wallet.address);
}

async function refreshDashboard() {
  if (!auth.isAuthenticated) return;

  dashboardLoading.value = true;

  try {
    await auth.loadMyElections();
    ensureSelectedElection();
    await loadSelectedElectionData();
  } finally {
    dashboardLoading.value = false;
  }
}

async function handleSelectElection(address) {
  if (!address) return;
  if (selectedElection.value === address) {
    await loadSelectedElectionData();
    return;
  }
  selectedElection.value = address;
}

async function handleCardAction(item) {
  const cta = cardCta(item);
  if (cta.disabled) return;

  if (cta.action === "results") {
    goToResults(item.election_address);
    return;
  }

  await handleSelectElection(item.election_address);
  scrollToAnchor("wallet-operation");

  if (cta.action === "vote") {
    window.setTimeout(() => {
      scrollToAnchor(voting.isAuthorized ? "candidate-list" : "wallet-operation");
    }, 120);
  }
}

function goToResults(address) {
  router.push({ name: "Results", query: { election: address } });
}

async function handleAuthorize() {
  if (!selectedDashboardItem.value || !wallet.address) return;

  authorizeLoading.value = true;
  pageMessage.text = "";

  try {
    const data = await authorizeTicket(selectedDashboardItem.value.election_address, wallet.address);
    pageMessage.type = "success";
    pageMessage.text = data.message;
    await auth.loadMyElections();
    await loadSelectedElectionData();
  } catch (err) {
    pageMessage.type = "error";
    pageMessage.text = err.response?.data?.detail || err.message || "领票失败";
  } finally {
    authorizeLoading.value = false;
  }
}

async function handleVote(candidateId) {
  voteError.value = "";
  voteTxHash.value = "";

  try {
    const txHash = await voting.castVote(candidateId);
    voteTxHash.value = txHash;

    await markVoteComplete(selectedElection.value, wallet.address, txHash);
    await auth.loadMyElections();
    await voting.loadCandidates();
    await refreshChainStatus();
  } catch (err) {
    voteError.value = err.response?.data?.detail || err.message || "投票失败";
  }
}

watch(
  () => [auth.sessionReady, auth.isAuthenticated],
  async ([ready, isAuthenticated]) => {
    if (!ready || !isAuthenticated) return;
    await refreshDashboard();
  },
  { immediate: true }
);

watch(
  () => wallet.address,
  async () => {
    if (!selectedElection.value) return;
    await refreshChainStatus();
  }
);

watch(
  filteredDashboardItems,
  async () => {
    ensureSelectedElection();
  }
);

watch(
  selectedElection,
  async (address, previousAddress) => {
    if (!address || address === previousAddress) return;
    await loadSelectedElectionData();
  }
);
</script>

<style scoped>
.vote-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 420px);
  gap: 18px;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.12), transparent 30%),
    radial-gradient(circle at bottom right, rgba(99, 102, 241, 0.12), transparent 35%),
    #ffffff;
}

.hero-kicker,
.detail-kicker {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 11px;
  color: #0f766e;
  font-weight: 700;
}

.dashboard-hero h2,
.detail-head h3 {
  margin: 0;
}

.hero-desc,
.help-panel p,
.wallet-hint,
.wallet-copy,
.empty-desc,
.badge-desc,
.badge-detail {
  color: var(--text-secondary);
}

.hero-actions,
.wallet-actions,
.wallet-cta-row,
.detail-badges,
.section-head,
.card-top,
.ticket-row,
.badge-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-actions {
  margin-top: 18px;
  flex-wrap: wrap;
}

.btn-help {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid var(--border);
}

.btn-secondary {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid var(--border);
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fafc;
}

.help-panel {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(15, 118, 110, 0.15);
  background: rgba(240, 253, 250, 0.9);
}

.help-panel p {
  margin: 0;
}

.help-panel p + p {
  margin-top: 8px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stat-box {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.88);
}

.stat-box span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-box strong {
  font-size: 34px;
  line-height: 1;
}

.section-head {
  justify-content: space-between;
  flex-wrap: wrap;
}

.section-head h3 {
  margin: 0;
}

.tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tab-btn {
  border: 1px solid var(--border);
  background: #ffffff;
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}

.empty-inline,
.loading-text {
  padding: 24px 10px;
  text-align: center;
  color: var(--text-secondary);
}

.election-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.election-card {
  padding: 22px;
  border-radius: 22px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, #ffffff, #fbfcfe);
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.03);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.election-card:hover,
.election-card.active {
  transform: translateY(-2px);
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.08);
}

.title-stack h4 {
  margin: 0;
  font-size: 22px;
  line-height: 1.25;
}

.address-line,
.detail-address-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.copy-btn {
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.copy-btn:hover {
  color: #0f172a;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.badge-phase-active {
  background: #e9f9ef;
  color: #0f8f4b;
}

.badge-phase-pending {
  background: #fff4df;
  color: #c27803;
}

.badge-phase-ended {
  background: #f1f5f9;
  color: #64748b;
}

.badge-ticket-available {
  background: #fff1f2;
  color: #d9485f;
}

.badge-ticket-claimed {
  background: #eef4ff;
  color: #2563eb;
}

.badge-ticket-voted {
  background: #eaf8ef;
  color: #13803d;
}

.ticket-row {
  justify-content: space-between;
  margin-top: 18px;
}

.ticket-caption,
.time-range {
  color: var(--text-secondary);
}

.ticket-caption {
  font-size: 13px;
}

.time-range {
  margin: 16px 0 20px;
  font-size: 15px;
  font-weight: 600;
}

.card-cta {
  width: 100%;
  border: none;
  border-radius: 14px;
  padding: 14px 16px;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.16s ease, opacity 0.16s ease, box-shadow 0.16s ease;
}

.card-cta:not(:disabled):hover {
  transform: translateY(-1px);
}

.cta-claim {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.2);
}

.cta-vote {
  background: linear-gradient(135deg, #0f172a, #1e3a8a);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18);
}

.cta-result {
  background: #f8fafc;
  color: #334155;
  border: 1px solid #dbe3ee;
}

.cta-disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.detail-card {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 28%),
    #ffffff;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.detail-panel {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #ffffff;
}

.detail-panel h4 {
  margin-top: 0;
}

.wallet-panel {
  background: linear-gradient(180deg, #ffffff, #f8fbff);
}

.wallet-actions,
.wallet-cta-row {
  margin: 16px 0 0;
  flex-wrap: wrap;
}

.wallet-state {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.mini-state {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-secondary);
}

.wallet-hint {
  margin: 16px 0 0;
}

.btn-claim {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
}

.btn-disabled {
  background: #e5e7eb;
  color: #94a3b8;
  cursor: not-allowed;
}

.badge-showcase {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 420px);
  gap: 20px;
  align-items: center;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.14), transparent 30%),
    #ffffff;
}

.badge-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0;
}

.meta-chip {
  min-width: 140px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid var(--border);
}

.meta-chip span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.badge-card {
  padding: 22px;
  border-radius: 22px;
  background: linear-gradient(180deg, #0f172a, #111827);
  color: #ffffff;
}

.badge-image {
  width: 100%;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
}

.badge-pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 12px;
}

.candidates-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-card {
  text-align: center;
  padding: 48px 24px;
}

.empty-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
}

@media (max-width: 960px) {
  .dashboard-hero,
  .detail-grid,
  .badge-showcase {
    grid-template-columns: 1fr;
  }

  .detail-head,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
