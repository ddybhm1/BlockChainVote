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
            <router-link to="/vote" class="btn btn-primary">进入我的投票</router-link>
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
    router.push(route.query.redirect || "/vote");
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
  gap: 16px;
}

.auth-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 420px);
  gap: 20px;
  align-items: stretch;
}

.hero-copy {
  padding-right: 12px;
}

.hero-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #0f766e;
}

.hero-copy h2 {
  margin: 0 0 12px;
  font-size: 34px;
  line-height: 1.2;
}

.desc,
.session-desc,
.flow-card p {
  color: var(--text-secondary);
}

.inner-card {
  margin-bottom: 0;
  background:
    linear-gradient(145deg, rgba(79, 70, 229, 0.08), rgba(14, 165, 233, 0.05)),
    #ffffff;
}

.session-chip {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #047857;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 12px;
}

.student-line {
  margin: 12px 0 8px;
  font-size: 15px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
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

.session-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.btn-ghost {
  background: #ffffff;
  color: var(--text);
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
