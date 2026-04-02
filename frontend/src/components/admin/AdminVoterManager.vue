<template>
  <div class="section voter-management">
    <div class="section-header-row">
      <h3>投票人员管理</h3>
      <div class="header-actions">
        <label class="btn btn-excel" :class="{ 'btn-loading': submitting }" title="支持 .xlsx 格式，需包含“学号”和“初始密码”列">
          <span v-if="submitting" class="spinner-small"></span>
          <span v-else>📥</span>
          Excel 一键导入
          <input type="file" class="file-hidden" accept=".xlsx, .xls" :disabled="submitting" @change="handleExcelInput" />
        </label>
      </div>
    </div>

    <div v-if="voterStats.total >= 0" class="voter-stats">
      已注册：<strong>{{ voterStats.total }}</strong> 人 |
      已领票（本项目）：<strong>{{ voterStats.claimed }}</strong> 人
    </div>

    <div class="batch-list">
      <div class="batch-header">
        <span class="header-label">学号</span>
        <span class="header-label">密码</span>
        <span class="spacer"></span>
      </div>

      <div v-for="(item, index) in voterItems" :key="index" class="batch-row">
        <input
          v-model="item.studentId"
          class="input-field"
          placeholder="学号"
        />
        <input
          v-model="item.password"
          class="input-field"
          placeholder="密码"
        />
        <button
          type="button"
          class="btn-icon btn-remove"
          :disabled="voterItems.length <= 1"
          title="删除"
          @click="removeVoter(index)"
        >
          ✕
        </button>
      </div>
    </div>

    <div class="batch-actions">
      <button type="button" class="btn btn-secondary" @click="addVoter">
        + 新增一行
      </button>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="submitting || !hasValidVoters"
        @click="$emit('submit', validVoters)"
      >
        {{ submitting ? "注册中..." : `注册 ${validVoterCount} 个选民` }}
      </button>
    </div>

    <div v-if="message" :class="['feedback', 'alert', messageOk ? 'alert-success' : 'alert-error']">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { toRef } from "vue";
import { useAdminVoterBatch } from "../../composables/useAdminVoterBatch.js";

const props = defineProps({
  submitting: { type: Boolean, default: false },
  message: { type: String, default: "" },
  messageOk: { type: Boolean, default: false },
  voterStats: { type: Object, default: () => ({ total: -1, claimed: 0 }) },
  resetKey: { type: Number, default: 0 },
});

const emit = defineEmits(["submit", "import-excel"]);

const {
  voterItems,
  validVoters,
  validVoterCount,
  hasValidVoters,
  addVoter,
  removeVoter,
} = useAdminVoterBatch(toRef(props, "resetKey"));

function handleExcelInput(event) {
  const file = event.target.files?.[0];
  if (file) {
    emit("import-excel", file);
  }
  event.target.value = "";
}
</script>

<style scoped>
.section {
  margin-top: 24px;
}

.section h3 {
  margin: 0;
  font-size: 16px;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: rgba(0, 0, 0, 0.02);
  padding: 10px 14px;
  border-radius: 8px;
  border-left: 4px solid var(--primary);
}

.btn-excel {
  background-color: #217346;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(33, 115, 70, 0.2);
}

.btn-excel:hover {
  background-color: #1a5c38;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(33, 115, 70, 0.3);
}

.btn-excel.btn-loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.voter-stats {
  padding: 10px 14px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 14px;
}

.batch-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.batch-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border, #e5e5e5);
  margin-bottom: 6px;
}

.header-label {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #888);
}

.spacer {
  width: 32px;
}

.batch-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-row .input-field {
  flex: 1;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-remove {
  background: #f8d7da;
  color: #721c24;
}

.btn-remove:hover {
  background: #f5c6cb;
}

.btn-remove:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.batch-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-secondary {
  padding: 10px 20px;
  border: 1px dashed var(--border, #ccc);
  border-radius: 8px;
  background: transparent;
  font-size: 14px;
  cursor: pointer;
  color: var(--text-secondary, #666);
}

.btn-secondary:hover {
  background: var(--bg-secondary, #f5f5f5);
}

.feedback {
  margin-top: 12px;
}

.file-hidden {
  display: none;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .section-header-row,
  .batch-row,
  .batch-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .spacer {
    display: none;
  }
}
</style>
