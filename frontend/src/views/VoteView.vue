<template>
  <div class="vote-view">
    <div v-if="!auth.sessionReady" class="card empty-card">
      <p class="empty-title">正在恢复登录会话</p>
      <p class="empty-desc">稍等一下，我们正在读取你的身份状态。</p>
    </div>

    <div v-else-if="!auth.isAuthenticated" class="card empty-card">
      <p class="empty-title">请先登录学号身份</p>
      <p class="empty-desc">登录后才能查看你拥有哪些项目的投票权，并进入具体项目页面完成投票。</p>
      <router-link to="/auth" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <DashboardHero
        :total-count="dashboardItems.length"
        :todo-count="todoCount"
        :claimed-pending-count="claimedPendingCount"
        :voted-count="votedCount"
        :show-help="showHelp"
        :dashboard-loading="dashboardLoading"
        @toggle-help="showHelp = !showHelp"
        @refresh="refreshDashboard"
        @select-tab="activeTab = $event"
      />

      <div v-if="pageMessage.text" :class="['alert', pageMessage.type === 'success' ? 'alert-success' : 'alert-error']">
        {{ pageMessage.text }}
      </div>

      <section class="card">
        <div class="section-head">
          <div class="section-head-top">
            <h3>我的项目列表</h3>
            <DashboardSearchBar v-model="searchQuery" class="flex-search" />
          </div>
          <div class="section-head-bottom">
            <p class="section-desc">选中任意项目后会进入独立详情页查看信息并投票。</p>
          </div>
        </div>

        <p v-if="searchQuery" class="search-summary">当前关键字 “{{ searchQuery }}” 共匹配到 {{ filteredDashboardItems.length }} 个项目。</p>
        <div class="filter-toolbar">
          <div class="filter-group">
            <label class="filter-label">状态</label>
            <select v-model="statusFilter" class="filter-select">
              <option value="">全部状态</option>
              <option value="active">进行中</option>
              <option value="pending">待参与</option>
              <option value="completed">已完成</option>
              <option value="ended">已结束</option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">排序</label>
            <select v-model="sortBy" class="filter-select">
              <option value="latest">最新优先</option>
              <option value="deadline">按截止时间</option>
              <option value="status">按状态</option>
            </select>
          </div>

          <div class="filter-spacer"></div>

          <div class="view-toggle">
            <button
              type="button"
              class="view-btn"
              :class="{ active: viewMode === 'grid' }"
              title="卡片视图"
              @click="viewMode = 'grid'"
            >
              ⊞ 卡片
            </button>
            <button
              type="button"
              class="view-btn"
              :class="{ active: viewMode === 'list' }"
              title="列表视图"
              @click="viewMode = 'list'"
            >
              ≡ 列表
            </button>
          </div>
        </div>
        <div v-if="!filteredDashboardItems.length" class="empty-inline">
          {{ searchQuery ? "没有匹配的投票项目，请试试项目标题关键词或合约地址片段。" : "当前筛选条件下暂无项目。" }}
        </div>

        <div v-else class="election-grid">
          <ElectionSummaryCard
            v-for="item in paginatedItems"
            :key="item.election_address"
            :item="item"
            @select="openElectionDetail"
            @action="handleCardAction"
            @copy-address="copyAddress"
          />
        </div>

        <div v-if="totalPages > 1" class="pagination">
          <button 
            type="button"
            class="btn btn-secondary" 
            :disabled="currentPage === 1" 
            @click="currentPage--"
          >
            上一页
          </button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button 
            type="button"
            class="btn btn-secondary" 
            :disabled="currentPage === totalPages" 
            @click="currentPage++"
          >
            下一页
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import DashboardHero from "../components/dashboard/DashboardHero.vue";
import DashboardSearchBar from "../components/dashboard/DashboardSearchBar.vue";
import DashboardTabs from "../components/dashboard/DashboardTabs.vue";
import ElectionSummaryCard from "../components/dashboard/ElectionSummaryCard.vue";
import { useAuthStore } from "../stores/auth.js";
import { cardCta, isHistoryItem, isTodoItem, matchesDashboardSearch, sortDashboardItems } from "../utils/dashboard.js";

const auth = useAuthStore();
const router = useRouter();

const dashboardLoading = ref(false);
const activeTab = ref("all");
const showHelp = ref(false);
const searchQuery = ref("");
const currentPage = ref(1);
const itemsPerPage = 10;
const statusFilter = ref("");
const sortBy = ref("latest");
const viewMode = ref("grid");
const pageMessage = reactive({
  type: "success",
  text: "",
});

const dashboardItems = computed(() => auth.myElections);
const sortedDashboardItems = computed(() => sortDashboardItems(dashboardItems.value));
const searchedDashboardItems = computed(() =>
  sortedDashboardItems.value.filter((item) => matchesDashboardSearch(item, searchQuery.value))
);
const todoCount = computed(() => dashboardItems.value.filter(isTodoItem).length);
const claimedPendingCount = computed(
  () => dashboardItems.value.filter((item) => item.phase !== "ENDED" && item.status === "CLAIMED").length
);
const votedCount = computed(() => dashboardItems.value.filter((item) => item.phase === "ENDED" || item.status === "VOTED").length);

