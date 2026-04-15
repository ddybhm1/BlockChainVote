<template>
  <div class="section">
    <h3>候选人批量管理</h3>

    <template v-if="statusStarted">
      <div class="alert alert-info">
        投票已开始，无法添加候选人。如需重新配置，请创建新项目。
      </div>
    </template>

    <template v-else>
      <div v-if="uploadMessage" :class="['alert', uploadMessageOk ? 'alert-success' : 'alert-error']">
        {{ uploadMessage }}
      </div>

      <div class="batch-list">
        <div v-for="(item, index) in batchItems" :key="index" class="batch-row">
          <input
            v-model="item.name"
            class="input-field"
            placeholder="候选人名称"
          />

          <div class="cid-input-group">
            <input
              v-model="item.cid"
              class="input-field"
              :placeholder="item.uploadingImg ? '上传中...' : '头像 CID'"
              :disabled="item.uploadingImg"
            />

            <label class="btn-icon btn-upload" :title="item.uploadingImg ? '上传中...' : '上传头像到 IPFS'">
              <span v-if="item.uploadingImg" class="spinner"></span>
              <span v-else>🖼️</span>
              <input
                type="file"
                class="file-hidden"
                accept="image/*"
                :disabled="item.uploadingImg"
                @change="handleFileUpload($event, index, 'image')"
              />
            </label>
          </div>

          <div class="cid-input-group">
            <input
              v-model="item.manifestoCid"
              class="input-field"
              :placeholder="item.uploadingDoc ? '上传中...' : '宣言 CID'"
              :disabled="item.uploadingDoc"
            />

            <label class="btn-icon btn-upload" :title="item.uploadingDoc ? '上传中...' : '上传 PDF 宣言到 IPFS'">
              <span v-if="item.uploadingDoc" class="spinner"></span>
              <span v-else>📄</span>
              <input
                type="file"
                class="file-hidden"
                accept="application/pdf,.pdf"
                :disabled="item.uploadingDoc"
                @change="handleFileUpload($event, index, 'document')"
              />
            </label>
          </div>

          <button
            type="button"
            class="btn-icon btn-remove"
            :disabled="batchItems.length <= 1"
            title="删除"
            @click="removeItem(index)"
          >
            ✕
          </button>
        </div>
      </div>

      <div class="batch-actions">
        <button type="button" class="btn btn-secondary" @click="addItem">
          + 新增一行
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="submitting || !hasValidItems"
          @click="$emit('submit', validItems)"
        >
          {{ submitting ? "提交中...(等待链上确认)" : `提交 ${validCount} 个候选人` }}
        </button>
      </div>
    </template>

    <div v-if="candidates.length" class="table-block">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h3 style="margin: 0;">已添加的候选人</h3>
        <input
          v-model="searchQuery"
          class="input-field"
          style="width: 250px; padding: 6px 12px; margin: 0;"
          placeholder="搜索候选人名称或 CID..."
        />
      </div>
      <table class="candidate-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>头像 CID</th>
            <th>宣言 CID</th>
            <th>得票</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredCandidates.length === 0">
            <td colspan="5" style="text-align: center; color: #999; padding: 20px;">未找到匹配的候选人</td>
          </tr>
          <tr v-for="(candidate, index) in filteredCandidates" :key="index">
            <td>{{ index }}</td>
            <td>{{ candidate.name }}</td>
            <td class="cid-cell">{{ candidate.cid }}</td>
            <td class="cid-cell">{{ candidate.manifestoCid }}</td>
            <td>{{ candidate.votes }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef } from "vue";
import { useAdminCandidateBatch } from "../../composables/useAdminCandidateBatch.js";

const props = defineProps({
  statusStarted: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  candidates: { type: Array, default: () => [] },
  resetKey: { type: Number, default: 0 },
});

defineEmits(["submit"]);

const searchQuery = ref("");

const filteredCandidates = computed(() => {
  if (!searchQuery.value.trim()) return props.candidates;
  const q = searchQuery.value.toLowerCase();
  return props.candidates.filter(c => 
    c.name.toLowerCase().includes(q) || 
    c.cid.toLowerCase().includes(q) ||
    c.manifestoCid.toLowerCase().includes(q)
  );
});

const {
  batchItems,
  uploadMessage,
  uploadMessageOk,
  validItems,
  validCount,
  hasValidItems,
  addItem,
  removeItem,
  handleFileUpload,
} = useAdminCandidateBatch(toRef(props, "resetKey"));
</script>

<style scoped>
.section,
.table-block {
  margin-top: 24px;
}

.section h3,
.table-block h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.batch-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.batch-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-row .input-field {
  flex: 1;
}

.cid-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.cid-input-group .input-field {
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

.btn-upload {
  background: #e8f4fd;
  color: #0d6efd;
  transition: background 0.15s;
}

.btn-upload:hover {
  background: #cce5ff;
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

.file-hidden {
  display: none;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #ccc;
  border-top-color: #0d6efd;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.candidate-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.candidate-table th,
.candidate-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border, #e5e5e5);
  text-align: left;
}

.candidate-table th {
  font-weight: 600;
  background: var(--bg-secondary, #f5f5f5);
}

.cid-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .batch-row,
  .batch-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
