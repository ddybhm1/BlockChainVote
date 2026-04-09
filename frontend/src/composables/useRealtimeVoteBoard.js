import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { init, use } from "echarts/core";
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

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

export function useRealtimeVoteBoard(props, rankChartEl) {
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

  let rankChart = null;
  let socket = null;
  let reconnectTimer = null;
  let activeAddress = "";

  const titleText = computed(() =>
    props.electionTitle ? `${props.electionTitle} · 实时投票动态大屏` : "实时投票动态大屏"
  );

  const rankedCandidates = computed(() => [...candidates.value].sort((a, b) => b.votes - a.votes));
  const feedEvents = computed(() => [...recentEvents.value].slice(-10).reverse());

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

  const signalClass = computed(() => `signal-${connectionState.value}`);

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
    if (rankChartEl.value && !rankChart) {
      rankChart = init(rankChartEl.value);
    }
  }

  function disposeCharts() {
    if (rankChart) {
      rankChart.dispose();
      rankChart = null;
    }
  }

  function handleResize() {
    rankChart?.resize();
  }

  function renderCharts() {
    initCharts();

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

  function candidateShare(votes) {
    if (!totals.voted) return "0.0";
    return ((votes / totals.voted) * 100).toFixed(1);
  }

  function candidateName(candidateId) {
    return candidates.value.find((candidate) => candidate.id === candidateId)?.name || `候选人 #${candidateId}`;
  }

  function formatClock(timestamp) {
    if (!timestamp) return "--:--:--";
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

  return {
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
  };
}
