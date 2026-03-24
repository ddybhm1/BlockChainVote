<template>
  <div class="wallet-connect">
    <template v-if="wallet.address">
      <span class="wallet-addr" :title="wallet.address">
        {{ shortAddress }}
      </span>
      <button class="btn-sm btn-outline" @click="wallet.disconnect()">断开</button>
    </template>
    <template v-else>
      <button class="btn-sm btn-primary" @click="wallet.connect()" :disabled="wallet.loading">
        {{ wallet.loading ? '连接中...' : '🦊 连接钱包' }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useWalletStore } from "../stores/wallet.js";

const wallet = useWalletStore();

const shortAddress = computed(() => {
  const addr = wallet.address;
  if (!addr) return "";
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
});
</script>

<style scoped>
.wallet-connect {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wallet-addr {
  font-size: 13px;
  font-family: monospace;
  color: var(--text-secondary);
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
}

.btn-sm {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-sm.btn-primary {
  background: var(--primary);
  color: white;
}
.btn-sm.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}
.btn-sm.btn-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-sm.btn-outline:hover {
  background: #f1f5f9;
}
</style>
