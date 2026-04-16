<template>
  <div class="realtime-board">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Live On-Chain Feed</p>
        <h3>{{ titleText }}</h3>
        <p class="hero-desc">
          链上每确认一笔 <code>Voted</code> 事件，票数柱状图与热度榜都会同步刷新，无需手动刷新页面。
        </p>
      </div>
      <div class="hero-metrics">
        <div class="signal-pill" :class="signalClass">
          <span class="signal-dot"></span>
          {{ connectionText }}
        </div>
        <div class="metric-block">
          <span class="metric-value"><AnimatedNumber :value="totals.voted" /></span>
          <span class="metric-label">已确认投票</span>
        </div>
        <div class="metric-inline">
          <span>授权选民 <AnimatedNumber :value="totals.voters" /></span>
          <span>候选人 <AnimatedNumber :value="totals.candidates" /></span>
          <span>{{ statusText }}</span>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>

    <div class="board-grid">
      <section class="screen-card stats-card">
        <div class="screen-header">
          <div>
            <h4>票数实时滚动排行榜</h4>
            <p>票数变化时会自动重排并高亮最新上升项</p>
          </div>
          <span class="screen-badge subtle">Top {{ rankedCandidates.length }}</span>
        </div>

        <div ref="rankChartEl" class="chart chart-compact"></div>
      </section>
    </div>

    <section class="screen-card live-feed-card">
      <div class="screen-header">
        <div>
          <h4>最新上链播报</h4>
          <p>最新确认的投票事件会在这里持续滚动展示</p>
        </div>
        <span class="screen-badge warm">Confirmed Feed</span>
      </div>

      <div v-if="feedEvents.length" class="feed-list">
          <TransitionGroup name="bubble-pop">
            <div
              v-for="event in feedEvents"
              :key="`${event.txHash}-${event.sequence}`"
              class="feed-item"
              :class="{ 'feed-hot': latestVote && latestVote.txHash === event.txHash }"
            >
              <span class="feed-time">{{ formatClock(event.blockTime) }}</span>
              <el-avatar
                :size="24"
                :src="`https://api.dicebear.com/7.x/identicon/svg?seed=${event.candidateId}`"
                class="feed-avatar"
              />
              <strong>{{ candidateName(event.candidateId) }}</strong>
              <span class="feed-text">获得 1 票</span>
              <span class="feed-voter">{{ shortAddress(event.voter) }}</span>
              <a :href="txUrl(event.txHash)" target="_blank" rel="noreferrer">查看交易</a>
            </div>
          </TransitionGroup>        </div>
      <div v-else class="empty-state">
        暂时还没有抓到新的投票事件，保持页面打开后会自动接收链上更新。
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import AnimatedNumber from "./AnimatedNumber.vue";
import { useRealtimeVoteBoard } from "../composables/useRealtimeVoteBoard.js";

const props = defineProps({
  electionAddress: {
    type: String,
    required: true,
  },
  electionTitle: {
    type: String,
    default: "",
  },
});

const rankChartEl = ref(null);

const {
  candidates,
  recentEvents,
  latestVote,
  errorMessage,
  totals,
  titleText,
  rankedCandidates,
  feedEvents,
  statusText,
  connectionText,
  signalClass,
  candidateShare,
  candidateName,
  formatClock,
  shortAddress,
  txUrl,
} = useRealtimeVoteBoard(props, rankChartEl);
</script>

<style scoped>
.realtime-board {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-panel,
.screen-card {
  border: 1px solid rgba(86, 138, 184, 0.24);
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(74, 222, 128, 0.16), transparent 32%),
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.2), transparent 28%),
    linear-gradient(135deg, #091423 0%, #0b2034 48%, #112b42 100%);
  box-shadow: 0 20px 60px rgba(4, 12, 24, 0.24);
  color: #f5fbff;
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 1fr);
  gap: 24px;
  padding: 28px;
}

.eyebrow {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: #7dd3fc;
}

.hero-copy h3 {
  margin: 0;
  font-size: 32px;
  line-height: 1.15;
}

.hero-desc {
  margin: 14px 0 0;
  color: rgba(226, 240, 255, 0.78);
  max-width: 720px;
}

.hero-desc code {
  color: #fde68a;
}

.hero-metrics {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 16px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(6, 18, 32, 0.46);
  border: 1px solid rgba(92, 154, 204, 0.18);
}

.signal-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.signal-live {
  color: #bbf7d0;
  background: rgba(20, 83, 45, 0.52);
}

.signal-connecting,
.signal-disconnected {
  color: #fde68a;
  background: rgba(133, 77, 14, 0.4);
}