const tabs = computed(() => [
  { key: "todo", label: "待办事项", count: searchedDashboardItems.value.filter(isTodoItem).length },
  { key: "all", label: "全部项目", count: searchedDashboardItems.value.length },
  { key: "history", label: "已参与/历史", count: searchedDashboardItems.value.filter(isHistoryItem).length },
]);

function applyStatusFilter(items) {
  if (!statusFilter.value) return items;
  
  return items.filter((item) => {
    switch (statusFilter.value) {
      case "active":
        return item.phase === "ACTIVE";
      case "pending":
        return item.phase === "PENDING";
      case "completed":
        return item.status === "VOTED";
      case "ended":
        return item.phase === "ENDED";
      default:
        return true;
    }
  });
}

function applySortBy(items) {
  const sorted = [...items];
  
  switch (sortBy.value) {
    case "deadline":
      sorted.sort((a, b) => (a.end_time || 0) - (b.end_time || 0));
      break;
    case "status":
      const statusOrder = { ACTIVE: 0, PENDING: 1, ENDED: 2 };
      sorted.sort((a, b) => (statusOrder[a.phase] ?? 9) - (statusOrder[b.phase] ?? 9));
      break;
    case "latest":
    default:
      sorted.sort((a, b) => (b.start_time || 0) - (a.start_time || 0));
      break;
  }
  
  return sorted;
}

const filteredDashboardItems = computed(() => {
  let items = searchedDashboardItems.value;
  
  // 如果有状态筛选，优先使用状态筛选；否则使用标签筛选
  if (statusFilter.value) {
    // 状态筛选优先级较高
    items = applyStatusFilter(items);
  } else {
    // 应用标签筛选
    if (activeTab.value === "todo") {
      items = items.filter(isTodoItem);
    } else if (activeTab.value === "history") {
      items = items.filter(isHistoryItem);
    }
  }
  
  // 应用排序
  items = applySortBy(items);
  
  return items;
});

const totalPages = computed(() => Math.ceil(filteredDashboardItems.value.length / itemsPerPage) || 1);

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return filteredDashboardItems.value.slice(start, end);
});

watch([activeTab, searchQuery, statusFilter, sortBy], () => {
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
  console.log("openElectionDetail called with address:", address);
  if (!address) {
    console.error("openElectionDetail: Missing address");
    return;
  }
  console.log("Pushing to router for DashboardElection");
  router.push({ name: "DashboardElection", params: { electionAddress: address } });
}

function goToResults(address) {
  router.push({ name: "Results", query: { election: address } });
}

function handleCardAction(item) {
  console.log("Card action clicked", item);
  const cta = cardCta(item);
  if (cta.action === "results") {
    goToResults(item.election_address);
    return;
  }

  openElectionDetail(item.election_address);
}

async function refreshDashboard() {
  if (!auth.isAuthenticated) return;

  dashboardLoading.value = true;

  try {
    await auth.loadMyElections();
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
</script>

<style scoped>
.vote-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-card {
  text-align: center;
  padding: 64px 24px;
  background: white;
}

.empty-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px;
}

.empty-desc {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 auto 24px;
  max-width: 500px;
}

.section-head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 20px;
  margin-bottom: 24px;
}

.section-head-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.section-head-top h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
}

.flex-search {
  max-width: 320px;
  width: 100%;
}

.section-head-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.section-desc,
.search-summary,
.empty-inline,
.empty-desc {
  color: var(--text-secondary);
}

.section-desc {
  margin: 8px 0 0;
  font-size: 15px;
}

.search-summary {
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 16px;
  background: #f3f4f6;
  border-radius: 8px;
  border-left: 4px solid var(--primary);
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #ffffff;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(91, 33, 182, 0.1);
}

.filter-select:hover {
  border-color: var(--primary);
}

.filter-spacer {
  flex: 1;
}

.view-toggle {
  display: flex;
  gap: 4px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 8px;
}

.view-btn {
  padding: 8px 12px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn:hover {
  background: #f8fafc;
  color: var(--text-primary);
}

.view-btn.active {
  background: #ffffff;
  color: var(--primary);
  border-color: var(--border);
  font-weight: 600;
}

.empty-inline {
  padding: 48px 24px;
  text-align: center;
  background: #f9fafb;
  border-radius: var(--radius);
  border: 1px dashed var(--border);
  font-size: 15px;
}

.election-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

@media (max-width: 1200px) {
  .election-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .election-grid {
    grid-template-columns: 1fr;
  }

  .filter-toolbar {
    flex-wrap: wrap;
    gap: 12px;
  }

  .filter-spacer {
    flex: 1 100%;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.page-info {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
  min-width: 120px;
  text-align: center;
}

.btn-secondary {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-secondary:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
  border-color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fafc;
  border-color: var(--primary);
  color: var(--primary);
}

@media (max-width: 960px) {
  .section-tools {
    align-items: stretch;
    min-width: 100%;
  }
}
</style>
