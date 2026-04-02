<template>
  <div class="results-view">
    <ResultsIntroCard v-model="selectedElection" />

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
import { defineAsyncComponent } from "vue";
import { useRoute, useRouter } from "vue-router";
import ResultsIntroCard from "../components/results/ResultsIntroCard.vue";
import { useResultsSelection } from "../composables/useResultsSelection.js";
import { useVotingStore } from "../stores/voting.js";

const RealTimeVoteBoard = defineAsyncComponent(() => import("../components/RealTimeVoteBoard.vue"));

const voting = useVotingStore();
const route = useRoute();
const router = useRouter();

const { selectedElection, selectedTitle } = useResultsSelection(voting, route, router);
</script>

<style scoped>
.results-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
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
</style>
