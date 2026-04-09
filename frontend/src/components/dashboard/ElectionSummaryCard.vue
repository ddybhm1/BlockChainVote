<template>
  <el-card 
    class="election-card"
    shadow="hover"
    @click="$emit('select', item.election_address)"
  >
    <!-- Header -->
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <h3 class="card-title" :title="item.title">{{ displayTitle(item.title) }}</h3>
          <el-tag :type="badgeInfo.type" effect="light" size="small" style="margin-left: 8px;">
            {{ badgeInfo.label }}
          </el-tag>
        </div>
        <el-button
          link
          size="small"
          icon="DocumentCopy"
          @click.stop="$emit('copy-address', item.election_address)"
          title="复制合约地址"
        />
      </div>
    </template>

    <!-- Content & Actions -->
    <template #default>
      <div class="card-content">
        <!-- Project Info -->
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">🔗 合约地址</span>
            <span class="info-value">{{ shortAddress(item.election_address) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">📅 截止时间</span>
            <span class="info-value">{{ formatTime(item.end_time) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">⏱️ 剩余时间</span>
            <span class="info-value" :class="getTimeClass(item)">{{ getTimeRemaining(item) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">📊 参与状态</span>
            <span class="info-value">{{ getParticipationStatus(item) }}</span>
          </div>
        </div>

        <!-- Progress/Stats -->
        <div class="card-stats">
          <div class="stat-row" v-if="item.phase === 'ENDED' || item.status === 'VOTED'">
            <span class="stat-label">你的选择:</span>
            <el-tag type="success" size="small">✓ 已投票</el-tag>
          </div>
          <div class="stat-row" v-else-if="item.status === 'CLAIMED'">
            <span class="stat-label">当前状态:</span>
            <el-tag type="warning" size="small">⏳ 已领票待投</el-tag>
          </div>
          <div class="stat-row" v-else>
            <span class="stat-label">状态:</span>
            <el-tag type="info" size="small">📌 未领票</el-tag>
          </div>
        </div>

        <!-- Actions -->
        <el-button
          :type="cta.className === 'btn-primary' ? 'primary' : 'default'"
          :disabled="cta.disabled"
          class="action-btn"
          @click.stop="$emit('action', item)"
        >
          {{ cta.label }} →
        </el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { computed } from "vue";
import {
  cardCta,
  displayTitle,
  unifiedBadge,
} from "../../utils/dashboard.js";

const props = defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
});

defineEmits(["select", "action", "copy-address"]);

const cta = computed(() => cardCta(props.item));
const badgeInfo = computed(() => unifiedBadge(props.item));

function shortAddress(address) {
  if (!address) return "-";
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}

function formatTime(timestamp) {
  if (!timestamp) return "-";
  const date = new Date(timestamp * 1000);
  const now = new Date();
  const diff = date - now;
  
  if (diff < 0) {
    return "已结束";
  }
  
  return date.toLocaleDateString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function getTimeRemaining(item) {
  if (!item.end_time) return "-";
  
  const now = new Date();
  const endTime = new Date(item.end_time * 1000);
  const diff = endTime - now;
  
  if (diff <= 0) {
    return "已结束";
  }
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  
  if (days > 0) {
    return `${days}天${hours}小时`;
  } else if (hours > 0) {
    return `${hours}小时`;
  } else {
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${minutes}分钟`;
  }
}

function getTimeClass(item) {
  if (!item.end_time) return "";
  
  const now = new Date();
  const endTime = new Date(item.end_time * 1000);
  const diff = endTime - now;
  
  if (diff <= 0) return "time-ended";
  if (diff < 24 * 60 * 60 * 1000) return "time-urgent";
  return "time-normal";
}

function getParticipationStatus(item) {
  if (item.phase === "ENDED" || item.status === "VOTED") {
    return "✓ 已参与";
  } else if (item.status === "CLAIMED") {
    return "⏳ 已领票待投";
  } else {
    return "📌 未参与";
  }
}
</script>

<style scoped>
.election-card {
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.election-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.header-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #999;
  font-weight: 600;
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  word-break: break-word;
}

.time-urgent {
  color: #f56c6c;
  font-weight: 700;
}

.time-normal {
  color: #67c23a;
}

.time-ended {
  color: #999;
}

.card-stats {
  padding: 12px;
  background: #f5f9ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.stat-label {
  color: #666;
  font-weight: 500;
  min-width: 60px;
}

.action-btn {
  width: 100%;
  margin-top: auto;
  height: 36px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.2s ease;
}

:deep(.el-card__footer) {
  padding: 12px 20px;
  background: transparent;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 640px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .card-title {
    font-size: 14px;
  }
}
</style>
