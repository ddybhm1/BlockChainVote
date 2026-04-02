<template>
  <section class="dashboard-hero">
    <div class="hero-left">
      <div class="welcome-header">
        <h2 class="welcome-title">欢迎回来</h2>
        <p class="welcome-subtitle">请在截止前完成待投票项目，已完成项目可查看结果与链上记录。</p>
      </div>
      
      <div class="hero-actions">
        <button class="btn btn-help" type="button" @click="$emit('toggle-help')">
          <span v-if="!showHelp">ℹ 使用说明</span>
          <span v-else>✓ 已展开</span>
        </button>
        <button class="btn btn-refresh" type="button" :disabled="dashboardLoading" @click="$emit('refresh')">
          {{ dashboardLoading ? "刷新中..." : "⟳ 刷新状态" }}
        </button>
      </div>

      <div v-if="showHelp" class="help-panel">
        <p>系统先用学号会话确认身份，再由 MySQL 记录领票/投票状态，最后利用零知识和隔离钱包保护链上匿名。</p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card clickable" @click="$emit('select-tab', 'todo')">
        <div class="stat-label">待投项目</div>
        <div class="stat-value highlight-orange">{{ todoCount }}</div>
      </div>
      <div class="stat-card clickable" @click="$emit('select-tab', 'history')">
        <div class="stat-label">已完成</div>
        <div class="stat-value highlight-blue">{{ votedCount }}</div>
      </div>
      <div class="stat-card clickable" @click="$emit('select-tab', 'all')">
        <div class="stat-label">全部项目</div>
        <div class="stat-value">{{ totalCount }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  totalCount: { type: Number, default: 0 },
  todoCount: { type: Number, default: 0 },
  claimedPendingCount: { type: Number, default: 0 },
  votedCount: { type: Number, default: 0 },
  showHelp: { type: Boolean, default: false },
  dashboardLoading: { type: Boolean, default: false },
});

defineEmits(["toggle-help", "refresh", "select-tab"]);
</script>

<style scoped>
.dashboard-hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  padding: 32px;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid var(--border);
  align-items: start;
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.welcome-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1.25;
}

.welcome-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 16px;
  border: 1px solid var(--border);
  background: #f8fafc;
  color: var(--text-primary);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: var(--primary);
  color: var(--primary);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-help,
.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.help-panel {
  margin-top: 8px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(15, 118, 110, 0.15);
  background: #f0fdfa;
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
}

.help-panel p {
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  background: linear-gradient(135deg, #f8fafc, #f5f7fb);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
  box-shadow: 0 8px 16px rgba(91, 33, 182, 0.08);
}

.stat-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.highlight-orange {
  color: #f97316;
}

.highlight-blue {
  color: #2563eb;
}

@media (max-width: 960px) {
  .dashboard-hero {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .dashboard-hero {
    padding: 24px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 16px 12px;
  }
}
</style>
