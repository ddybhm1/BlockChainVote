<template>
  <div class="section">
    <h3>系统监控日志看板</h3>

    <div class="subsection">
      <h4>交易日志 (Gas 费用记录)</h4>
      <div class="log-controls">
        <div class="log-stats">
          总交易：<strong>{{ transactionLogs.length }}</strong> |
          平均 Gas：<strong>{{ avgGasUsed }}</strong>
        </div>
        <button class="btn btn-secondary" type="button" :disabled="loadingTxLogs" @click="$emit('refresh-transaction-logs')">
          {{ loadingTxLogs ? "加载中..." : "刷新日志" }}
        </button>
      </div>

      <div v-if="transactionLogs.length === 0" class="alert alert-info">
        暂无交易日志
      </div>
      <div v-else class="table-container">
        <table class="logs-table">
          <thead>
            <tr>
              <th>操作类型</th>
              <th>Gas 消耗</th>
              <th>总费用</th>
              <th>交易哈希</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in transactionLogs.slice(0, 15)" :key="log.id">
              <td><strong>{{ log.operation_type }}</strong></td>
              <td>{{ log.gas_used || "-" }}</td>
              <td class="tx-cost" :title="log.total_cost">{{ formatWeiValue(log.total_cost) }}</td>
              <td class="tx-hash">
                <a v-if="log.tx_hash" :href="`https://sepolia.etherscan.io/tx/${log.tx_hash}`" target="_blank" rel="noreferrer">
                  {{ log.tx_hash.slice(0, 10) }}...
                </a>
                <span v-else>-</span>
              </td>
              <td><span :class="['status-badge', `status-${log.status}`]">{{ log.status }}</span></td>
              <td class="time-cell">{{ formatAdminTime(log.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="subsection">
      <h4>安全拦截日志</h4>
      <div class="log-controls">
        <span class="log-stats">
          总事件：<strong>{{ securityLogStats.total }}</strong> |
          警告：<strong>{{ securityLogStats.warning }}</strong> |
          严重：<strong>{{ securityLogStats.critical }}</strong>
        </span>
        <button class="btn btn-secondary" type="button" :disabled="loadingSecLogs" @click="$emit('refresh-security-logs')">
          {{ loadingSecLogs ? "加载中..." : "刷新日志" }}
        </button>
      </div>

      <div v-if="securityLogs.length === 0" class="alert alert-info">
        暂无安全事件
      </div>
      <table v-else class="logs-table">
        <thead>
          <tr>
            <th>事件类型</th>
            <th>学号/地址</th>
            <th>详情</th>
            <th>严重程度</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in securityLogs.slice(0, 10)" :key="log.id" :class="`severity-${log.severity}`">
            <td><strong>{{ log.event_type }}</strong></td>
            <td>{{ log.student_id || "-" }}</td>
            <td class="details-cell">{{ log.details }}</td>
            <td><span :class="['severity-badge', `severity-${log.severity}`]">{{ log.severity }}</span></td>
            <td class="time-cell">{{ formatAdminTime(log.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { formatAdminTime, formatWeiValue } from "../../utils/admin.js";

defineProps({
  transactionLogs: { type: Array, default: () => [] },
  securityLogs: { type: Array, default: () => [] },
  securityLogStats: { type: Object, default: () => ({ total: 0, warning: 0, critical: 0 }) },
  avgGasUsed: { type: Number, default: 0 },
  loadingTxLogs: { type: Boolean, default: false },
  loadingSecLogs: { type: Boolean, default: false },
});

defineEmits(["refresh-transaction-logs", "refresh-security-logs"]);
</script>

<style scoped>
.section {
  margin-top: 24px;
}

.section h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.subsection {
  margin-top: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 4px solid var(--primary);
}

.subsection h4 {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--text);
}

.log-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
}

.log-stats {
  font-size: 13px;
  color: var(--text-secondary);
}

.table-container {
  overflow-x: auto;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.logs-table thead {
  background: var(--bg-secondary, #f5f5f5);
}

.logs-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

.logs-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}

.logs-table tbody tr:hover {
  background: #f9fafb;
}

.tx-cost,
.tx-hash {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.tx-hash {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.time-cell {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.details-cell {
  max-width: 300px;
  word-break: break-word;
}

.status-badge,
.severity-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-success {
  background: #d4edda;
  color: #155724;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.severity-info {
  background: #d1ecf1;
  color: #0c5460;
}

.severity-warning {
  background: #fff3cd;
  color: #856404;
}

.severity-critical {
  background: #f8d7da;
  color: #721c24;
}

.logs-table tbody tr.severity-critical {
  background: #fff5f5;
}

@media (max-width: 860px) {
  .log-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
