<template>
  <el-container class="vote-master">
    <!-- Loading / Auth States -->
    <el-main class="vote-main" v-if="!auth.sessionReady">
      <el-empty description="正在恢复登录会话，请稍候..."></el-empty>
    </el-main>

    <el-main class="vote-main" v-else-if="!auth.isAuthenticated">
      <el-result
        icon="warning"
        title="需要登录"
        sub-title="请先使用学号登录身份认证，然后即可查看和参与投票"
      >
        <template #extra>
          <router-link to="/auth">
            <el-button type="primary" size="large">前往登录</el-button>
          </router-link>
        </template>
      </el-result>
    </el-main>

    <!-- Main Dashboard -->
    <el-main class="vote-main" v-else>
      <!-- Hero Stats Section -->
      <div class="hero-section">
        <div class="hero-title">
          <h1>投票中心</h1>
          <p>民主决策，链上见证</p>
        </div>
        
        <el-row :gutter="20" class="hero-stats">
          <el-col :xs="24" :sm="12" :md="6">
            <el-card class="stat-card" shadow="hover" @click="jumpByBucket('todo')">
              <div class="stat-icon" style="background: #fef3c7; color: #f59e0b;">📋</div>
              <div class="stat-content">
                <div class="stat-label">待投项目</div>
                <div class="stat-value"><AnimatedNumber :value="todoCount" /></div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card class="stat-card" shadow="hover" @click="jumpByBucket('history')">
              <div class="stat-icon" style="background: #dbeafe; color: #3b82f6;">✓</div>
              <div class="stat-content">
                <div class="stat-label">已完成</div>
                <div class="stat-value"><AnimatedNumber :value="votedCount" /></div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card class="stat-card" shadow="hover" @click="jumpByBucket('claimed')">
              <div class="stat-icon" style="background: #dbeafe; color: #3b82f6;">⏳</div>
              <div class="stat-content">
                <div class="stat-label">已领票待投</div>
                <div class="stat-value"><AnimatedNumber :value="claimedPendingCount" /></div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- Message Alert -->
      <el-alert
        v-if="pageMessage.text"
        :title="pageMessage.text"
        :type="pageMessage.type === 'success' ? 'success' : 'error'"
        show-icon
        closable
        style="margin-bottom: 24px"
      />

      <!-- Search & Filter Section -->
      <el-card class="filter-card" shadow="hover">
        <template #header>
          <div class="card-header-box">
            <span class="section-title">📋 项目列表</span>
            <el-button-group>
              <el-button 
                :type="dashboardLoading ? 'info' : 'default'"
                :icon="dashboardLoading ? 'Loading' : 'RefreshRight'"
                :loading="dashboardLoading"
                @click="refreshDashboard"
              >
                {{ dashboardLoading ? '刷新中' : '刷新' }}
              </el-button>
            </el-button-group>
          </div>
        </template>

        <div class="filter-actions" style="margin-top: 16px;">
          <el-input
            v-model="searchQuery"
            placeholder="搜索项目标题或合约地址..."
            clearable
            prefix-icon="Search"
          />
        </div>
      </el-card>

      <!-- Projects Grid -->
      <el-empty v-if="!filteredDashboardItems.length" description="暂无项目" style="margin-top: 40px" />
      
      <div v-else class="elections-container">
        <el-row :gutter="20">
          <el-col v-for="item in paginatedItems" :key="item.election_address" :xs="24" :sm="12" :md="8">
            <ElectionSummaryCard
              :item="item"
              @select="openElectionDetail"
              @action="handleCardAction"
              @copy-address="copyAddress"
            />
          </el-col>
        </el-row>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="itemsPerPage"
          :page-sizes="[10, 20, 30]"
          :total="filteredDashboardItems.length"
          layout="total, sizes, prev, pager, next"
          @size-change="currentPage = 1"
        />
      </div>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ethers } from "ethers";
import ElectionSummaryCard from "../components/dashboard/ElectionSummaryCard.vue";
import AnimatedNumber from "../components/AnimatedNumber.vue";
import { markVoted } from "../services/api.js";
import { ELECTION_ABI } from "../services/contract.js";
import { useAuthStore } from "../stores/auth.js";
import { useWalletStore } from "../stores/wallet.js";
import { cardCta, isHistoryItem, isTodoItem, sortDashboardItems } from "../utils/dashboard.js";

const auth = useAuthStore();
const wallet = useWalletStore();
const router = useRouter();
const route = useRoute();

const dashboardLoading = ref(false);
const chainSyncing = ref(false);
const searchQuery = ref("");
const currentPage = ref(1);
const itemsPerPage = ref(10);
const pageMessage = reactive({
  type: "success",
  text: "",
});

