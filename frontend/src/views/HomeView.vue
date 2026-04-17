<template>
  <div class="home">
    <div class="hero card">
      <h1>⛓️ 基于区块链的安全可信电子投票系统</h1>
      <p class="subtitle">
        面向校园选举的链上投票平台，支持身份核验、匿名投票与公开计票。<br />
        投票前先完成学号登录，实时结果页则始终对公众开放。
      </p>

      <div class="hero-actions">
        <template v-if="auth.isAuthenticated">
          <button class="btn btn-primary" type="button" @click="router.push('/dashboard')">
            进入我的投票
          </button>
          <router-link to="/creator" class="btn btn-secondary">创建自己的投票项目</router-link>
          <router-link to="/results" class="btn btn-secondary">查看公开计票结果</router-link>
        </template>
        <template v-else>
          <button class="btn btn-primary" type="button" @click="handleProtectedEntry">
            学号登录开始投票
          </button>
          <router-link to="/creator" class="btn btn-secondary">钱包登录创建投票项目</router-link>
          <router-link to="/results" class="btn btn-secondary">查看公开计票结果</router-link>
        </template>
      </div>

      <p class="hero-note">
        选民入口只有一条主路径：先验证学号身份，再进入“我的投票”按项目连接钱包完成投票。
      </p>
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
      <div class="feature card">
        <div class="feature-icon">🛠️</div>
        <h3>创建自己的投票项目</h3>
        <p>无需学号密码，直接通过钱包连接进入自治投票站，支付开站费后即可链上创建独立子合约项目。</p>
        <div style="margin-top: 12px;">
          <router-link to="/creator" class="btn btn-secondary">进入自治投票站</router-link>
        </div>
      </div>
    </div>

    <div class="card steps-card">
      <h3>📋 使用流程</h3>
      <ol class="steps">
        <li><strong>学号登录</strong> - 点击页面中的“学号登录开始投票”或右上角“学号登录”完成身份验证</li>
        <li><strong>查看项目</strong> - 在“我的投票”中查看自己拥有哪些项目的投票权及当前状态</li>
        <li><strong>按需连接钱包</strong> - 只在具体项目里申请投票权或投票时连接 MetaMask</li>
        <li><strong>签名投票</strong> - 使用当前项目对应的钱包地址完成链上签名和投票</li>
        <li><strong>查看结果</strong> - 可在实时结果页或 Etherscan 中独立验证最终票数，访客也可直接查看</li>
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
  padding: 64px 24px;
  background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.8) 100%);
  border: none;
}

.hero h1 {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #1f2937 0%, #4f46e5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 18px;
  max-width: 600px;
  margin: 0 auto 32px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-note {
  margin: 24px auto 0;
  max-width: 760px;
  color: #9ca3af;
  font-size: 14px;
}

.btn-secondary {
  background: rgba(255,255,255,0.9);
  border: 1px solid var(--border);
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.feature {
  text-align: center;
  padding: 32px 24px;
  border-top: 4px solid var(--primary);
}

.feature-icon {
  font-size: 42px;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
}

.feature h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #111827;
}

.feature p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.steps-card {
  padding: 32px;
}

.steps-card h3 {
  font-size: 20px;
  margin-top: 0;
  margin-bottom: 24px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.steps {
  padding-left: 0;
  list-style: none;
  counter-reset: step;
}

.steps li {
  position: relative;
  padding: 12px 0 12px 48px;
  font-size: 15px;
  color: #374151;
  border-bottom: 1px dashed #e5e7eb;
}

.steps li:last-child {
  border-bottom: none;
}

.steps li::before {
  counter-increment: step;
  content: counter(step);
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
}

.steps strong {
  color: #111827;
}

@media (max-width: 768px) {
  .features {
    grid-template-columns: 1fr;
  }
}
</style>
