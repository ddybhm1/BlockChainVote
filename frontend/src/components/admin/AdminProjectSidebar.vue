<template>
  <div>
    <div class="section">
      <h3>创建新投票项目</h3>
      <div class="create-row">
        <input
          class="input-field"
          :value="title"
          placeholder="请输入投票项目名称"
          style="flex: 1"
          @input="$emit('update:title', $event.target.value)"
        />
        <button class="btn btn-primary" :disabled="creating || !title.trim()" type="button" @click="$emit('create')">
          {{ creating ? "创建中...(等待链上确认)" : "创建项目" }}
        </button>
      </div>
    </div>

    <div class="section">
      <h3>我的投票项目</h3>
      <div v-if="!elections.length" class="alert alert-info">
        暂无投票项目。请先创建一个新项目。
      </div>
      <div v-else class="election-list">
        <div
          v-for="election in elections"
          :key="election.address"
          :class="['election-item', { active: selectedAddr === election.address }]"
          @click="$emit('select', election.address)"
        >
          <div class="el-title">{{ election.title }}</div>
          <div class="el-meta">
            <span class="el-addr" :title="election.address">
              {{ election.address.slice(0, 10) }}...{{ election.address.slice(-6) }}
            </span>
            <span class="el-time">{{ formatAdminTime(election.createdAt) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatAdminTime } from "../../utils/admin.js";

defineProps({
  title: { type: String, default: "" },
  creating: { type: Boolean, default: false },
  elections: { type: Array, default: () => [] },
  selectedAddr: { type: String, default: "" },
});

defineEmits(["update:title", "create", "select"]);
</script>

<style scoped>
.section {
  margin-top: 24px;
}

.section h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.create-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.election-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.election-item {
  padding: 12px 16px;
  border: 2px solid var(--border, #e5e5e5);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.election-item:hover {
  border-color: var(--primary, #4f46e5);
  background: #f8f7ff;
}

.election-item.active {
  border-color: var(--primary, #4f46e5);
  background: #eef2ff;
}

.el-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}

.el-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary, #888);
}

.el-addr {
  font-family: monospace;
}

@media (max-width: 700px) {
  .create-row {
    flex-direction: column;
    align-items: stretch;
  }

  .el-meta {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
