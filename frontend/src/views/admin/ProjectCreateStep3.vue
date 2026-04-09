<template>
  <el-container class="admin-layout">
    <el-header class="admin-header">
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/admin' }">管理面板</el-breadcrumb-item>
          <el-breadcrumb-item>新建投票项目 - 选民</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </el-header>

    <el-main class="admin-main">
      <el-card>
        <el-steps :active="2" finish-status="success" align-center style="margin-bottom: 30px;">
          <el-step title="项目信息" description="填写项目名称和时间" />
          <el-step title="添加候选人" description="可选" />
          <el-step title="添加选民" description="可选" />
          <el-step title="启动投票" description="最后确认" />
        </el-steps>

        <div style="margin: 0 auto; max-width: 800px; display: flex; flex-direction: column; gap: 16px;">
          <el-alert :title="'选民配置项目：' + contractAddr" type="success" />

          <AdminVoterManager
            :submitting="submitting"
            :message="wizardMsg"
            :message-ok="wizardMsgOk"
            :voter-stats="voterStats"
            :reset-key="voterResetKey"
            @submit="handleBatchRegister"
            @import-excel="handleExcelImport"
          />

          <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <el-button @click="router.push('/admin')">跳出向导 (取消)</el-button>
            <div style="display: flex; gap: 12px;">
              <el-button type="primary" @click="goToStep4">下一步（已完成或跳过）</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AdminVoterManager from '../../components/admin/AdminVoterManager.vue';
import { uploadVotersExcel, registerVoter, getVotersCount } from '../../services/api.js';

const route = useRoute();
const router = useRouter();

const contractAddr = computed(() => route.params.address);
const startTime = computed(() => route.query.start);
const endTime = computed(() => route.query.end);

const submitting = ref(false);
const wizardMsg = ref("");
const wizardMsgOk = ref(false);
const voterResetKey = ref(0);
const voterStats = reactive({ total: -1, claimed: 0 });

function goToStep4() {
  router.push(`/admin/create/${contractAddr.value}/step4?start=${encodeURIComponent(startTime.value)}&end=${encodeURIComponent(endTime.value)}`);
}

async function loadVoterStats() {
  if (!contractAddr.value) return;
  try {
    const data = await getVotersCount(contractAddr.value);
    voterStats.total = data.total_registered;
    voterStats.claimed = data.total_claimed;
  } catch (e) {
    console.error("获取选民统计失败:", e);
  }
}

onMounted(() => {
  loadVoterStats();
});

async function handleExcelImport(file) {
  if (!file) return;
  if (!contractAddr.value) {
    wizardMsg.value = "缺少目标合约地址";
    wizardMsgOk.value = false;
    return;
  }

  submitting.value = true;
  wizardMsg.value = "Excel 正在导入中...";
  wizardMsgOk.value = true;

  try {
    const res = await uploadVotersExcel(contractAddr.value, file);
    if (res.success) {
      wizardMsg.value = res.message;
      wizardMsgOk.value = true;
      if (res.errors && res.errors.length > 0) {
        wizardMsg.value += ` (部分错误: ${res.errors.join('; ')})`;
        wizardMsgOk.value = false;
      }
    } else {
      wizardMsg.value = res.message || "导入失败";
      wizardMsgOk.value = false;
    }
  } catch (e) {
    wizardMsg.value = `导入失败: ${e.response?.data?.detail || e.message}`;
    wizardMsgOk.value = false;
  } finally {
    submitting.value = false;
    await loadVoterStats();
  }
}

async function handleBatchRegister(items) {
  if (!items.length) return;
  if (!contractAddr.value) return;

  submitting.value = true;
  wizardMsg.value = "";
  let success = 0;
  let failed = 0;
  const errors = [];

  for (const v of items) {
    try {
      await registerVoter(v.studentId.trim(), v.password.trim(), contractAddr.value);
      success++;
    } catch (e) {
      failed++;
      const detail = e.response?.data?.detail || e.message;
      errors.push(`${v.studentId}: ${detail}`);
    }
  }

  if (failed === 0) {
    wizardMsg.value = `成功注册 ${success} 个选民！`;
    wizardMsgOk.value = true;
    voterResetKey.value += 1;
  } else {
    wizardMsg.value = `成功 ${success} 个，失败 ${failed} 个：${errors.join("；")}`;
    wizardMsgOk.value = false;
  }

  await loadVoterStats();
  submitting.value = false;
}
</script>

<style scoped>
.admin-layout { height: 100vh; background-color: #f5f7fa; }
.admin-header { background-color: #fff; border-bottom: 1px solid #ebedf0; display: flex; align-items: center; padding: 0 24px; height: 60px; }
.admin-main { padding: 24px; }
.alert { padding: 16px; border-radius: 8px; background: white; }
.alert-error { color: #b91c1c; background-color: #fef2f2; border: 1px solid #fecaca; }
.alert-success { color: #15803d; background-color: #f0fdf4; border: 1px solid #bbf7d0; }
</style>