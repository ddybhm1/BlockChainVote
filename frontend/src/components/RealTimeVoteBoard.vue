<template>
  <div class="realtime-board">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Live On-Chain Feed</p>
        <h3>{{ titleText }}</h3>
        <p class="hero-desc">
          链上每确认一笔 <code>Voted</code> 事件，走势折线图、票数柱状图和热度榜都会同步刷新，无需手动刷新页面。
        </p>
      </div>
      <div class="hero-metrics">
        <div class="signal-pill" :class="signalClass">
          <span class="signal-dot"></span>
          {{ connectionText }}
        </div>
        <div class="metric-block">
          <span class="metric-value">{{ totals.voted }}</span>
          <span class="metric-label">已确认投票</span>
        </div>
        <div class="metric-inline">
          <span>授权选民 {{ totals.voters }}</span>
          <span>候选人 {{ totals.candidates }}</span>
          <span>{{ statusText }}</span>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>

    <div class="board-grid">
      <section class="screen-card trend-card">
        <div class="screen-header">
          <div>
            <h4>投票走势折线图</h4>
            <p>展示近 {{ recentEvents.length || 0 }} 笔确认交易带来的票数抬升</p>
          </div>
          <span class="screen-badge">Auto Live</span>
        </div>
        <div ref="trendChartEl" class="chart chart-tall"></div>
      </section>

      <section class="screen-card stats-card">
        <div class="screen-header">
          <div>
            <h4>票数实时滚动排行榜</h4>
            <p>票数变化时会自动重排并高亮最新上升项</p>
          </div>
          <span class="screen-badge subtle">Top {{ rankedCandidates.length }}</span>
        </div>

        <div ref="rankChartEl" class="chart chart-compact"></div>

        <div v-if="rankedCandidates.length" class="leaderboard">
          <div
            v-for="(candidate, index) in rankedCandidates"
            :key="candidate.id"
            class="leader-row"
            :class="{ 'leader-hot': latestVote && latestVote.candidateId === candidate.id }"
          >
            <div class="leader-rank">{{ index + 1 }}</div>
            <div class="leader-main">
              <strong>{{ candidate.name }}</strong>
              <span>{{ candidate.votes }} 票 · {{ candidateShare(candidate.votes) }}%</span>
            </div>
            <div class="leader-trend">
              <span v-if="latestVote && latestVote.candidateId === candidate.id" class="rise-chip">+1</span>
              <span v-else>{{ index === 0 ? "领跑" : "追赶中" }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          当前项目还没有候选人数据。
        </div>
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
        <div
          v-for="event in feedEvents"
          :key="`${event.txHash}-${event.sequence}`"
          class="feed-item"
          :class="{ 'feed-hot': latestVote && latestVote.txHash === event.txHash }"
        >
          <span class="feed-time">{{ formatClock(event.blockTime) }}</span>
          <strong>{{ candidateName(event.candidateId) }}</strong>
          <span class="feed-text">获得 1 票</span>
          <span class="feed-voter">{{ shortAddress(event.voter) }}</span>
          <a :href="txUrl(event.txHash)" target="_blank" rel="noreferrer">查看交易</a>
        </div>
      </div>

      <div v-else class="empty-state">
        暂时还没有抓到新的投票事件，保持页面打开后会自动接收链上更新。
      </div>
    </section>
  </div>
</template>

<script setup>
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { init, use, graphic } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from "vue";

use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

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

const trendChartEl = ref(null);
const rankChartEl = ref(null);
const candidates = ref([]);
const recentEvents = ref([]);
const latestVote = ref(null);
const errorMessage = ref("");
const connectionState = ref("connecting");
const totals = reactive({
  started: false,
  ended: false,
  candidates: 0,
  voters: 0,
  voted: 0,
});

let trendChart = null;
let rankChart = null;
let socket = null;
let reconnectTimer = null;
let activeAddress = "";

const titleText = computed(() => {
  return props.electionTitle
    ? `${props.electionTitle} · 实时投票动态大屏`
    : "实时投票动态大屏";
});

const rankedCandidates = computed(() => {
  return [...candidates.value].sort((a, b) => b.votes - a.votes);
});

const feedEvents = computed(() => {
  return [...recentEvents.value].slice(-10).reverse();
});

const statusText = computed(() => {
  if (!totals.started) return "投票未开始";
  if (totals.ended) return "投票已截止";
  return "投票进行中";
});

const connectionText = computed(() => {
  if (connectionState.value === "live") return "实时连接中";
  if (connectionState.value === "error") return "连接异常";
  if (connectionState.value === "disconnected") return "重连中";
  return "建立连接中";
});

const signalClass = computed(() => {
  return `signal-${connectionState.value}`;
});

watch(
  () => props.electionAddress,
  async (address) => {
    resetBoard();
    if (!address) {
      closeSocket();
      return;
    }
    activeAddress = address;
    await openSocket(address);
  },
  { immediate: true }
);

watch(
  [candidates, recentEvents, () => totals.voted],
  async () => {
    await nextTick();
    renderCharts();
  },
  { deep: true }
);

onMounted(async () => {
  await nextTick();
  initCharts();
  renderCharts();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  closeSocket();
  clearReconnect();
  window.removeEventListener("resize", handleResize);
  disposeCharts();
});

function resetBoard() {
  candidates.value = [];
  recentEvents.value = [];
  latestVote.value = null;
  errorMessage.value = "";
  connectionState.value = "connecting";
  syncTotals({});
}

async function openSocket(address) {
  closeSocket();
  clearReconnect();

  const ws = new WebSocket(buildWsUrl(address));
  socket = ws;

  ws.onopen = () => {
    connectionState.value = "live";
    errorMessage.value = "";
  };

  ws.onmessage = async (event) => {
    try {
      const payload = JSON.parse(event.data);
      applyPayload(payload);
      await nextTick();
      renderCharts();
    } catch (error) {
      errorMessage.value = `实时数据解析失败：${error.message || error}`;
    }
  };

  ws.onerror = () => {
    connectionState.value = "error";
    errorMessage.value = "实时连接出现异常，正在尝试重新连接。";
  };

  ws.onclose = () => {
    if (socket === ws) {
      socket = null;
    }

    if (activeAddress !== address) {
      return;
    }

    connectionState.value = "disconnected";
    scheduleReconnect(address);
  };
}

function closeSocket() {
  if (!socket) return;
  const current = socket;
  socket = null;
  current.onclose = null;
  current.close();
}

function scheduleReconnect(address) {
  clearReconnect();
  reconnectTimer = window.setTimeout(() => {
    if (activeAddress === address) {
      openSocket(address);
    }
  }, 3000);
}

function clearReconnect() {
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function applyPayload(payload) {
  if (payload.type === "snapshot") {
    syncTotals(payload.totals);
    candidates.value = payload.candidates || [];
    recentEvents.value = (payload.recentEvents || []).slice(-60);
    latestVote.value = recentEvents.value[recentEvents.value.length - 1] || null;
    connectionState.value = "live";
    return;
  }

  if (payload.type === "vote_update") {
    syncTotals(payload.totals);
    candidates.value = payload.candidates || candidates.value;
    recentEvents.value = [...recentEvents.value, ...(payload.newEvents || [])].slice(-60);
    latestVote.value = payload.latestVote || latestVote.value;
    connectionState.value = "live";
    return;
  }

  if (payload.type === "stream_error") {
    connectionState.value = "error";
    errorMessage.value = payload.message || "实时推流出现异常";
  }
}

function syncTotals(nextTotals = {}) {
  totals.started = Boolean(nextTotals.started);
  totals.ended = Boolean(nextTotals.ended);
  totals.candidates = Number(nextTotals.candidates || 0);
  totals.voters = Number(nextTotals.voters || 0);
  totals.voted = Number(nextTotals.voted || 0);
}

function buildWsUrl(address) {
  const configuredBase = import.meta.env.VITE_WS_BASE_URL;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const base = configuredBase || `${protocol}://${window.location.host}`;
  const normalizedBase = base.replace(/\/$/, "");
  return `${normalizedBase}/ws/elections/${address}/votes`;
}

function initCharts() {
  if (trendChartEl.value && !trendChart) {
    trendChart = init(trendChartEl.value);
  }
  if (rankChartEl.value && !rankChart) {
    rankChart = init(rankChartEl.value);
  }
}

function disposeCharts() {
  if (trendChart) {
    trendChart.dispose();
    trendChart = null;
  }
  if (rankChart) {
    rankChart.dispose();
    rankChart = null;
  }
}

function handleResize() {
  trendChart?.resize();
  rankChart?.resize();
}

function renderCharts() {
  initCharts();

  if (trendChart) {
    const trendSeries = buildTrendSeries();
    trendChart.setOption({
      animationDuration: 500,
      backgroundColor: "transparent",
      grid: {
        left: 48,
        right: 20,
        top: 28,
        bottom: 36,
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(5, 15, 33, 0.92)",
        borderWidth: 0,
        textStyle: { color: "#e6f4ff" },
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: trendSeries.labels,
        axisLabel: {
          color: "rgba(226, 240, 255, 0.72)",
          fontSize: 11,
        },
        axisLine: {
          lineStyle: { color: "rgba(103, 160, 210, 0.28)" },
        },
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        axisLabel: {
          color: "rgba(226, 240, 255, 0.72)",
        },
        splitLine: {
          lineStyle: { color: "rgba(103, 160, 210, 0.14)" },
        },
      },
      series: [
        {
          type: "line",
          smooth: true,
          symbolSize: 8,
          data: trendSeries.values,
          lineStyle: {
            width: 4,
            color: "#3dd9b6",
          },
          itemStyle: {
            color: "#fbbf24",
            borderColor: "#ffffff",
            borderWidth: 1,
          },
          areaStyle: {
            color: new graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(61, 217, 182, 0.42)" },
              { offset: 1, color: "rgba(61, 217, 182, 0.02)" },
            ]),
          },
        },
      ],
    });
  }

  if (rankChart) {
    const ranking = [...rankedCandidates.value].slice(0, 6).reverse();
    rankChart.setOption({
      animationDuration: 500,
      backgroundColor: "transparent",
      grid: {
        left: 12,
        right: 12,
        top: 12,
        bottom: 12,
        containLabel: true,
      },
      xAxis: {
        type: "value",
        minInterval: 1,
        axisLabel: { color: "rgba(226, 240, 255, 0.7)" },
        splitLine: {
          lineStyle: { color: "rgba(103, 160, 210, 0.14)" },
        },
      },
      yAxis: {
        type: "category",
        data: ranking.map((candidate) => candidate.name),
        axisLabel: {
          color: "#f5fbff",
          fontWeight: 600,
        },
        axisLine: {
          lineStyle: { color: "rgba(103, 160, 210, 0.18)" },
        },
      },
      series: [
        {
          type: "bar",
          data: ranking.map((candidate) => ({
            value: candidate.votes,
            itemStyle: {
              color:
                latestVote.value && latestVote.value.candidateId === candidate.id
                  ? "#ff8a4c"
                  : "#3b82f6",
              borderRadius: [0, 10, 10, 0],
            },
          })),
          label: {
            show: true,
            position: "right",
            color: "#f8fbff",
            fontWeight: 700,
          },
        },
      ],
    });
  }
}

