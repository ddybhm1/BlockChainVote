<template>
  <div class="results-view">
    <div class="card">
      <div class="results-header">
        <h2>📊 实时投票结果</h2>
        <button class="btn btn-primary" @click="refresh" :disabled="voting.loading || !selectedElection" style="padding:6px 14px;font-size:13px">
          🔄 刷新
        </button>
      </div>
      <p class="desc">数据直接从以太坊区块链读取，任何人均可通过 Etherscan 独立验证。</p>
      <ElectionSelector v-model="selectedElection" />
    </div>

    <template v-if="selectedElection">
      <div class="card time-card" style="margin-bottom:16px;">
        <div><strong>投票开始时间：</strong>{{ voting.startTime ? new Date(voting.startTime * 1000).toLocaleString() : '未部署' }}</div>
        <div><strong>投票截止时间：</strong>{{ voting.endTime ? new Date(voting.endTime * 1000).toLocaleString() : '未部署' }}</div>
        <div class="time-status">
          <strong>投票状态：</strong>
          <span :class="['status-badge', statusClass]">{{ statusText }}</span>
        </div>
      </div>
      <div v-if="voting.loading" class="card" style="text-align:center;padding:40px">
        正在从区块链读取最新数据...
      </div>

      <template v-else>
        <!-- 统计概览 -->
        <div class="stats-row">
          <div class="stat card">
            <span class="stat-value">{{ voting.candidates.length }}</span>
            <span class="stat-label">候选人</span>
          </div>
          <div class="stat card">
            <span class="stat-value">{{ voting.totalVotes }}</span>
            <span class="stat-label">已投票数</span>
          </div>
          <div class="stat card">
            <span class="stat-value">{{ voting.totalVoters }}</span>
            <span class="stat-label">授权选民</span>
          </div>
          <div class="stat card">
            <span class="stat-value">{{ participationRate }}%</span>
            <span class="stat-label">投票率</span>
          </div>
        </div>

        <!-- 票数排行 -->
        <div class="card">
          <div class="results-card-header">
            <h3>排行榜</h3>
            <span class="badge badge-info">实时链内核验</span>
          </div>
          <div v-if="sortedCandidates.length === 0" style="text-align:center;padding:20px;color:var(--text-secondary)">
            暂无候选人数据
          </div>
          <div v-for="(c, i) in sortedCandidates" :key="i" class="rank-item">
            <div class="rank-pos">{{ i + 1 }}</div>
            <div class="rank-info">
              <div class="rank-name-row">
                <strong>{{ c.name }}</strong>
                <a 
                  v-if="c.cid" 
                  :href="`https://ipfs.io/ipfs/${c.cid}`" 
                  target="_blank" 
                  class="cid-verify-link"
                  title="在 IPFS 上验证候选人原始数据"
                >
                  验证 CID
                </a>
              </div>
              <span class="rank-votes">{{ c.votes }} 票</span>
            </div>
            <div class="rank-bar-wrap">
              <div
                class="rank-bar"
                :style="{ width: barWidth(c.votes) + '%' }"
              ></div>
            </div>
            <div class="rank-pct">{{ percentage(c.votes) }}%</div>
          </div>
        </div>

        <!-- 链上验证/审计 -->
        <div class="card auditor-card">
          <div class="auditor-header">
            <h3>🏢 公众/审计员 (Public Observer) —— Web3 监督角色</h3>
            <span class="auditor-badge">只读 & 数据全透明</span>
          </div>
          <div class="auditor-content">
            <p>基于区块链的选举允许任何人作为“隐形监督者”验证公平性：</p>
            <ul class="audit-list">
              <li><strong>免许可验证</strong>：直接调用智能合约的 <code>voteCount</code> 核对票数。</li>
              <li><strong>审计每一笔交易</strong>：核查链上 <code>Voted</code> 事件日志，核实每一张票。</li>
              <li><strong>候选人原始数据核查</strong>：提取 <code>candidateCIDs</code> 映射，去官方网关验证。</li>
            </ul>
            <div class="audit-actions">
              <a
                :href="`https://sepolia.etherscan.io/address/${selectedElection}`"
                target="_blank"
                class="btn btn-primary btn-sm"
              >
                在 Etherscan 上验证交易记录
              </a>
              <a
                :href="`https://sepolia.etherscan.io/address/${selectedElection}#readContract`"
                target="_blank"
                class="btn btn-secondary btn-sm"
              >
                直接读取合约数据
              </a>
            </div>
          </div>
        </div>
      </template>
    </template>

    <div v-else class="card" style="text-align:center;padding:40px">
      <p style="font-size:18px;margin-bottom:8px">请先选择投票项目</p>
      <p style="color:var(--text-secondary)">在上方下拉框中选择要查看结果的项目</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useVotingStore } from "../stores/voting.js";
import ElectionSelector from "../components/ElectionSelector.vue";

const voting = useVotingStore();
const selectedElection = ref("");

watch(selectedElection, async (addr) => {
  if (!addr) return;
  voting.selectElection(addr);
  await voting.loadCandidates();
});

const sortedCandidates = computed(() => {
  return [...voting.candidates].sort((a, b) => b.votes - a.votes);
});

const maxVotes = computed(() => {
  return Math.max(1, ...voting.candidates.map((c) => c.votes));
});

const participationRate = computed(() => {
  if (voting.totalVoters === 0) return "0.0";
  return ((voting.totalVotes / voting.totalVoters) * 100).toFixed(1);
});

const statusText = computed(() => {
  if (!voting.votingStarted) return "未开始";
  if (voting.votingEnded) return "已截止";
  return "进行中";
});

const statusClass = computed(() => {
  if (!voting.votingStarted) return "badge-warning";
  if (voting.votingEnded) return "badge-danger";
  return "badge-success";
});

function barWidth(votes) {
  return (votes / maxVotes.value) * 100;
}

function percentage(votes) {
  if (voting.totalVotes === 0) return "0.0";
  return ((votes / voting.totalVotes) * 100).toFixed(1);
}

async function refresh() {
  await voting.loadCandidates();
}
</script>

<style scoped>
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 8px;
}
.time-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.time-status {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  text-align: center;
  padding: 20px;
}
.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: var(--primary);
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.rank-item:last-child {
  border-bottom: none;
}
.rank-pos {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.rank-info {
  min-width: 120px;
  display: flex;
  flex-direction: column;
}
.rank-votes {
  font-size: 13px;
  color: var(--text-secondary);
}
.rank-bar-wrap {
  flex: 1;
  height: 10px;
  background: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
}
.rank-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #818cf8);
  border-radius: 5px;
  transition: width 0.5s ease;
}
.rank-pct {
  font-size: 14px;
  font-weight: 700;
  min-width: 50px;
  text-align: right;
}

/* 审计员卡片样式 */
.auditor-card {
  border-left: 4px solid var(--success);
  background: #fcfdfd;
}
.auditor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.auditor-badge {
  font-size: 11px;
  background: var(--success);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
}
.audit-list {
  padding-left: 18px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 12px 0;
}
.audit-actions {
  display: flex;
  gap: 10px;
}
.rank-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cid-verify-link {
  font-size: 10px;
  background: #f1f5f9;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 1px 6px;
  border-radius: 4px;
}
.cid-verify-link:hover {
  background: var(--primary);
  color: white;
}
.badge-info {
  background: #e0f2fe;
  color: #0369a1;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
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
.results-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

