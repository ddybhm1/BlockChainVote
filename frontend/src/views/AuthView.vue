<template>
  <div class="auth-view">
    <section class="card auth-hero">
      <div class="hero-copy">
        <p class="hero-kicker">Identity-Centered Flow</p>
        <h2>学号登录后，再决定每个项目使用哪个钱包投票</h2>
        <p class="desc">
          系统先用学号和密码建立登录会话，再展示你拥有投票权的项目列表。钱包只会在具体项目点击“领票”或“投票”时临时介入，支持为不同项目切换不同地址。
        </p>
      </div>

      <div class="hero-side card inner-card">
        <template v-if="auth.isAuthenticated">
          <div class="session-chip">已登录</div>
          <h3>欢迎回来</h3>
          <p class="student-line">当前学号：<strong>{{ auth.studentId }}</strong></p>
          <p class="session-desc">现在可以进入“我的投票”，查看各项目的未领票、已领票和已投票状态。</p>

          <div class="session-actions">
            <router-link to="/dashboard" class="btn btn-primary">进入我的投票</router-link>
            <button class="btn btn-ghost" type="button" @click="handleLogout">退出登录</button>
          </div>
        </template>

        <template v-else>
          <h3>身份登录</h3>
          <p class="session-desc">先建立学号会话，再按项目选择钱包地址进行匿名投票。</p>

          <form class="auth-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label>学号</label>
              <input v-model="form.studentId" class="input-field" placeholder="请输入学号" required />
            </div>
            <div class="form-group">
              <label>密码</label>
              <input v-model="form.password" class="input-field" type="password" placeholder="请输入密码" required />
            </div>

            <div v-if="message" :class="['alert', loginSuccess ? 'alert-success' : 'alert-error']">
              {{ message }}
            </div>

            <button class="btn btn-primary" type="submit" :disabled="auth.loading" style="width: 100%">
              {{ auth.loading ? "登录中..." : "登录并查看我的投票" }}
            </button>
          </form>
        </template>
      </div>
    </section>

    <section class="card">
      <h3>流程亮点</h3>
      <div class="flow-grid">
        <article class="flow-card">
          <span class="step-no">01</span>
          <h4>身份登录</h4>
          <p>后端签发学号会话，前端后续接口都带 JWT，不再用钱包地址充当登录凭证。</p>
        </article>
        <article class="flow-card">
          <span class="step-no">02</span>
          <h4>查看我的项目</h4>
          <p>仪表盘从 MySQL 读取每个项目的状态机，直接告诉你哪些项目未领票、已领票、已投票。</p>
        </article>
        <article class="flow-card">
          <span class="step-no">03</span>
          <h4>项目内临时连钱包</h4>
          <p>只有在具体项目中点击领票或投票时才连接 MetaMask，因此可以自由切换地址完成跨项目匿名投票。</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth.js";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const form = reactive({
  studentId: auth.studentId || "",
  password: "",
});
const message = ref("");
const loginSuccess = ref(false);

async function handleLogin() {
  message.value = "";

  try {
    await auth.login(form.studentId, form.password);
    await auth.loadMyElections();
    loginSuccess.value = true;
    message.value = "登录成功，正在进入我的投票仪表盘。";
    router.push(route.query.redirect || "/dashboard");
  } catch (err) {
    loginSuccess.value = false;
    message.value = err.response?.data?.detail || err.message || "登录失败";
  }
}

function handleLogout() {
  auth.logout();
  form.password = "";
  message.value = "";
}
</script>

<style scoped>
.auth-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.auth-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 420px);
  gap: 32px;
  align-items: stretch;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.4));
  border: none;
}

.hero-copy {
  padding-right: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-kicker {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--primary);
}

.hero-copy h2 {
  margin: 0 0 16px;
  font-size: 38px;
  line-height: 1.25;
  background: linear-gradient(135deg, #1f2937, #4f46e5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.desc,
.session-desc,
.flow-card p {
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.7;
}

.inner-card {
  margin-bottom: 0;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.85));
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  padding: 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.session-chip {
  display: inline-flex;
  padding: 6px 14px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #047857;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 16px;
  align-self: flex-start;
}

.student-line {
  margin: 16px 0 12px;
  font-size: 16px;
  color: #111827;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.session-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 24px;
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.5);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 24px;
}

.flow-card {
  padding: 24px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius);
  border: 1px solid rgba(255, 255, 255, 0.9);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.flow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.step-no {
  display: inline-block;
  font-size: 24px;
  font-weight: 900;
  color: var(--primary);
  opacity: 0.2;
  margin-bottom: 8px;
}

.flow-card h4 {
  font-size: 18px;
  margin-top: 0;
  margin-bottom: 12px;
  color: #1f2937;
}

.flow-card p {
  font-size: 14px;
  margin: 0;
}

@media (max-width: 860px) {
  .auth-hero {
    grid-template-columns: 1fr;
  }
  .flow-grid {
    grid-template-columns: 1fr;
  }
}
</style>
  border: 1px solid var(--border);
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.flow-card {
  padding: 18px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.flow-card h4 {
  margin: 10px 0 8px;
}

.step-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #0f172a;
  color: #ffffff;
  font-weight: 700;
  letter-spacing: 0.04em;
}

@media (max-width: 900px) {
  .auth-hero,
  .flow-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy h2 {
    font-size: 28px;
  }
}
</style>
