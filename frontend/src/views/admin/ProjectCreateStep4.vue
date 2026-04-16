<template>
  <el-container class="admin-layout">
    <el-header class="admin-header">
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/admin' }">管理面板</el-breadcrumb-item>
          <el-breadcrumb-item>新建投票项目 - 启动</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </el-header>

    <el-main class="admin-main">
      <el-card>
        <el-steps :active="3" finish-status="success" align-center style="margin-bottom: 30px;">
          <el-step title="项目信息" description="填写项目名称和时间" />
          <el-step title="添加候选人" description="可选" />
          <el-step title="添加选民" description="可选" />
          <el-step title="启动投票" description="最后确认" />
        </el-steps>

        <div style="margin: 0 auto; max-width: 600px; display: flex; flex-direction: column; gap: 16px;">
          <el-alert title="此步骤将最终锁定项目的投票时间，启动区块链投票机制。" type="warning" show-icon />
          <el-alert :title="'部署的目标合约：' + contractAddr" type="info" />
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
              <label style="display: block; margin-bottom: 8px; font-weight: 600;">投票开始时间</label>
              <el-input :model-value="startTime" disabled />
            </div>
            <div>
              <label style="display: block; margin-bottom: 8px; font-weight: 600;">投票结束时间</label>
              <el-input :model-value="endTime" disabled />
            </div>
          </div>

          <div v-if="wizardMsg" :class="['alert', wizardMsgOk ? 'alert-success' : 'alert-error']" style="margin-top: 16px;">{{ wizardMsg }}</div>

          <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <el-button @click="router.push('/admin')">暂不启动 (返回)</el-button>
            <el-button type="success" :loading="submitting" @click="handleStart">启动投票</el-button>
          </div>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { setVotingTime } from '../../services/api.js';
import { useVotingStore } from '../../stores/voting.js';

const route = useRoute();
const router = useRouter();
const voting = useVotingStore();

const contractAddr = computed(() => route.params.address);
const startTime = computed(() => route.query.start);
const endTime = computed(() => route.query.end);

const submitting = ref(false);
const wizardMsg = ref("");
const wizardMsgOk = ref(false);

async function handleStart() {
  if (!contractAddr.value || !startTime.value || !endTime.value) {
    wizardMsg.value = "缺少必要参数（地址或时间）";
    wizardMsgOk.value = false;
    return;
  }

  submitting.value = true;
  wizardMsg.value = "正在启动投票...";
  wizardMsgOk.value = true;

  try {
    const startTs = Math.floor(new Date(startTime.value).getTime() / 1000);
    const endTs = Math.floor(new Date(endTime.value).getTime() / 1000);

    await setVotingTime(contractAddr.value, startTs, endTs);
    
    wizardMsg.value = "✓ 投票已正式启动！项目现已生效。";
    wizardMsgOk.value = true;

    await voting.loadElections();
    
    setTimeout(() => {
      voting.selectElection(contractAddr.value);
      router.push({ name: 'Admin', query: { menu: 'project-board', addr: contractAddr.value } });
    }, 1500);
  } catch (e) {
    wizardMsg.value = "启动失败：" + (e.response?.data?.detail || e.message);
    wizardMsgOk.value = false;
  } finally {
    submitting.value = false;
  }
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