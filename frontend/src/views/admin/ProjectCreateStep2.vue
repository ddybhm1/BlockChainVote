<template>
  <el-container class="admin-layout">
    <el-header class="admin-header">
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/admin' }">管理面板</el-breadcrumb-item>
          <el-breadcrumb-item>新建投票项目 - 候选人</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </el-header>

    <el-main class="admin-main">
      <el-card>
        <el-steps :active="1" finish-status="success" align-center style="margin-bottom: 30px;">
          <el-step title="项目信息" description="填写项目名称和时间" />
          <el-step title="添加候选人" description="可选" />
          <el-step title="添加选民" description="可选" />
          <el-step title="启动投票" description="最后确认" />
        </el-steps>

        <div style="margin: 0 auto; max-width: 800px; display: flex; flex-direction: column; gap: 16px;">
          <el-alert :title="'项目已部署：' + contractAddr" type="success" />
          
          <AdminCandidateManager
            :status-started="false"
            :submitting="submitting"
            :candidates="candidates"
            :reset-key="candidateResetKey"
            @submit="handleBatchAdd"
          />

          <div v-if="wizardMsg" :class="['alert', wizardMsgOk ? 'alert-success' : 'alert-error']" style="margin-top: 16px;">{{ wizardMsg }}</div>

          <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <el-button @click="router.push('/admin')">跳出向导 (取消)</el-button>
            <div style="display: flex; gap: 12px;">
              <el-button type="primary" @click="goToStep3">下一步（如果没有或已添加）</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AdminCandidateManager from '../../components/admin/AdminCandidateManager.vue';
import { useWalletStore } from '../../stores/wallet.js';
import { logTransaction } from '../../services/api.js';
import { ethers } from 'ethers';
import { ELECTION_ABI } from '../../services/contract.js';

const route = useRoute();
const router = useRouter();
const wallet = useWalletStore();

const contractAddr = computed(() => route.params.address);
const startTime = computed(() => route.query.start);
const endTime = computed(() => route.query.end);

const submitting = ref(false);
const wizardMsg = ref("");
const wizardMsgOk = ref(false);
const candidates = ref([]);
const candidateResetKey = ref(0);

function goToStep3() {
  router.push(`/admin/create/${contractAddr.value}/step3?start=${encodeURIComponent(startTime.value)}&end=${encodeURIComponent(endTime.value)}`);
}

async function getWriteContract(addr) {
  const signer = await wallet.getSigner();
  if (!signer) throw new Error("请先连接钱包");
  return new ethers.Contract(addr, ELECTION_ABI, signer);
}

async function handleBatchAdd(items) {
  if (!items.length) return;
  if (!contractAddr.value) {
    wizardMsg.value = "缺少合约地址信息";
    wizardMsgOk.value = false;
    return;
  }

  submitting.value = true;
  wizardMsg.value = "";
  try {
    const contract = await getWriteContract(contractAddr.value);
    const names = items.map(i => i.name.trim());
    const cids = items.map(i => i.cid.trim());
    const manifestoCids = items.map(i => i.manifestoCid.trim());

    let tx;
    if (items.length === 1) {
      tx = await contract.addCandidate(names[0], cids[0], manifestoCids[0]);
    } else {
      tx = await contract.addCandidatesBatch(names, cids, manifestoCids);
    }

    wizardMsg.value = `交易已发送（${items.length} 个候选人），等待链上确认...`;
    wizardMsgOk.value = true;

    await logTransaction({
      tx_hash: tx.hash,
      election_address: contractAddr.value,
      operation_type: "ADD_CANDIDATES",
      status: "pending"
    });

    const receipt = await tx.wait();

    await logTransaction({
      tx_hash: tx.hash,
      election_address: contractAddr.value,
      operation_type: "ADD_CANDIDATES",
      gas_used: Number(receipt.gasUsed),
      total_cost: receipt.fee.toString(),
      status: "success"
    });

    wizardMsg.value = `✓ 成功添加 ${items.length} 个候选人！可以点击下一步。`;
    wizardMsgOk.value = true;
    candidateResetKey.value += 1;
    // For wizard logic, we don't necessarily need to reload candidates, just display success message.
  } catch (e) {
    wizardMsg.value = e.reason || e.message || "添加失败";
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