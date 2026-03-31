<template>
  <Teleport to="body">
    <transition name="dialog-fade">
      <div v-if="modelValue" class="dialog-backdrop" @click.self="handleClose">
        <div class="dialog-shell">
          <section class="dialog-aside">
            <p class="aside-kicker">{{ sourceLabel }}</p>
            <div class="crest-mark">
              <span>BV</span>
            </div>
            <h3>先验证学号身份，再进入个人投票空间</h3>
            <p class="aside-desc">
              这一步只负责确认你的学生身份。钱包地址会在具体项目操作时再介入，既保留流程严谨性，也照顾匿名投票体验。
            </p>

            <div class="aside-chips">
              <span class="aside-chip">学号登录</span>
              <span class="aside-chip">项目级匿名</span>
              <span class="aside-chip">链上公开计票</span>
            </div>

            <ul class="aside-points">
              <li>查看你拥有投票权的全部项目</li>
              <li>识别哪些项目待办、哪些已经完成</li>
              <li>在具体项目里按需连接或切换 MetaMask 地址</li>
            </ul>
          </section>

          <section class="dialog-panel">
            <button class="close-btn" type="button" @click="handleClose">关闭</button>

            <p class="panel-kicker">Student Login</p>
            <h2>学号登录</h2>
            <p class="panel-desc">登录成功后将直接进入“我的投票”仪表盘。</p>

            <form class="login-form" @submit.prevent="handleLogin">
              <label class="field-group">
                <span>学号</span>
                <input
                  v-model.trim="form.studentId"
                  class="input-field field-input"
                  placeholder="请输入学号"
                  autocomplete="username"
                  required
                />
              </label>

              <label class="field-group">
                <span>密码</span>
                <input
                  v-model="form.password"
                  class="input-field field-input"
                  type="password"
                  placeholder="请输入密码"
                  autocomplete="current-password"
                  required
                />
              </label>

              <div class="safe-note">
                登录只用于读取你的个人投票项目和状态，不会把钱包地址写入学号记录。
              </div>

              <div v-if="message" :class="['alert', isSuccess ? 'alert-success' : 'alert-error']">
                {{ message }}
              </div>

              <div class="form-actions">
                <button class="btn btn-secondary" type="button" @click="handleClose">
                  取消
                </button>
                <button class="btn btn-primary submit-btn" type="submit" :disabled="auth.loading">
                  {{ auth.loading ? "登录中..." : "登录并进入我的投票" }}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth.js";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  redirectPath: {
    type: String,
    default: "/dashboard",
  },
  sourceLabel: {
    type: String,
    default: "Campus Access",
  },
});

const emit = defineEmits(["update:modelValue", "success"]);

const auth = useAuthStore();
const router = useRouter();

const form = reactive({
  studentId: auth.studentId || "",
  password: "",
});

const message = computed(() => state.message);
const isSuccess = computed(() => state.isSuccess);

const state = reactive({
  message: "",
  isSuccess: false,
});

function resetState() {
  state.message = "";
  state.isSuccess = false;
  form.studentId = auth.studentId || form.studentId || "";
  form.password = "";
}

function handleClose() {
  emit("update:modelValue", false);
}

async function handleLogin() {
  state.message = "";

  try {
    await auth.login(form.studentId, form.password);
    await auth.loadMyElections();
    state.isSuccess = true;
    state.message = "验证成功，正在进入我的投票仪表盘。";
    emit("success");
    emit("update:modelValue", false);
    await router.push(props.redirectPath || "/dashboard");
  } catch (err) {
    state.isSuccess = false;
    state.message = err.response?.data?.detail || err.message || "登录失败";
  }
}

function handleKeydown(event) {
  if (event.key === "Escape" && props.modelValue) {
    handleClose();
  }
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      resetState();
      window.document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeydown);
      return;
    }

    window.document.body.style.overflow = "";
    window.removeEventListener("keydown", handleKeydown);
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  window.document.body.style.overflow = "";
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 400;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.22), transparent 26%),
    radial-gradient(circle at bottom right, rgba(15, 118, 110, 0.16), transparent 24%),
    rgba(15, 23, 42, 0.56);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.dialog-shell {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(360px, 420px);
  border-radius: 28px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 34px 90px rgba(15, 23, 42, 0.26);
}

.dialog-aside {
  position: relative;
  padding: 34px 34px 30px;
  color: #ecfeff;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.16), transparent 22%),
    radial-gradient(circle at 80% 75%, rgba(59, 130, 246, 0.24), transparent 26%),
    linear-gradient(145deg, #0f172a, #0f3d4a 52%, #14532d);
}

.aside-kicker,
.panel-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.aside-kicker {
  color: rgba(236, 254, 255, 0.72);
}

.crest-mark {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  margin-bottom: 18px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.crest-mark span {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.dialog-aside h3 {
  margin: 0;
  font-size: 34px;
  line-height: 1.18;
}

.aside-desc {
  margin: 16px 0 0;
  max-width: 520px;
  color: rgba(236, 254, 255, 0.82);
}

.aside-chips {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 18px 0 22px;
}

.aside-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.aside-points {
  margin: 0;
  padding-left: 18px;
  color: rgba(236, 254, 255, 0.88);
}

.aside-points li + li {
  margin-top: 8px;
}

.dialog-panel {
  position: relative;
  padding: 30px 30px 28px;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 1)),
    #ffffff;
}

.close-btn {
  position: absolute;
  top: 18px;
  right: 18px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.panel-kicker {
  color: #0f766e;
}

.dialog-panel h2 {
  margin: 0;
  font-size: 30px;
}

.panel-desc {
  margin: 10px 0 0;
  color: var(--text-secondary);
}

.login-form {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-size: 14px;
  font-weight: 600;
}

.field-input {
  min-height: 48px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
}

.safe-note {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbeafe;
  background: #f8fbff;
  color: #475569;
  font-size: 13px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.submit-btn {
  flex: 1;
  min-height: 48px;
  border-radius: 14px;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.22s ease;
}

.dialog-fade-enter-active .dialog-shell,
.dialog-fade-leave-active .dialog-shell {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .dialog-shell,
.dialog-fade-leave-to .dialog-shell {
  transform: translateY(10px) scale(0.985);
  opacity: 0;
}

@media (max-width: 860px) {
  .dialog-shell {
    grid-template-columns: 1fr;
  }

  .dialog-aside h3 {
    font-size: 28px;
  }
}

@media (max-width: 520px) {
  .dialog-backdrop {
    padding: 12px;
  }

  .dialog-panel,
  .dialog-aside {
    padding-left: 20px;
    padding-right: 20px;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
