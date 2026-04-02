<template>
  <div class="wallet-section">
    <template v-if="!walletAddress">
      <div class="alert alert-info">
        <p>连接管理钱包后，才能创建和维护投票项目。</p>
        <p class="wallet-desc">只有工厂合约拥有者地址才可以执行管理员操作。</p>
        <button class="btn btn-primary" type="button" :disabled="walletLoading" @click="$emit('connect')">
          {{ walletLoading ? "连接中..." : "连接 MetaMask 钱包" }}
        </button>
      </div>
    </template>

    <template v-else>
      <div :class="['wallet-info', { 'is-owner': isFactoryOwner }]">
        <div class="wallet-header">
          <span class="wallet-badge">
            <span v-if="isFactoryOwner" class="badge-owner">工厂拥有者</span>
            <span v-else class="badge-error">非拥有者</span>
          </span>
          <span class="wallet-address" :title="walletAddress">
            {{ walletAddress.slice(0, 6) }}...{{ walletAddress.slice(-4) }}
          </span>
        </div>

        <div v-if="!isFactoryOwner" class="alert alert-error">
          当前钱包地址不是工厂合约的拥有者，无法执行管理操作。请切换到拥有者账户。
        </div>
        <div v-else class="alert alert-success">
          当前钱包拥有管理员权限，可以继续创建项目、维护投票时间和选民名单。
        </div>

        <button class="btn btn-secondary" type="button" @click="$emit('disconnect')">
          断开钱包
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  walletAddress: { type: String, default: "" },
  walletLoading: { type: Boolean, default: false },
  isFactoryOwner: { type: Boolean, default: false },
});

defineEmits(["connect", "disconnect"]);
</script>

<style scoped>
.wallet-section {
  margin-bottom: 24px;
}

.wallet-section .alert {
  margin: 0;
  padding: 16px;
  border-radius: 8px;
}

.wallet-desc {
  margin: 8px 0 0;
  font-size: 13px;
}

.wallet-info {
  padding: 12px 16px;
  background: #f8f9fb;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.wallet-info.is-owner {
  background: #f0fdf4;
  border-color: #86efac;
}

.wallet-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.wallet-badge {
  display: flex;
  gap: 8px;
  align-items: center;
}

.badge-owner {
  display: inline-block;
  background: #fbbf24;
  color: #78350f;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.badge-error {
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.wallet-address {
  font-family: monospace;
  font-size: 13px;
  color: var(--text);
  flex: 1;
  text-align: right;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-secondary {
  margin-top: 8px;
}
</style>
