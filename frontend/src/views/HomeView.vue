<template>
  <div class="home">
    <div class="hero card">
      <h1>⛓️ 基于区块链的安全可信电子投票系统</h1>
      <p class="subtitle">
        利用以太坊智能合约实现透明计票，IPFS 确保资料防篡改，<br />
        以“学号会话 + 项目内临时钱包”架构兼顾身份防伪与匿名投票。
      </p>

      <div class="hero-actions">
        <template v-if="auth.isAuthenticated">
          <button class="btn btn-primary" type="button" @click="router.push('/dashboard')">
            进入控制台
          </button>
        </template>
        <template v-else>
          <button class="btn btn-primary" type="button" @click="handleProtectedEntry">
            学号登录后领取选票
          </button>
          <button class="btn btn-success" type="button" @click="handleProtectedEntry">
            进入投票大厅
          </button>
        </template>
        <router-link to="/results" class="btn btn-secondary">📊 公众审计入口</router-link>
      </div>
    </div>

    <div class="features">
      <div class="feature card">
        <div class="feature-icon">🔒</div>
        <h3>身份防伪 + 项目级匿名</h3>
        <p>学号密码负责 Web2 登录，钱包只在具体项目里临时参与，管理员无法在数据库中恢复身份与地址映射。</p>
      </div>
      <div class="feature card">
        <div class="feature-icon">📦</div>
        <h3>IPFS 资料防篡改</h3>
        <p>候选人资料存入 IPFS，CID 写入智能合约。任何篡改都将导致哈希不匹配，被前端立即识别。</p>
      </div>
      <div class="feature card">
        <div class="feature-icon">📊</div>
        <h3>链上透明计票</h3>
        <p>选票直接上链，任何人都能在大屏或区块浏览器中验证票数变化，计票过程公开透明。</p>
      </div>
    </div>

    <div class="card">
      <h3>📋 投票流程</h3>
      <ol class="steps">
        <li><strong>学号登录</strong> - 点击右上角“学号登录”，完成身份验证并进入个人仪表盘</li>
        <li><strong>查看项目</strong> - 在“我的投票”中查看自己拥有哪些项目的投票权及当前状态</li>
        <li><strong>按需连接钱包</strong> - 只在具体项目里申请投票权或投票时连接 MetaMask</li>
        <li><strong>签名投票</strong> - 使用当前项目对应的钱包地址完成链上签名和投票</li>
        <li><strong>查看结果</strong> - 可在实时结果页或 Etherscan 中独立验证最终票数</li>
      </ol>
    </div>

    <StudentLoginDialog
      v-model="showLoginPrompt"
      :redirect-path="pendingEntry"
      source-label="Homepage Access"
      @success="clearLoginQuery"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import StudentLoginDialog from "../components/StudentLoginDialog.vue";
import { useAuthStore } from "../stores/auth.js";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const showLoginPrompt = ref(false);
const pendingEntry = ref("/dashboard");

function handleProtectedEntry() {
  const target = "/dashboard";

  if (auth.isAuthenticated) {
    router.push("/dashboard");
    return;
  }

  pendingEntry.value = target;
  showLoginPrompt.value = true;
}

function clearLoginQuery() {
  if (!route.query.login && !route.query.redirect) return;
  const nextQuery = { ...route.query };
  delete nextQuery.login;
  delete nextQuery.redirect;
  router.replace({ query: nextQuery });
}

watch(showLoginPrompt, (isOpen) => {
  if (isOpen) return;
  clearLoginQuery();
});

function syncLoginDialogFromRoute() {
  if (route.query.login !== "1") return;
  pendingEntry.value = typeof route.query.redirect === "string" ? route.query.redirect : "/dashboard";
  showLoginPrompt.value = true;
}

watch(
  () => [route.query.login, route.query.redirect],
  () => {
    syncLoginDialogFromRoute();
  }
);

onMounted(() => {
  syncLoginDialogFromRoute();
});
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 48px 24px;
}

.hero h1 {
  font-size: 28px;
  margin-bottom: 12px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: 24px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-secondary {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text);
  text-decoration: none;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.feature {
  text-align: center;
}

.feature-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.feature h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.feature p {
  font-size: 13px;
  color: var(--text-secondary);
}

.steps {
  padding-left: 20px;
}

.steps li {
  padding: 8px 0;
  font-size: 14px;
}

@media (max-width: 640px) {
  .features {
    grid-template-columns: 1fr;
  }
}
</style>