function buildTrendSeries() {
  if (!recentEvents.value.length) {
    return {
      labels: ["当前票数"],
      values: [totals.voted],
    };
  }

  const labels = [];
  const values = [];
  let currentVotes = Math.max(0, totals.voted - recentEvents.value.length);

  recentEvents.value.forEach((event) => {
    currentVotes += 1;
    labels.push(formatClock(event.blockTime));
    values.push(currentVotes);
  });

  return { labels, values };
}

function candidateShare(votes) {
  if (!totals.voted) return "0.0";
  return ((votes / totals.voted) * 100).toFixed(1);
}

function candidateName(candidateId) {
  return candidates.value.find((candidate) => candidate.id === candidateId)?.name || `候选人 #${candidateId}`;
}

function formatClock(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString("zh-CN", {
    hour12: false,
  });
}

function shortAddress(address) {
  if (!address) return "--";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function txUrl(hash) {
  return `https://sepolia.etherscan.io/tx/${hash}`;
}
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
  grid-template-columns: minmax(0, 1.5fr) minmax(350px, 0.95fr);
  gap: 18px;
}

.screen-card {
  padding: 20px;
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

.chart-tall {
  height: 360px;
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

.leader-row:hover {
  transform: translateY(-1px);
}

.leader-hot {
  border-color: rgba(251, 146, 60, 0.58);
  box-shadow: 0 0 0 1px rgba(251, 146, 60, 0.18), 0 12px 28px rgba(251, 146, 60, 0.12);
}

.leader-rank {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #38bdf8, #2563eb);
  font-weight: 800;
  font-size: 16px;
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
  border-color: rgba(61, 217, 182, 0.45);
  box-shadow: 0 0 0 1px rgba(61, 217, 182, 0.16);
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
</style>
