<template>
  <article :class="['election-card', { active: selected }]" @click="$emit('select', item.election_address)">
    <div class="card-header">
      <div class="title-section">
        <h3 class="card-title">{{ displayTitle(item.title) }}</h3>
        <span :class="['status-badge', badgeInfo.class]">{{ badgeInfo.label }}</span>
      </div>
      <div class="copy-btn-wrapper">
        <button
          type="button"
          class="copy-icon-btn"
          title="点击复制合约地址"
          @click.stop="$emit('copy-address', item.election_address)"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
    </div>

    <div class="card-info-row">
      <div class="info-item">
        <span class="info-icon">🏛️</span>
        <span class="info-label">来源</span>
        <span class="info-value">{{ getOrganization(item) }}</span>
      </div>
      <div class="info-item">
        <span class="info-icon">📅</span>
        <span class="info-label">截止时间</span>
        <span class="info-value">{{ formatTime(item.end_time) }}</span>
      </div>
    </div>

    <div class="card-info-row">
      <div class="info-item">
        <span class="info-icon">⏱️</span>
        <span class="info-label">剩余时间</span>
        <span class="info-value">{{ getTimeRemaining(item) }}</span>
      </div>
      <div class="info-item">
        <span class="info-icon">👥</span>
        <span class="info-label">参与状态</span>
        <span class="info-value">{{ getParticipationStatus(item) }}</span>
      </div>
    </div>

    <div class="card-footer">
      <button
        :class="['card-cta', 'btn', cta.className]"
        :disabled="cta.disabled"
        type="button"
        @click.stop="$emit('action', item)"
      >
        {{ cta.label }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import {
  cardCta,
  displayTitle,
  formatRangeCompact,
  shortAddress,
  unifiedBadge,
} from "../../utils/dashboard.js";

const props = defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
});

defineEmits(["select", "action", "copy-address"]);

const cta = computed(() => cardCta(props.item));
const badgeInfo = computed(() => unifiedBadge(props.item));

// 获取组织名称
function getOrganization(item) {
  if (!item.creator) return "未知组织";
  if (item.creator.includes("committee") || item.creator.includes("委员会")) return "班级委员会";
  if (item.creator.includes("union") || item.creator.includes("学生会")) return "学生会";
  if (item.creator.includes("college") || item.creator.includes("学院")) return "学院团委";
  return "学生组织";
}

// 格式化时间显示
function formatTime(timestamp) {
  if (!timestamp) return "-";
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

// 获取剩余时间
function getTimeRemaining(item) {
  if (!item.end_time) return "无法获取";
  const now = Math.floor(Date.now() / 1000);
  const remaining = item.end_time - now;
  
  if (remaining <= 0) return "已结束";
  if (remaining < 3600) return `剩余 ${Math.floor(remaining / 60)} 分钟`;
  if (remaining < 86400) return `剩余 ${Math.floor(remaining / 3600)} 小时`;
  return `剩余 ${Math.floor(remaining / 86400)} 天`;
}

// 获取参与状态
function getParticipationStatus(item) {
  if (item.status === "VOTED") return "已投票";
  if (item.status === "CLAIMED") return "已领票";
  if (item.phase === "ENDED") return "已结束";
  return "未参与";
}
</script>

<style scoped>
.election-card {
  padding: 20px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.election-card:hover,
.election-card.active {
  transform: translateY(-4px);
  border-color: var(--primary);
  box-shadow: 0 12px 24px rgba(91, 33, 182, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  line-height: 1.4;
  word-break: break-word;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-phase-active {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #86efac;
}

.badge-phase-pending {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde047;
}

.badge-phase-ended {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.badge-ticket-available {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fca5a5;
}

.badge-ticket-claimed {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #93c5fd;
}

.badge-ticket-voted {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #86efac;
}

.copy-btn-wrapper {
  flex-shrink: 0;
}

.copy-icon-btn {
  background: transparent;
  border: none;
  padding: 4px 8px;
  cursor: pointer;
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.copy-icon-btn:hover {
  background: #f3f4f6;
  color: var(--primary);
}

.card-info-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  min-width: 0;
}

.info-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.info-label {
  color: var(--text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.info-value {
  color: #111827;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.card-cta {
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-cta:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.cta-claim {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
}

.cta-vote {
  background: linear-gradient(135deg, #0f172a, #1e3a8a);
  color: #ffffff;
}

.cta-result {
  background: #f8fafc;
  color: #334155;
  border: 1px solid var(--border);
}

.cta-disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .election-card {
    padding: 16px;
    gap: 12px;
  }

  .card-title {
    font-size: 15px;
  }

  .card-info-row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 10px;
  }
}
</style>
