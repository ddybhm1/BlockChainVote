<template>
  <div class="election-selector">
    <label class="selector-label">选择投票项目</label>
    <div v-if="loading" class="selector-loading">加载中...</div>
    <div v-else-if="!elections.length" class="selector-empty">暂无可用投票项目</div>
    <select v-else class="selector-select" :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
      <option value="" disabled>-- 请选择投票项目 --</option>
      <option v-for="el in elections" :key="el.address" :value="el.address">
        {{ el.title }}（{{ el.address.slice(0, 8) }}...）
      </option>
    </select>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useVotingStore } from "../stores/voting.js";

defineProps({
  modelValue: { type: String, default: "" },
});
defineEmits(["update:modelValue"]);

const voting = useVotingStore();
const elections = ref([]);
const loading = ref(true);

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
.selector-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 6px;
  font-size: 14px;
  background: white;
}
.selector-loading, .selector-empty {
  font-size: 14px;
  color: var(--text-secondary, #888);
}
</style>
