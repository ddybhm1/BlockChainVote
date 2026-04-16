<template>
  <div>
    <div class="section" style="border: 1px solid #EBEEF5; padding: 20px; border-radius: 8px; background-color: #fff;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h3 style="margin: 0; padding: 0;">工厂项目列表</h3>
      </div>
      <div v-if="!elections.length" class="alert alert-info">
        当前工厂合约下暂无子项目。请先创建一个新项目。
      </div>
      <div v-else-if="!filteredElections.length" class="alert alert-warning">
        没有找到包含 "{{ searchQuery }}" 的项目。
      </div>
      <div v-else class="election-list" style="display: flex; flex-direction: column; gap: 12px;">
        <div
          v-for="election in filteredElections"
          :key="election.address"
          :class="['election-item', { active: selectedAddr === election.address }]"
          @click="$emit('select', election.address)"
          style="padding: 16px; border: 1px solid #E4E7ED; border-radius: 8px; cursor: pointer; transition: all 0.2s;"
        >
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div class="el-title" style="font-size: 16px; font-weight: bold; color: #303133;">{{ election.title }}</div>
            <el-tag :type="getElectionType(election.status)" size="small">
              {{ getElectionStatusText(election.status) }}
            </el-tag>
          </div>
          <div class="el-meta" style="display: flex; justify-content: space-between; align-items: flex-end; color: #909399; font-size: 13px;">
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <span class="el-addr" :title="election.address" style="font-family: monospace;">
                {{ election.address.slice(0, 10) }}...{{ election.address.slice(-6) }}
              </span>
              <span class="el-time" style="font-size: 12px;">
                开票时间: {{ election.startTime ? formatAdminTime(election.startTime) : '未设置' }} &nbsp;|&nbsp; 截止时间: {{ election.endTime ? formatAdminTime(election.endTime) : '未设置' }}
              </span>
            </div>
            <span class="el-time" style="font-size: 12px;">创建于: {{ formatAdminTime(election.createdAt) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { formatAdminTime } from "../../utils/admin.js";

const props = defineProps({
  elections: { type: Array, default: () => [] },
  selectedAddr: { type: String, default: "" },
  projectStatuses: { type: Object, default: () => ({}) },
  projectTimes: { type: Object, default: () => ({}) },
  searchQuery: { type: String, default: "" }
});

const emit = defineEmits(["select"]);

const filteredElections = computed(() => {
  let list = props.elections;
  if (props.searchQuery.trim()) {
    const q = props.searchQuery.toLowerCase();
    list = list.filter(e => 
      e.title.toLowerCase().includes(q) || 
      e.address.toLowerCase().includes(q)
    );
  }
  // 注入状态
  return list.map(e => ({
    ...e,
    status: props.projectStatuses[e.address] || 'loading',
    startTime: props.projectTimes[e.address]?.start || 0,
    endTime: props.projectTimes[e.address]?.end || 0
  }));
});

function handleCreateClick() {
  emit('create');
}

function getElectionStatusText(status) {
  if (status === 'not_started') return '待部署 / 未开始';
  if (status === 'in_progress') return '进行中';
  if (status === 'ended') return '已结束';
  return '加载中...';
}

function getElectionType(status) {
  if (status === 'not_started') return 'info';
  if (status === 'in_progress') return 'success';
  if (status === 'ended') return 'danger';
  return 'info';
}
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
