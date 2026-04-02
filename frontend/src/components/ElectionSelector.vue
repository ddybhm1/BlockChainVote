<template>
  <div class="election-selector">
    <label class="selector-label">选择投票项目</label>
    <div v-if="loading" class="selector-loading">加载中...</div>
    <div v-else-if="!elections.length" class="selector-empty">暂无可用投票项目</div>
    <div v-else class="selector-search-wrapper">
      <div class="search-input-container">
        <input
          v-model="searchQuery"
          type="text"
          class="selector-search"
          placeholder="搜索项目名称或合约地址"
        />
        <span v-if="searchQuery" class="search-clear" @click="searchQuery = ''">✕</span>
      </div>
      
      <div v-if="filteredElections.length === 0 && searchQuery" class="search-empty">
        未找到匹配的项目
      </div>
      
      <div v-else-if="filteredElections.length > 0" class="search-results">
        <div
          v-for="el in filteredElections"
          :key="el.address"
          class="search-result-item"
          :class="{ active: el.address === modelValue }"
          @click="selectElection(el.address)"
        >
          <div class="result-title">{{ el.title }}</div>
          <div class="result-address">{{ el.address }}</div>
        </div>
      </div>

      <div v-if="!searchQuery && selectedElectionTitle" class="selected-display">
        已选择：<strong>{{ selectedElectionTitle }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useVotingStore } from "../stores/voting.js";

const props = defineProps({
  modelValue: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);

const voting = useVotingStore();
const elections = ref([]);
const loading = ref(true);
const searchQuery = ref("");

const filteredElections = computed(() => {
  if (!searchQuery.value.trim()) {
    return elections.value;
  }

  const query = searchQuery.value.toLowerCase();
  return elections.value.filter(
    (el) =>
      el.title.toLowerCase().includes(query) ||
      el.address.toLowerCase().includes(query)
  );
});

const selectedElectionTitle = computed(() => {
  const selected = elections.value.find((el) => el.address === props.modelValue);
  return selected ? selected.title : "";
});

function selectElection(address) {
  emit("update:modelValue", address);
  searchQuery.value = "";
}

onMounted(async () => {
  await voting.loadElections();
  elections.value = voting.elections;
  loading.value = false;
});
</script>

<style scoped>
.election-selector {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 8px;
}

.selector-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #888);
  margin-bottom: 6px;
}

.selector-search-wrapper {
  position: relative;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.selector-search {
  width: 100%;
  padding: 10px 12px;
  padding-right: 32px;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 6px;
  font-size: 14px;
  background: white;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.selector-search:focus {
  outline: none;
  border-color: var(--primary, #5b21b6);
  box-shadow: 0 0 0 3px rgba(91, 33, 182, 0.1);
}

.search-clear {
  position: absolute;
  right: 12px;
  cursor: pointer;
  color: var(--text-secondary, #888);
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.search-clear:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-primary, #333);
}

.search-results {
  margin-top: 8px;
  max-height: 300px;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 6px;
  background: white;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-result-item {
  padding: 12px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border, #e5e5e5);
  transition: background-color 0.2s ease;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: #f5f5f5;
}

.search-result-item.active {
  background-color: rgba(91, 33, 182, 0.1);
  border-left: 3px solid var(--primary, #5b21b6);
  padding-left: 9px;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #333);
  margin-bottom: 4px;
}

.result-address {
  font-size: 12px;
  color: var(--text-secondary, #888);
  font-family: monospace;
}

.search-empty {
  padding: 16px 12px;
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary, #888);
  background: white;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 6px;
  margin-top: 8px;
}

.selected-display {
  margin-top: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-secondary, #888);
  background: white;
  border-radius: 4px;
  border: 1px solid var(--border, #e5e5e5);
}

.selector-loading,
.selector-empty {
  font-size: 14px;
  color: var(--text-secondary, #888);
}

/* 滚动条样式 */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
