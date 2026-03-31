<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="nav-brand">
        ⛓️ 区块链投票系统
      </router-link>
      <div v-if="!isAdminPage" class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/auth" class="nav-link">{{ auth.isAuthenticated ? "身份中心" : "登录" }}</router-link>
        <router-link to="/vote" class="nav-link">我的投票</router-link>
        <router-link to="/results" class="nav-link">实时结果</router-link>
      </div>
      <div v-else class="nav-spacer"></div>
      <div v-if="auth.isAuthenticated && !isAdminPage" class="nav-session">
        学号 {{ auth.studentId }}
      </div>
      <div class="nav-wallet">
        <WalletConnect />
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import WalletConnect from "./WalletConnect.vue";
import { useAuthStore } from "../stores/auth.js";

const route = useRoute();
const auth = useAuthStore();

const isAdminPage = computed(() => route.path === "/admin");
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
  max-width: 960px;
  margin: 0 auto;
  padding: 0 16px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 24px;
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
  gap: 8px;
  flex: 1;
}

.nav-spacer {
  flex: 1;
}

.nav-link {
  padding: 6px 14px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.nav-link:hover {
  background: #f1f5f9;
  color: var(--text);
}
.nav-link.router-link-active {
  background: #eef2ff;
  color: var(--primary);
  font-weight: 600;
}

.nav-wallet {
  flex-shrink: 0;
}

.nav-session {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--text-secondary);
  background: #f8fafc;
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 999px;
}
</style>
