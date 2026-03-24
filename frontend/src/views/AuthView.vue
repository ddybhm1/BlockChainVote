<template>
  <div class="auth-view">
    <div class="card">
      <h2>🎫 领取投票选票</h2>
      <p class="desc">验证学号身份后，授权当前钱包地址获得投票权。后端不会记录地址与学号的关联。</p>

      <ElectionSelector v-model="selectedElection" />

      <div v-if="!wallet.address" class="alert alert-info">
        请先点击右上角「连接钱包」按钮连接 MetaMask 钱包
      </div>

      <div v-else-if="!selectedElection" class="alert alert-info">
        请先选择要参与的投票项目
      </div>

      <template v-else>
        <div v-if="result.message" :class="['alert', result.success ? 'alert-success' : 'alert-error']">
          {{ result.message }}
          <div v-if="result.txHash" class="tx-link">
            交易哈希:
            <a :href="`https://sepolia.etherscan.io/tx/${result.txHash}`" target="_blank">
              {{ result.txHash.slice(0, 18) }}...
            </a>
          </div>
        </div>

        <form @submit.prevent="handleClaim" class="auth-form">
          <div class="form-group">
            <label>当前钱包地址（匿名地址）</label>
            <input class="input-field" :value="wallet.address" disabled />
          </div>
          <div class="form-group">
            <label>学号</label>
            <input class="input-field" v-model="form.studentId" placeholder="请输入学号" required />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input class="input-field" type="password" v-model="form.password" placeholder="请输入密码" required />
          </div>
          <button class="btn btn-primary" type="submit" :disabled="loading" style="width:100%">
            {{ loading ? '授权中...(等待链上确认)' : '申请投票资格' }}
          </button>
        </form>
      </template>
    </div>

    <div class="card">
      <h3>🔐 安全机制说明</h3>
      <ul class="security-notes">
        <li><strong>身份验证：</strong>后端在 MySQL 中校验学号与密码，拦截非法用户</li>
        <li><strong>防重复领票：</strong>每个学号在每个投票项目中仅能领取一次投票权</li>
        <li><strong>阅后即焚：</strong>后端授权完成后立即丢弃钱包地址，MySQL 中不保存任何映射</li>
        <li><strong>匿名投票：</strong>后续投票直接通过 MetaMask 与区块链交互，不经过后端</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useWalletStore } from "../stores/wallet.js";
import { claimTicket } from "../services/api.js";
import ElectionSelector from "../components/ElectionSelector.vue";

const wallet = useWalletStore();
const loading = ref(false);
const form = reactive({ studentId: "", password: "" });
const result = reactive({ success: false, message: "", txHash: "" });
const selectedElection = ref("");

async function handleClaim() {
  if (!wallet.address || !selectedElection.value) return;
  loading.value = true;
  result.message = "";
  result.txHash = "";

  try {
    const res = await claimTicket(form.studentId, form.password, wallet.address, selectedElection.value);
    result.success = true;
    result.message = res.message;
    result.txHash = res.tx_hash || "";
  } catch (err) {
    result.success = false;
    result.message = err.response?.data?.detail || err.message || "领票失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-view h2 {
  margin-bottom: 8px;
}
.desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 20px;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 14px;
  font-weight: 600;
}
.tx-link {
  margin-top: 6px;
  font-size: 13px;
}
.tx-link a {
  color: inherit;
  text-decoration: underline;
}
.security-notes {
  list-style: none;
  padding: 0;
}
.security-notes li {
  padding: 6px 0;
  font-size: 14px;
  color: var(--text-secondary);
}
</style>
