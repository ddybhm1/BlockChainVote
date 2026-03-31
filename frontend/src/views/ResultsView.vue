<template>
  <div class="results-view">
    <section class="card intro-card">
      <div class="intro-head">
        <div>
          <p class="intro-kicker">Public Hall</p>
          <h2>WebSocket 实时动态数据大屏</h2>
        </div>
        <a
          v-if="selectedElection"
          class="btn btn-secondary ghost-link"
          :href="`https://sepolia.etherscan.io/address/${selectedElection}`"
          target="_blank"
          rel="noreferrer"
        >
          Etherscan 验证
        </a>
      </div>

      <p class="desc">
        大屏通过 FastAPI WebSocket 持续接收链上投票事件，前端使用 ECharts 实时渲染走势曲线和排行榜，适合放在答辩展示或公众大厅。
      </p>

      <ElectionSelector v-model="selectedElection" />
    </section>

    <RealTimeVoteBoard
      v-if="selectedElection"
      :election-address="selectedElection"
      :election-title="selectedTitle"
    />

    <section v-else class="card empty-card">
      <p class="empty-title">先选择一个投票项目</p>
      <p class="empty-desc">选中后会自动建立实时连接，并持续接收最新的链上投票动态。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ElectionSelector from "../components/ElectionSelector.vue";
import RealTimeVoteBoard from "../components/RealTimeVoteBoard.vue";
import { useVotingStore } from "../stores/voting.js";

const voting = useVotingStore();
const route = useRoute();
const router = useRouter();
const selectedElection = ref("");

watch(selectedElection, async (address) => {
  if (!address) {
    const nextQuery = { ...route.query };
    delete nextQuery.election;
    router.replace({ query: nextQuery });
    return;
  }

  if (route.query.election !== address) {
    router.replace({ query: { ...route.query, election: address } });
  }
  await voting.selectElection(address);
});

const selectedTitle = computed(() => {
  return (
    voting.elections.find(
      (election) => election.address.toLowerCase() === selectedElection.value.toLowerCase()
    )?.title || ""
  );
});

onMounted(() => {
  if (typeof route.query.election === "string" && route.query.election) {
    selectedElection.value = route.query.election;
  }
});

watch(
  () => voting.elections,
  (items) => {
    if (!selectedElection.value) return;
    const matched = items.find(
      (item) => item.address.toLowerCase() === selectedElection.value.toLowerCase()
    );
    if (matched && matched.address !== selectedElection.value) {
      selectedElection.value = matched.address;
    }
  },
  { deep: true }
);
</script>

<style scoped>
.results-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

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

.empty-card {
  padding: 48px 24px;
  text-align: center;
}

.empty-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
}

.empty-desc {
  margin: 0;
  color: var(--text-secondary);
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
