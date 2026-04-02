<template>
  <div>
    <div class="section">
      <h3>创建新投票项目</h3>
      <div class="create-row" style="flex-direction: column; align-items: stretch;">
        <input
          class="input-field"
          :value="title"
          placeholder="请输入投票项目名称"
          @input="$emit('update:title', $event.target.value)"
        />
        <div style="display: flex; align-items: center; gap: 12px;">
          <input
            class="input-field"
            style="flex: 1;"
            :value="sbtImageCid"
            placeholder="SBT 徽章图片 CID (上传自动填入)"
            @input="$emit('update:sbtImageCid', $event.target.value)"
          />
          <label class="btn btn-secondary" :class="{ disabled: uploading }" style="margin: 0; cursor: pointer; white-space: nowrap;">
            {{ uploading ? '上传中...' : '上传图片到 IPFS' }}
            <input type="file" accept="image/*" style="display: none" @change="handleFileChange" :disabled="uploading" />
          </label>
        </div>
        <button class="btn btn-primary" :disabled="creating || !title.trim() || !sbtImageCid.trim()" type="button" @click="$emit('create')">
          {{ creating ? "创建中...(等待链上确认)" : "创建项目" }}
        </button>
        <div v-if="uploadError" class="alert alert-error" style="margin-top: 8px; padding: 6px 12px; font-size: 14px;">
          {{ uploadError }}
        </div>
      </div>
    </div>

    <div class="section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h3 style="margin: 0;">我的投票项目</h3>
        <input 
          class="input-field" 
          v-model="searchQuery" 
          placeholder="搜索项目名称..." 
          style="width: 140px; padding: 4px 8px; font-size: 13px;"
        />
      </div>
      <div v-if="!elections.length" class="alert alert-info">
        暂无投票项目。请先创建一个新项目。
      </div>
      <div v-else-if="!filteredElections.length" class="alert alert-warning">
        没有找到包含 "{{ searchQuery }}" 的项目。
      </div>
      <div v-else class="election-list">
        <div
          v-for="election in filteredElections"
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
import { ref, computed } from "vue";
import { formatAdminTime } from "../../utils/admin.js";
import { uploadToIPFS } from "../../services/api.js";

const props = defineProps({
  title: { type: String, default: "" },
  sbtImageCid: { type: String, default: "" },
  creating: { type: Boolean, default: false },
  elections: { type: Array, default: () => [] },
  selectedAddr: { type: String, default: "" },
});

const emit = defineEmits(["update:title", "update:sbtImageCid", "create", "select"]);

const uploading = ref(false);
const uploadError = ref("");
const searchQuery = ref("");

const filteredElections = computed(() => {
  if (!searchQuery.value.trim()) return props.elections;
  const q = searchQuery.value.toLowerCase();
  return props.elections.filter(e => 
    e.title.toLowerCase().includes(q) || 
    e.address.toLowerCase().includes(q)
  );
});

async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  uploading.value = true;
  uploadError.value = "";
  try {
    const result = await uploadToIPFS(file);
    emit('update:sbtImageCid', result.cid);
  } catch (e) {
    uploadError.value = "图片上传失败：" + (e.response?.data?.detail || e.message);
  } finally {
    uploading.value = false;
    event.target.value = ""; // reset file input
  }
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
