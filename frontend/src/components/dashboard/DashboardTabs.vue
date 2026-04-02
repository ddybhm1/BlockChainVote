<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab-btn', { active: activeTab === tab.key }]"
      type="button"
      @click="$emit('update:activeTab', tab.key)"
    >
      {{ tab.label }} <span class="tab-count">({{ tab.count }})</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, default: () => [] },
  activeTab: { type: String, default: "todo" },
});

defineEmits(["update:activeTab"]);
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tab-btn {
  border: 1px solid var(--border);
  background: #ffffff;
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-count {
  font-weight: 500;
  opacity: 0.6;
}

.tab-btn.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}
</style>
