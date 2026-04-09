<template>
  <el-container class="admin-layout">
    <el-header class="admin-header">
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/admin' }">管理面板</el-breadcrumb-item>
          <el-breadcrumb-item>新建投票项目</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </el-header>

    <el-main class="admin-main">
      <el-card>
        <el-steps :active="0" finish-status="success" align-center style="margin-bottom: 30px;">
          <el-step title="项目信息" description="填写项目名称和时间" />
          <el-step title="添加候选人" description="可选" />
          <el-step title="添加选民" description="可选" />
          <el-step title="启动投票" description="最后确认" />
        </el-steps>

        <div style="max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px;">
          <el-alert title="此步骤将创建一个新的智能合约，需要钱包签名并消耗 Gas。" type="info" show-icon />
          
          <div>
            <label style="display: block; margin-bottom: 8px; font-weight: 600;">项目名称 *</label>
            <el-input v-model="wizardData.projectName" placeholder="例如：学生会换届投票 2026" />
          </div>

          <div>
            <label style="display: block; margin-bottom: 8px; font-weight: 600;">SBT 徽章图片 *</label>
            <div style="display: flex; gap: 12px; align-items: flex-start;">
              <div style="flex: 1;">
                <el-input v-model="wizardData.sbtImageCid" placeholder="图片 CID（自动填入）" disabled />
              </div>
              <label class="btn btn-secondary" :class="{ disabled: wizardData.sbtImageUploading }" style="margin: 0; cursor: pointer; white-space: nowrap; padding: 8px 16px; border: 1px solid #DCDFE6; border-radius: 4px;">
                {{ wizardData.sbtImageUploading ? '上传中...' : '上传图片到 IPFS' }}
                <input type="file" accept="image/*" style="display: none" @change="handleUploadImage" :disabled="wizardData.sbtImageUploading" />
              </label>
            </div>
            <div v-if="wizardData.sbtImageError" style="color: #ef4444; font-size: 12px; margin-top: 4px;">{{ wizardData.sbtImageError }}</div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
              <label style="display: block; margin-bottom: 8px; font-weight: 600;">投票开始时间 *</label>
              <el-date-picker v-model="wizardData.startTime" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" />
            </div>
            <div>
              <label style="display: block; margin-bottom: 8px; font-weight: 600;">投票结束时间 *</label>
              <el-date-picker v-model="wizardData.endTime" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" />
            </div>
          </div>

          <div v-if="wizardMsg" :class="['alert', wizardMsgOk ? 'alert-success' : 'alert-error']" style="margin-top:16px;">{{ wizardMsg }}</div>
          
          <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <el-button @click="router.push('/admin')">取消返回</el-button>
            <el-button type="primary" :loading="wizardStepSubmitting" :disabled="!wizardStep1Valid()" @click="handleDeploy">部署项目</el-button>
          </div>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useVotingStore } from '../../stores/voting.js';
import { uploadToIPFS, syncElectionToBackend } from '../../services/api.js';

const router = useRouter();
const voting = useVotingStore();

const wizardData = reactive({
  projectName: "",
  sbtImageCid: "",
  sbtImageUploading: false,
  sbtImageError: "",
  startTime: "",
  endTime: ""
});
const wizardStepSubmitting = ref(false);
const wizardMsg = ref("");
const wizardMsgOk = ref(false);

async function handleUploadImage(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  wizardData.sbtImageUploading = true;
  wizardData.sbtImageError = "";
  try {
    const result = await uploadToIPFS(file);
    wizardData.sbtImageCid = result.cid;
  } catch (e) {
    wizardData.sbtImageError = "图片上传失败：" + (e.response?.data?.detail || e.message);
  } finally {
    wizardData.sbtImageUploading = false;
    event.target.value = "";
  }
}

function wizardStep1Valid() {
  return wizardData.projectName.trim() &&
         wizardData.sbtImageCid.trim() &&
         wizardData.startTime &&
         wizardData.endTime &&
         new Date(wizardData.endTime) > new Date(wizardData.startTime);
}

async function handleDeploy() {
  if (!wizardStep1Valid()) {
    wizardMsg.value = "请检查所有输入：项目名称、SBT 图片、开始时间和结束时间";
    wizardMsgOk.value = false;
    return;
  }

  wizardStepSubmitting.value = true;
  wizardMsg.value = "正在将项目部署到区块链...";
  wizardMsgOk.value = true;

  try {
    const factory = await voting.getFactoryWriteContract();
    const tx = await factory.createElection(
      wizardData.projectName.trim(),
      wizardData.sbtImageCid.trim()
    );
    
    wizardMsg.value = "交易已发送，等待链上确认...";
    const receipt = await tx.wait();
    
    const iface = factory.interface;
    let newAddr = "";
    for (const log of receipt.logs) {
      try {
        const parsed = iface.parseLog(log);
        if (parsed && parsed.name === "ElectionCreated") {
          newAddr = parsed.args.electionAddr;
          break;
        }
      } catch {}
    }

    if (!newAddr) throw new Error("无法解析新合约地址");
    
    try {
      const startTs = Math.floor(new Date(wizardData.startTime).getTime() / 1000);
      const endTs = Math.floor(new Date(wizardData.endTime).getTime() / 1000);
      await syncElectionToBackend(newAddr, wizardData.projectName, startTs, endTs);
    } catch (e) {
      console.warn("后端同步项目可能有问题:", e);
    }

    wizardMsg.value = "✓ 合约部署成功！准备跳转到下一步...";
    wizardMsgOk.value = true;
    
    await voting.loadElections();
    
    setTimeout(() => {
      router.push(`/admin/create/${newAddr}/step2?start=${encodeURIComponent(wizardData.startTime)}&end=${encodeURIComponent(wizardData.endTime)}`);
    }, 1000);
  } catch (e) {
    wizardMsg.value = "部署失败：" + (e.reason || e.message);
    wizardMsgOk.value = false;
  } finally {
    wizardStepSubmitting.value = false;
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