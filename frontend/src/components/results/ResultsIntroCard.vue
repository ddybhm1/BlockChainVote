<template>
  <section class="card intro-card">
    <div class="intro-head">
      <div>
        <p class="intro-kicker">Public Hall</p>
        <h2>WebSocket 实时动态数据大屏</h2>
      </div>
      <a
        v-if="modelValue"
        class="btn btn-secondary ghost-link"
        :href="`https://sepolia.etherscan.io/address/${modelValue}`"
        target="_blank"
        rel="noreferrer"
      >
        Etherscan 验证
      </a>
    </div>

    <p class="desc">
      大屏通过 FastAPI WebSocket 持续接收链上投票事件，前端使用 ECharts 实时渲染走势曲线和排行榜，适合放在答辩展示或公众大厅。
    </p>

    <ElectionSelector :model-value="modelValue" @update:modelValue="$emit('update:modelValue', $event)" />
  </section>
</template>

<script setup>
import ElectionSelector from "../ElectionSelector.vue";

defineProps({
  modelValue: { type: String, default: "" },
});

defineEmits(["update:modelValue"]);
</script>

<style scoped>
.intro-card {
  padding: 24px 26px;
}

.intro-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.intro-kicker {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: #0369a1;
  font-weight: 700;
}

.intro-head h2 {
  margin: 0;
  font-size: 30px;
}

.desc {
  margin: 12px 0 18px;
  color: var(--text-secondary);
  max-width: 900px;
}

.ghost-link {
  border: 1px solid rgba(3, 105, 161, 0.18);
  background: rgba(2, 132, 199, 0.06);
  color: #075985;
  text-decoration: none;
}

.ghost-link:hover {
  background: rgba(2, 132, 199, 0.12);
}

@media (max-width: 768px) {
  .intro-head {
    flex-direction: column;
  }

  .intro-head h2 {
    font-size: 24px;
  }
}
</style>
