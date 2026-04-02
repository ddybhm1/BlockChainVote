<template>
  <section id="election-detail" class="card detail-card">
    <div class="detail-head">
      <div>
        <p class="detail-kicker">当前项目</p>
        <h3>{{ displayTitle(item.title) }}</h3>
        <div class="detail-address-row">
          <span>{{ shortAddress(item.election_address) }}</span>
          <button class="copy-btn" type="button" @click="$emit('copy-address', item.election_address)">复制地址</button>
        </div>
      </div>

      <div class="detail-badges">
        <span :class="['badge', phaseBadgeClass(item.phase)]">{{ phaseLabel(item.phase) }}</span>
        <span :class="['badge', ticketBadgeClass(item.status)]">{{ ticketLabel(item.status) }}</span>
      </div>
    </div>

    <div class="detail-grid">
      <div class="detail-panel">
        <h4>项目概览</h4>
        <p><strong>投票时间：</strong>{{ votingRange }}</p>
        <p><strong>链上已投票数：</strong>{{ totalVotes }}</p>
        <p><strong>候选人数：</strong>{{ candidateCount }}</p>
      </div>

      <div id="wallet-operation" class="detail-panel wallet-panel">
        <h4>钱包操作</h4>
        <p class="wallet-copy">
          <template v-if="walletAddress">
            当前钱包：<strong>{{ shortAddress(walletAddress) }}</strong>
          </template>
          <template v-else>
            当前未连接钱包，请在需要操作的项目里临时连接。
          </template>
        </p>

        <div class="wallet-actions">
          <button class="btn btn-primary" type="button" :disabled="walletLoading" @click="$emit('connect-wallet')">
            {{ walletLoading ? "连接中..." : walletAddress ? "切换钱包" : "连接钱包" }}
          </button>
          <button v-if="walletAddress" class="btn btn-secondary" type="button" @click="$emit('refresh-status')">
            检查当前地址状态
          </button>
        </div>

        <div class="wallet-state">
          <span class="mini-state">链上授权：{{ walletAddress ? (isAuthorized ? "是" : "否") : "-" }}</span>
          <span class="mini-state">链上已投：{{ walletAddress ? (hasVoted ? "是" : "否") : "-" }}</span>
        </div>

        <p class="wallet-hint">{{ walletHint }}</p>

        <div class="wallet-cta-row">
          <button
            v-if="showAuthorizeButton"
            class="btn btn-claim"
            type="button"
            :disabled="authorizeLoading || !walletAddress"
            @click="$emit('authorize')"
          >
            {{ authorizeLoading ? "申请中..." : "申请投票权" }}
          </button>
          <button
            v-else-if="showVoteButton"
            class="btn btn-primary"
            type="button"
            @click="$emit('vote-now')"
          >
            立即投票
          </button>
          <button v-else-if="showPendingButton" class="btn btn-disabled" type="button" disabled>
            敬请期待
          </button>
          <button v-else class="btn btn-secondary" type="button" @click="$emit('view-results', item.election_address)">
            查看结果
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import {
  displayTitle,
  formatRangeFull,
  phaseBadgeClass,
  phaseLabel,
  shortAddress,
  ticketBadgeClass,
  ticketLabel,
} from "../../utils/dashboard.js";

const props = defineProps({
  item: { type: Object, required: true },
  startTime: { type: Number, default: 0 },
  endTime: { type: Number, default: 0 },
  totalVotes: { type: Number, default: 0 },
  candidateCount: { type: Number, default: 0 },
  walletAddress: { type: String, default: "" },
  walletLoading: { type: Boolean, default: false },
  isAuthorized: { type: Boolean, default: false },
  hasVoted: { type: Boolean, default: false },
  authorizeLoading: { type: Boolean, default: false },
});

defineEmits([
  "copy-address",
  "connect-wallet",
  "refresh-status",
  "authorize",
  "vote-now",
  "view-results",
]);

const votingRange = computed(() =>
  formatRangeFull(props.startTime || props.item.start_time, props.endTime || props.item.end_time)
);

const walletHint = computed(() => {
  if (!props.item.eligible) {
    return "这个学号当前未被分配到该项目的投票资格。你仍然可以查看项目信息、候选人与公开结果，但不能在这里申请票权或投票。";
  }

  if (props.item.status === "AVAILABLE") {
    return "这是你当前最需要处理的项目。连接一个钱包后点击“申请投票权”，系统就会为这个项目授予该地址投票资格。";
  }

  if (props.item.status === "CLAIMED") {
    return "这个项目已经领票，请切换到当时授权的钱包地址后直接投票。";
  }

  return "这个项目已经完成或结束，现在更适合查看结果和留档。";
});

const showAuthorizeButton = computed(
  () => props.item.eligible && props.item.status === "AVAILABLE" && props.item.phase === "ACTIVE"
);

const showVoteButton = computed(
  () => props.item.eligible && props.item.status === "CLAIMED" && props.item.phase === "ACTIVE"
);

const showPendingButton = computed(() => props.item.eligible && props.item.phase === "PENDING");
</script>

<style scoped>
.detail-card {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 28%),
    #ffffff;
}

.detail-kicker {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 11px;
  color: #0f766e;
  font-weight: 700;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.detail-head h3 {
  margin: 0;
}

.detail-address-row,
.detail-badges,
.wallet-actions,
.wallet-cta-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-address-row {
  display: inline-flex;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.copy-btn {
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.copy-btn:hover {
  color: #0f172a;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.badge-phase-active {
  background: #e9f9ef;
  color: #0f8f4b;
}

.badge-phase-pending {
  background: #fff4df;
  color: #c27803;
}

.badge-phase-ended {
  background: #f1f5f9;
  color: #64748b;
}

.badge-ticket-available {
  background: #fff1f2;
  color: #d9485f;
}

.badge-ticket-restricted {
  background: #f8fafc;
  color: #64748b;
}

.badge-ticket-claimed {
  background: #eef4ff;
  color: #2563eb;
}

.badge-ticket-voted {
  background: #eaf8ef;
  color: #13803d;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.detail-panel {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #ffffff;
}

.detail-panel h4 {
  margin-top: 0;
}

.wallet-panel {
  background: linear-gradient(180deg, #ffffff, #f8fbff);
}

.wallet-copy,
.wallet-hint {
  color: var(--text-secondary);
}

.wallet-actions,
.wallet-cta-row {
  margin: 16px 0 0;
  flex-wrap: wrap;
}

.wallet-state {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.mini-state {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-secondary);
}

.wallet-hint {
  margin: 16px 0 0;
}

.btn-secondary {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid var(--border);
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fafc;
}

.btn-claim {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
}

.btn-disabled {
  background: #e5e7eb;
  color: #94a3b8;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
