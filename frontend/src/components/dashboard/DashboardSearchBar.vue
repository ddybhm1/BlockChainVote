<template>
  <label class="search-shell">
    <span class="search-icon">⌕</span>
    <input
      :value="modelValue"
      class="search-input"
      type="search"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "搜索项目标题或合约地址" },
});

defineEmits(["update:modelValue"]);
</script>

<style scoped>
.search-shell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: min(100%, 320px);
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.search-icon {
  color: #64748b;
  font-size: 15px;
}

.search-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 13px 0;
  font-size: 14px;
  color: #0f172a;
  outline: none;
}

.search-input::placeholder {
  color: #94a3b8;
}
</style>