.signal-error {
  color: #fecaca;
  background: rgba(127, 29, 29, 0.44);
}

.signal-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 16px currentColor;
}

.metric-block {
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 58px;
  line-height: 0.95;
  font-weight: 800;
  color: #f8fafc;
}

.metric-label {
  margin-top: 6px;
  color: rgba(226, 240, 255, 0.72);
}

.metric-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 13px;
  color: rgba(226, 240, 255, 0.8);
}

.metric-inline span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(14, 30, 48, 0.55);
}

.board-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
}

.screen-card {
  padding: 20px;
  backdrop-filter: blur(16px) saturate(180%);
  background: rgba(11, 25, 44, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 8px 32px 0 rgba(0, 0, 0, 0.37),
    inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.screen-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.screen-header h4 {
  margin: 0;
  font-size: 18px;
}

.screen-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(226, 240, 255, 0.7);
}

.screen-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.18);
  color: #bbf7d0;
  font-size: 12px;
  font-weight: 700;
}

.screen-badge.subtle {
  background: rgba(125, 211, 252, 0.14);
  color: #bae6fd;
}

.screen-badge.warm {
  background: rgba(251, 146, 60, 0.18);
  color: #fed7aa;
}

.chart {
  width: 100%;
}

.chart-compact {
  height: 260px;
}

.leaderboard {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.leader-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(7, 22, 37, 0.55);
  border: 1px solid rgba(103, 160, 210, 0.14);
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

@keyframes pulse-glow {
  0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(56, 189, 248, 0); }
  100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
}

.leader-row:hover {
  transform: translateY(-1px);
}

.leader-hot {
  animation: pulse-glow 2s infinite;
  border-color: rgba(56, 189, 248, 0.5) !important;
  background: rgba(56, 189, 248, 0.1) !important;
}

.flip-list-move {
  transition: transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.leader-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.leader-main strong {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.leader-main span,
.leader-trend {
  font-size: 13px;
  color: rgba(226, 240, 255, 0.74);
}

.rise-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(251, 146, 60, 0.2);
  color: #fdba74;
  font-weight: 700;
}

.live-feed-card {
  overflow: hidden;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feed-item {
  display: grid;
  grid-template-columns: 90px minmax(110px, 180px) 1fr 120px 84px;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(7, 22, 37, 0.55);
  border: 1px solid rgba(103, 160, 210, 0.14);
}

.feed-hot {
  position: relative;
  overflow: hidden;
}

.feed-hot::after {
  content: "";
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  animation: scan 1.5s ease;
}

@keyframes scan {
  100% { left: 100%; }
}

.feed-time,
.feed-voter,
.feed-text,
.feed-item a {
  font-size: 13px;
  color: rgba(226, 240, 255, 0.72);
}

.feed-item a {
  color: #7dd3fc;
  text-decoration: none;
}

.feed-item a:hover {
  color: #bae6fd;
}

.empty-state {
  padding: 24px;
  border-radius: 18px;
  text-align: center;
  color: rgba(226, 240, 255, 0.72);
  background: rgba(7, 22, 37, 0.4);
}

@media (max-width: 1100px) {
  .hero-panel,
  .board-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 800px) {
  .hero-panel,
  .screen-card {
    padding: 18px;
  }

  .hero-copy h3 {
    font-size: 26px;
  }

  .metric-value {
    font-size: 48px;
  }

  .feed-item {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
.race-bar-row {
  position: relative;
  overflow: hidden;
  padding: 0;
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.4) !important;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.race-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: transparent;
  z-index: 0;
  pointer-events: none;
}

.race-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.3) 0%, rgba(99, 102, 241, 0.6) 100%);
  transition: width 1s cubic-bezier(0.25, 1, 0.5, 1);
  border-right: 2px solid #60a5fa;
}

.leader-hot .race-bar-fill {
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.4) 0%, rgba(239, 68, 68, 0.7) 100%);
  border-right: 2px solid #fbbf24;
}

.leader-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  width: 100%;
}

.leader-avatar {
  margin-right: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.leader-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

.votes-num {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
}

.pulse-badge {
  background: #ef4444;
  color: #fff;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.75rem;
  font-weight: 800;
}
.bubble-pop-enter-active {
  transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.bubble-pop-leave-active {
  transition: all 0.4s ease-in;
}
.bubble-pop-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
.bubble-pop-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
.bubble-pop-move {
  transition: transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.feed-avatar {
  margin: 0 8px;
  vertical-align: middle;
  border: 1px solid rgba(255,255,255,0.2);
}

.feed-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  margin-bottom: 8px;
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}
</style>