const dashboardItems = computed(() => auth.myElections);
const sortedDashboardItems = computed(() => sortDashboardItems(dashboardItems.value));
const todoCount = computed(() => dashboardItems.value.filter(isTodoItem).length);
const claimedPendingCount = computed(
  () => dashboardItems.value.filter((item) => item.phase !== "ENDED" && item.status === "CLAIMED").length
);
const votedCount = computed(() => dashboardItems.value.filter((item) => item.phase === "ENDED" || item.status === "VOTED").length);

const routeBucket = computed(() => {
  const value = route.query.bucket;
  return typeof value === "string" ? value : "";
});

function applyBucketFilter(items, bucket) {
  if (bucket === "todo") {
    return items.filter(isTodoItem);
  }
  if (bucket === "history") {
    return items.filter(isHistoryItem);
  }
  if (bucket === "claimed") {
    return items.filter((item) => item.phase !== "ENDED" && item.status === "CLAIMED");
  }
  return items;
}

function applyUnifiedSearch(items, keyword) {
  const query = (keyword || "").trim().toLowerCase();
  if (!query) return items;

  const ranked = items
    .map((item) => {
      const title = (item.title || "").toLowerCase();
      const address = (item.election_address || "").toLowerCase();
      let score = -1;

      if (title === query || address === query) {
        score = 100;
      } else if (title.startsWith(query) || address.startsWith(query)) {
        score = 80;
      } else if (query.length >= 2 && title.includes(query)) {
        score = 60;
      } else if (query.length >= 2 && address.includes(query)) {
        score = 40;
      }

      return { item, score };
    })
    .filter((entry) => entry.score >= 0)
    .sort((left, right) => right.score - left.score || (left.item.title || "").localeCompare(right.item.title || ""));

  return ranked.map((entry) => entry.item);
}

function jumpByBucket(bucket) {
  router.push({ name: "Dashboard", query: { ...route.query, bucket } });
}

const filteredDashboardItems = computed(() => {
  const bucketFiltered = applyBucketFilter(sortedDashboardItems.value, routeBucket.value);
  return applyUnifiedSearch(bucketFiltered, searchQuery.value);
});

const totalPages = computed(() => Math.ceil(filteredDashboardItems.value.length / itemsPerPage.value) || 1);

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  return filteredDashboardItems.value.slice(start, end);
});

watch([routeBucket, searchQuery], () => {
  currentPage.value = 1;
});

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

function openElectionDetail(address) {
  if (!address) return;
  router.push({ name: "DashboardElection", params: { electionAddress: address } });
}

function goToResults(address) {
  router.push({ name: "Results", query: { election: address } });
}

function handleCardAction(item) {
  const cta = cardCta(item);
  if (cta.action === "results") {
    goToResults(item.election_address);
    return;
  }
  openElectionDetail(item.election_address);
}

async function syncCompletedVotesByStudent(items) {
  if (chainSyncing.value || !auth.isAuthenticated || !wallet.address) return false;

  const claimedItems = items.filter((item) => item.phase !== "ENDED" && item.status === "CLAIMED");
  if (!claimedItems.length) return false;

  chainSyncing.value = true;
  try {
    const provider = new ethers.JsonRpcProvider(
      import.meta.env.VITE_SEPOLIA_RPC || "https://rpc.sepolia.org"
    );

    let hasChanges = false;
    for (const item of claimedItems) {
      try {
        const contract = new ethers.Contract(item.election_address, ELECTION_ABI, provider);
        const voted = await contract.hasVoted(wallet.address);
        if (!voted) continue;

        await markVoted(item.election_address, wallet.address);
        hasChanges = true;
      } catch (err) {
        console.warn("同步学号项目完成状态失败:", item.election_address, err);
      }
    }

    return hasChanges;
  } finally {
    chainSyncing.value = false;
  }
}

async function refreshDashboard() {
  if (!auth.isAuthenticated) return;
  dashboardLoading.value = true;
  try {
    const elections = await auth.loadMyElections();
    const synced = await syncCompletedVotesByStudent(elections);
    if (synced) {
      await auth.loadMyElections();
    }
  } finally {
    dashboardLoading.value = false;
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
  async (address, previousAddress) => {
    if (!address || address === previousAddress || !auth.isAuthenticated) return;
    await refreshDashboard();
  }
);
</script>

<style scoped>
.vote-master {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.vote-main {
  padding: 40px 24px;
}

/* Hero Section */
.hero-section {
  margin-bottom: 32px;
}

.hero-title {
  margin-bottom: 24px;
}

.hero-title h1 {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-title p {
  margin: 0;
  font-size: 16px;
  color: #666;
}

.hero-stats {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  height: 100%;
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

/* Filter Card */
.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.card-header-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.filter-row {
  margin-bottom: 16px;
}

.filter-actions {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.demo-tabs {
  margin: 0;
}

/* Elections Container */
.elections-container {
  margin-bottom: 24px;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px 0;
  margin-top: 24px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .vote-main {
    padding: 24px 12px;
  }

  .hero-title h1 {
    font-size: 24px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }

  .stat-value {
    font-size: 24px;
  }
}
</style>
