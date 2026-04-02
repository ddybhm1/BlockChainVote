<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link :to="homeTarget" class="nav-brand">
        ⛓️ 电子投票上链存证与安全管理系统
      </router-link>

      <div v-if="!isAdminPage" class="nav-links">
        <router-link :to="homeTarget" class="nav-link">首页</router-link>
        <router-link v-if="auth.isAuthenticated" to="/dashboard" class="nav-link">我的投票</router-link>
        <router-link to="/results" class="nav-link">实时结果</router-link>
      </div>
      <div v-else class="nav-links" style="justify-content: flex-end;">
        <router-link to="/results" class="nav-link">实时结果</router-link>
      </div>

      <div v-if="auth.isAuthenticated && !isAdminPage" class="nav-account">
        <details class="account-menu">
          <summary class="account-trigger">学号 {{ auth.studentId }}</summary>
          <div class="account-dropdown">
            <router-link to="/dashboard" class="dropdown-link">我的投票</router-link>
            <router-link to="/admin" class="dropdown-link">管理后台</router-link>
            <button class="dropdown-link dropdown-btn" type="button" @click="showSystemDialog = true">
              系统说明
            </button>
            <button class="dropdown-link dropdown-btn" type="button" @click="handleLogout">
              退出登录
            </button>
          </div>
        </details>
      </div>

      <button
        v-if="!auth.isAuthenticated && !isAdminPage"
        type="button"
        class="nav-login-btn"
        @click="showLoginDialog = true"
      >
        学号登录
      </button>

      <div v-if="showWalletConnect" class="nav-wallet">
        <WalletConnect />
      </div>

      <StudentLoginDialog
        v-if="!isAdminPage"
        v-model="showLoginDialog"
        redirect-path="/dashboard"
        source-label="Global Navigation"
      />

      <Teleport to="body">
        <transition name="dialog-fade">
          <div v-if="showSystemDialog" class="dialog-backdrop" @click.self="showSystemDialog = false">
            <div class="dialog-card">
              <button class="dialog-close" type="button" @click="showSystemDialog = false">关闭</button>
              <p class="dialog-kicker">System Notes</p>
              <h3>系统说明</h3>
              <p class="dialog-desc">当前学号 <strong>{{ auth.studentId }}</strong> 已完成身份登录，你现在看到的是登录后的学生工作台。</p>
              <ul class="dialog-list">
                <li>“我的投票”只展示属于当前学号的私密项目与状态。</li>
                <li>钱包地址只在具体项目申请投票权或投票时才介入，不会写回学号记录。</li>
                <li>实时结果页依然是公开的，任何访客都可以查看链上计票动态。</li>
              </ul>
              <div class="dialog-actions">
                <router-link to="/dashboard" class="btn btn-primary" @click="showSystemDialog = false">
                  返回我的投票
                </router-link>
              </div>
            </div>
          </div>
        </transition>
      </Teleport>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";
import StudentLoginDialog from "./StudentLoginDialog.vue";
import WalletConnect from "./WalletConnect.vue";
import { useAuthStore } from "../stores/auth.js";
import { useWalletStore } from "../stores/wallet.js";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const wallet = useWalletStore();
const showLoginDialog = ref(false);
const showSystemDialog = ref(false);

const isAdminPage = computed(() => route.path?.startsWith("/admin") || false);
const showWalletConnect = computed(() => isAdminPage.value || auth.isAuthenticated);
const homeTarget = computed(() => (auth.isAuthenticated ? { name: "Home", query: { preview: "1" } } : { name: "Home" }));

function handleLogout() {
  showSystemDialog.value = false;
  auth.logout();
  wallet.disconnect();
  router.push("/");
}
</script>

<style scoped>
.navbar {
  background: white;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-inner {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 40px;
}

.nav-brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  gap: 32px;
  flex: 1;
  align-items: center;
}

.nav-spacer {
  flex: 1;
}

.nav-link {
  position: relative;
  padding: 8px 0;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color 0.3s ease;
}

.nav-link:hover {
  color: var(--text-primary);
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--primary);
  border-radius: 2px 2px 0 0;
  opacity: 0;
  transform: scaleX(0);
  transform-origin: center;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.nav-link:hover::after {
  opacity: 0.3;
  transform: scaleX(1);
}

.nav-link.router-link-active {
  color: var(--primary);
  font-weight: 600;
}

.nav-link.router-link-active::after {
  opacity: 1;
  transform: scaleX(1);
}
.admin-link {
  margin-left: auto;
  color: #fbbf24;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}
.admin-link:hover {
  background: #fef3c7;
  color: #b45309;
}

.nav-account,
.nav-wallet {
  flex-shrink: 0;
}

.account-menu {
  position: relative;
}

.account-trigger,
.nav-login-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #ffffff;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  list-style: none;
  transition: all 0.2s ease;
}

.account-trigger:hover {
  background: #f8fafc;
  border-color: var(--primary);
}

.account-trigger::-webkit-details-marker {
  display: none;
}

.nav-login-btn {
  background: var(--primary);
  border-color: var(--primary);
  color: #ffffff;
  font-weight: 600;
}

.nav-login-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(91, 33, 182, 0.15);
}

.account-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  min-width: 150px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: #ffffff;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 20;
}

.dropdown-link {
  display: block;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
  font-size: 14px;
}

.dropdown-link:hover {
  background: #f8fafc;
}

.dropdown-btn {
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 350;
  padding: 20px;
  background: rgba(15, 23, 42, 0.46);
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-card {
  width: min(440px, 100%);
  padding: 26px;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.18);
  position: relative;
}

.dialog-close {
  position: absolute;
  top: 16px;
  right: 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 700;
}

.dialog-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #0f766e;
}

.dialog-card h3 {
  margin: 0;
}

.dialog-desc,
.dialog-list {
  color: var(--text-secondary);
}

.dialog-list {
  padding-left: 18px;
}

.dialog-list li + li {
  margin-top: 8px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.18s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .nav-inner {
    flex-wrap: wrap;
    height: auto;
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .nav-links {
    order: 3;
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
