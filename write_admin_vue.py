import pathlib

file_content = """\
<template>
  <el-container class="admin-layout">
    <!-- Sidebar -->
    <el-aside width="250px" class="admin-sidebar">
      <div class="sidebar-logo">
        <el-icon :size="24" color="#fff" style="margin-right: 8px"><Monitor /></el-icon>
        <span style="color:#fff;font-weight:600;font-size:16px;">电子投票控制台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1E222D"
        text-color="#A3A6B0"
        active-text-color="#fff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="overview">
          <el-icon><DataLine /></el-icon>
          <span>概览看板</span>
        </el-menu-item>
        <el-menu-item index="projects">
          <el-icon><FolderOpened /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="candidates">
          <el-icon><UserFilled /></el-icon>
          <span>候选人管理</span>
        </el-menu-item>
        <el-menu-item index="voters">
          <el-icon><Tickets /></el-icon>
          <span>选票管理</span>
        </el-menu-item>
        <el-menu-item index="logs">
          <el-icon><List /></el-icon>
          <span>交易与安全</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- Header -->
      <el-header class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>管理面板</el-breadcrumb-item>
            <el-breadcrumb-item>{{ activeMenuName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <AdminAccessPanel
            :wallet-address="wallet.address"
            :wallet-loading="wallet.loading"
            :is-factory-owner="wallet.isFactoryOwner"
            @connect="wallet.connect()"
            @disconnect="wallet.disconnect()"
          />
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main class="admin-main">
        <div v-if="!wallet.address || !wallet.isFactoryOwner" class="alert alert-error">
          <el-empty description="管理员中心仅通过钱包地址认证，请先通过顶部右上角的 Wallet Connect 连接具有管理员权限的钱包" />
        </div>
        <div v-else>
          <!-- Global Message -->
          <el-alert v-if="globalMsg" :title="globalMsg" :type="globalMsgOk ? 'success' : 'error'" show-icon style="margin-bottom: 20px" />

          <!-- Context Selector -->
          <el-card shadow="hover" class="context-card" v-if="activeMenu !== 'overview'">
             <span style="font-weight:bold;margin-right:12px;">当前管理项目</span>
             <el-tag v-if="selectedTitle" type="primary" size="large" style="margin-right:12px;">{{ selectedTitle }}</el-tag>
             <el-tag v-else type="info" size="large" style="margin-right:12px;">未选择</el-tag>
             <span v-if="selectedAddr" style="font-family:monospace; color:#6b7280; font-size:13px; margin-right:12px;">{{ selectedAddr }}</span>
             <el-tag :type="status.ended ? 'danger' : (status.started ? 'success' : 'warning')" v-if="selectedAddr">
               {{ status.ended ? '已结束' : (status.started ? '进行中' : '未开始') }}
             </el-tag>
          </el-card>

          <!-- 1. Overview Board -->
          <div v-show="activeMenu === 'overview'">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-card shadow="hover" class="data-card">
                  <div class="card-icon" style="background:#E1F3D8;color:#67C23A;"><el-icon><VideoPlay /></el-icon></div>
                  <div class="card-info">
                    <div class="label">活跃项目</div>
                    <div class="value">{{ myElections ? myElections.length : 0 }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" class="data-card">
                  <div class="card-icon" style="background:#D9ECFF;color:#409EFF;"><el-icon><User /></el-icon></div>
                  <div class="card-info">
                    <div class="label">已投选票</div>
                    <div class="value">{{ voterStats.total !== -1 ? voterStats.total : '-' }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" class="data-card">
                  <div class="card-icon" style="background:#FAECD8;color:#E6A23C;"><el-icon><Cpu /></el-icon></div>
                  <div class="card-info">
                    <div class="label">Gas 消耗总额</div>
                    <div class="value">{{ avgGasUsed }} <span style="font-size:12px">wei</span></div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" class="data-card">
                  <div class="card-icon" style="background:#FDE2E2;color:#F56C6C;"><el-icon><WarnTriangleFilled /></el-icon></div>
                  <div class="card-info">
                    <div class="label">系统安全健康</div>
                    <div class="value" :style="{color: securityLogStats.critical > 0 ? '#F56C6C' : '#67C23A'}">
                      {{ securityLogStats.critical > 0 ? '风险' : '健康' }}
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 2. Projects -->
          <div v-show="activeMenu === 'projects'">
            <div style="margin-bottom:20px;">
              <AdminProjectSidebar
                :title="newTitle"
                :sbt-image-cid="newSbtImageCid"
                :creating="creating"
                :elections="myElections"
                :selected-addr="selectedAddr"
                @update:title="newTitle = $event"
                @update:sbtImageCid="newSbtImageCid = $event"
                @create="handleCreate"
                @select="handleSelect"
              />
            </div>
            
            <el-card shadow="hover" class="section-card" v-if="selectedAddr" header="时间控制">
              <div v-if="message" class="alert" :class="messageOk ? 'alert-success' : 'alert-error'" style="margin-bottom:12px">
                {{ message }}
              </div>
              <div style="display: flex; gap: 16px; align-items: center;">
                <el-date-picker v-model="startTime" type="datetime" placeholder="开始时间" :disabled="submitting || deployed" value-format="YYYY-MM-DDTHH:mm:ss" />
                <span style="color:#909399">至</span>
                <el-date-picker v-model="endTime" type="datetime" placeholder="结束时间" :disabled="submitting || deployed" value-format="YYYY-MM-DDTHH:mm:ss" />
                <el-button type="primary" :disabled="deployed || submitting || !candidates.length || !startTime || !endTime" @click="handleSaveVotingTime">
                   {{ submitting ? '部署中...' : (deployed ? '部署成功' : '部署') }}
                </el-button>
              </div>
              <el-alert v-if="deployed" title="项目已部署" type="info" description="当前项目已部署投票窗口时间，不可更改" show-icon style="margin-top:12px;"/>
            </el-card>
          </div>

          <!-- 3. Candidates -->
          <div v-show="activeMenu === 'candidates'">
            <el-card shadow="never" class="section-card" body-style="padding:0">
              <AdminCandidateManager
                :status-started="status.started"
                :submitting="submitting"
                :candidates="candidates"
                :reset-key="candidateResetKey"
                @submit="handleBatchAdd"
              />
            </el-card>
          </div>

          <!-- 4. Voters -->
          <div v-show="activeMenu === 'voters'">
            <el-card shadow="never" class="section-card" body-style="padding:0">
              <AdminVoterManager
                :submitting="voterSubmitting"
                :message="voterMessage"
                :message-ok="voterMessageOk"
                :voter-stats="voterStats"
                :reset-key="voterResetKey"
                @submit="handleBatchRegister"
                @import-excel="handleExcelImport"
              />
            </el-card>
          </div>

          <!-- 5. Logs Console -->
          <div v-show="activeMenu === 'logs'">
            <div class="console-wrapper">
              <AdminLogsPanel
                :transaction-logs="transactionLogs"
                :security-logs="securityLogs"
                :security-log-stats="securityLogStats"
                :avg-gas-used="avgGasUsed"
                :loading-tx-logs="loadingTxLogs"
                :loading-sec-logs="loadingSecLogs"
                @refresh-transaction-logs="loadTransactionLogs"
                @refresh-security-logs="loadSecurityLogs"
              />
            </div>
          </div>

        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ethers } from "ethers";
import { Monitor, DataLine, FolderOpened, UserFilled, Tickets, List, VideoPlay, User, Cpu, WarnTriangleFilled } from '@element-plus/icons-vue';

import AdminAccessPanel from "../components/admin/AdminAccessPanel.vue";
import AdminCandidateManager from "../components/admin/AdminCandidateManager.vue";
import AdminLogsPanel from "../components/admin/AdminLogsPanel.vue";
import AdminProjectSidebar from "../components/admin/AdminProjectSidebar.vue";
import AdminVoterManager from "../components/admin/AdminVoterManager.vue";
import { useWalletStore } from "../stores/wallet.js";
import { useVotingStore } from "../stores/voting.js";
import { ELECTION_ABI } from "../services/contract.js";
import { 
  registerVoter, 
  getVotersCount,
  uploadVotersExcel,
  getTransactionLogs,
  getSecurityLogs,
  logTransaction,
  setVotingTime
} from "../services/api.js";

// Layout state
const activeMenu = ref('overview');
const activeMenuName = computed(() => {
  const map = {
    overview: '概览看板',
    projects: '项目管理',
    candidates: '候选人管理',
    voters: '选票管理',
    logs: '交易与安全'
  };
  return map[activeMenu.value];
});

function handleMenuSelect(index) {
  activeMenu.value = index;
}

const startTime = ref("");
const endTime = ref("");
const deployed = ref(false);
const deployedStartTs = ref(0);
const deployedEndTs = ref(0);

const wallet = useWalletStore();
const voting = useVotingStore();

// 创建项目
const newTitle = ref("");
const newSbtImageCid = ref("");
const creating = ref(false);
const globalMsg = ref("");
const globalMsgOk = ref(false);

// 选中项目
const selectedAddr = ref("");
const selectedTitle = ref("");
const isAdmin = ref(false);
const submitting = ref(false);
const message = ref("");
const messageOk = ref(false);
const candidates = ref([]);
const status = reactive({ started: false, ended: false, candidates: 0 });
const voterSubmitting = ref(false);
const voterMessage = ref("");
const voterMessageOk = ref(false);
const voterStats = reactive({ total: -1, claimed: 0 });
const candidateResetKey = ref(0);
const voterResetKey = ref(0);

// ==================== 监控日志 ====================
const transactionLogs = ref([]);
const securityLogs = ref([]);
const securityLogStats = reactive({ total: 0, warning: 0, critical: 0 });
const loadingTxLogs = ref(false);
const loadingSecLogs = ref(false);

const avgGasUsed = computed(() => {
  if (transactionLogs.value.length === 0) return 0;
  const valid = transactionLogs.value.filter(l => l.gas_used > 0);
  if (valid.length === 0) return 0;
  const total = valid.reduce((acc, curr) => acc + curr.gas_used, 0);
  return Math.round(total / valid.length);
});

// 我创建的项目
const myElections = computed(() =>
  voting.elections.filter(e => e.creator.toLowerCase() === wallet.address?.toLowerCase())
);

function toDatetimeLocal(seconds) {
  if (!seconds) return "";
  const date = new Date(Number(seconds) * 1000);
  const pad = (v) => String(v).padStart(2, "0");
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function resetDeploymentState() {
  deployed.value = false;
  deployedStartTs.value = 0;
  deployedEndTs.value = 0;
  startTime.value = "";
  endTime.value = "";
}

function getReadContract(addr) {
  const provider = new ethers.JsonRpcProvider(
    import.meta.env.VITE_SEPOLIA_RPC || "https://rpc.sepolia.org"
  );
  return new ethers.Contract(addr, ELECTION_ABI, provider);
}

async function getWriteContract(addr) {
  const signer = await wallet.getSigner();
  if (!signer) throw new Error("请先连接钱包");
  return new ethers.Contract(addr, ELECTION_ABI, signer);
}

// ==================== 投票时间保存 ====================
async function handleSaveVotingTime() {
  if (!selectedAddr.value || !startTime.value || !endTime.value || deployed.value) return;
  submitting.value = true;
  message.value = '';
  messageOk.value = false;
  try {
    const startTs = Math.floor(new Date(startTime.value).getTime() / 1000);
    const endTs = Math.floor(new Date(endTime.value).getTime() / 1000);
    if (!startTs || !endTs || endTs <= startTs) {
      message.value = "请正确设置开始和截止时间";
      messageOk.value = false;
      return;
    }

    const res = await setVotingTime(selectedAddr.value, startTs, endTs);
    deployed.value = true;
    deployedStartTs.value = startTs;
    deployedEndTs.value = endTs;
    startTime.value = toDatetimeLocal(startTs);
    endTime.value = toDatetimeLocal(endTs);
    message.value = '部署成功，区块链将自动控制投票窗口。TxHash: ' + (res.tx_hash || '');
    messageOk.value = true;
    await voting.selectElection(selectedAddr.value);
  } catch (e) {
    message.value = '保存失败：' + (e.response?.data?.detail || e.message);
    messageOk.value = false;
  } finally {
    submitting.value = false;
  }
}

// ==================== 创建项目 ====================
async function handleCreate() {
  if (!newTitle.value.trim() || !newSbtImageCid.value.trim()) return;
  creating.value = true;
  globalMsg.value = "";
  try {
    const factory = await voting.getFactoryWriteContract();
    const tx = await factory.createElection(newTitle.value.trim(), newSbtImageCid.value.trim());
    globalMsg.value = "交易已发送，等待链上确认...";
    globalMsgOk.value = true;
    const receipt = await tx.wait();

    // 从事件日志中解析新合约地址
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

    globalMsg.value = newAddr
      ? `项目创建成功！合约地址：${newAddr}`
      : "项目创建成功！";
    globalMsgOk.value = true;
    newTitle.value = "";
    newSbtImageCid.value = "";
    await voting.loadElections();
    if (newAddr) {
      handleSelect(newAddr);
    }
  } catch (e) {
    let errMsg = "创建失败";
    const errStr = (e.code || "") + " " + (e.message || "");
    if (e.code === "ACTION_REJECTED" || errStr.includes("rejected") || errStr.includes("denied")) {
      errMsg = "交易被拒绝：请在 MetaMask 弹窗中点击「确认」来签署交易";
    } else if (errStr.includes("insufficient funds")) {
      errMsg = "账户 ETH 余额不足，请先获取 Sepolia 测试币";
    } else if (errStr.includes("network") || errStr.includes("connect")) {
      errMsg = "网络连接失败，请检查网络并刷新页面";
    } else if (e.reason) {
      errMsg = e.reason;
    } else if (e.message) {
      errMsg = e.message;
    }
    globalMsg.value = errMsg;
    globalMsgOk.value = false;
  } finally {
    creating.value = false;
  }
}

// ==================== 选择项目 ====================
async function handleSelect(addr) {
  resetDeploymentState();
  selectedAddr.value = addr;
  const el = voting.elections.find(e => e.address === addr);
  selectedTitle.value = el ? el.title : "";
  voting.selectElection(addr);
  await checkAdmin();
  await loadData();
  await loadVoterStats();
  await loadTransactionLogs();
  await loadSecurityLogs();
}

async function checkAdmin() {
  if (!wallet.address || !selectedAddr.value) {
    isAdmin.value = false;
    return;
  }
  try {
    const contract = getReadContract(selectedAddr.value);
    const adminAddr = await contract.admin();
    isAdmin.value = adminAddr.toLowerCase() === wallet.address.toLowerCase();
  } catch (e) {
    console.error("检查管理员失败:", e);
    isAdmin.value = false;
  }
}

async function loadData() {
  if (!selectedAddr.value) return;
  try {
    const contract = getReadContract(selectedAddr.value);
    const [st, all, startTsRaw, endTsRaw] = await Promise.all([
      contract.getVotingStatus(),
      contract.getAllCandidates(),
      contract.votingStartTime(),
      contract.votingEndTime(),
    ]);
    status.started = st[0];
    status.ended = st[1];

    const chainStartTs = Number(startTsRaw);
    const chainEndTs = Number(endTsRaw);
    if (chainStartTs > 0 && chainEndTs > 0) {
      deployed.value = true;
      deployedStartTs.value = chainStartTs;
      deployedEndTs.value = chainEndTs;
      startTime.value = toDatetimeLocal(chainStartTs);
      endTime.value = toDatetimeLocal(chainEndTs);
    } else {
      deployed.value = false;
      deployedStartTs.value = 0;
      deployedEndTs.value = 0;
    }

    const [names, cids, votes] = all;
    candidates.value = names.map((n, i) => ({
      name: n,
      cid: cids[i],
      votes: Number(votes[i]),
    }));
    status.candidates = candidates.value.length;
  } catch (e) {
    console.error("加载数据失败:", e);
  }
}

// ==================== 候选人操作 ====================
async function handleBatchAdd(items) {
  if (!items.length) return;
  submitting.value = true;
  message.value = "";
  try {
    const contract = await getWriteContract(selectedAddr.value);
    const names = items.map(i => i.name.trim());
    const cids = items.map(i => i.cid.trim());
    const manifestoCids = items.map(i => i.manifestoCid.trim());

    let tx;
    if (items.length === 1) {
      tx = await contract.addCandidate(names[0], cids[0], manifestoCids[0]);
    } else {
      tx = await contract.addCandidatesBatch(names, cids, manifestoCids);
    }

    message.value = `交易已发送（${items.length} 个候选人），等待链上确认...`;
    messageOk.value = true;

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "ADD_CANDIDATES",
      status: "pending"
    });

    const receipt = await tx.wait();

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "ADD_CANDIDATES",
      gas_used: Number(receipt.gasUsed),
      total_cost: receipt.fee.toString(),
      status: "success"
    });

    message.value = `成功添加 ${items.length} 个候选人！`;
    candidateResetKey.value += 1;
    await loadData();
    await loadTransactionLogs();
  } catch (e) {
    message.value = e.reason || e.message || "添加失败";
    messageOk.value = false;
  } finally {
    submitting.value = false;
  }
}

// ==================== 选民管理 ====================
async function loadVoterStats() {
  try {
    const data = await getVotersCount(selectedAddr.value);
    voterStats.total = data.total_registered;
    voterStats.claimed = data.total_claimed;
  } catch (e) {
    console.error("获取选民统计失败:", e);
  }
}

async function handleExcelImport(file) {
  if (!file) return;

  voterSubmitting.value = true;
  voterMessage.value = "Excel 正在导入中...";
  voterMessageOk.value = true;

  try {
    const res = await uploadVotersExcel(selectedAddr.value, file);
    if (res.success) {
      voterMessage.value = res.message;
      voterMessageOk.value = true;
      if (res.errors && res.errors.length > 0) {
        voterMessage.value += ` (部分错误: ${res.errors.join('; ')})`;
        voterMessageOk.value = false;
      }
    } else {
      voterMessage.value = res.message || "导入失败";
      voterMessageOk.value = false;
    }
  } catch (e) {
    voterMessage.value = `导入失败: ${e.response?.data?.detail || e.message}`;
    voterMessageOk.value = false;
  } finally {
    voterSubmitting.value = false;
    await loadVoterStats();
  }
}

async function handleBatchRegister(items) {
  if (!items.length) return;

  voterSubmitting.value = true;
  voterMessage.value = "";
  let success = 0;
  let failed = 0;
  const errors = [];

  for (const v of items) {
    try {
      await registerVoter(v.studentId.trim(), v.password.trim(), selectedAddr.value);
      success++;
    } catch (e) {
      failed++;
      const detail = e.response?.data?.detail || e.message;
      errors.push(`${v.studentId}: ${detail}`);
    }
  }

  if (failed === 0) {
    voterMessage.value = `成功注册 ${success} 个选民！`;
    voterMessageOk.value = true;
    voterResetKey.value += 1;
  } else {
    voterMessage.value = `成功 ${success} 个，失败 ${failed} 个：${errors.join("；")}`;
    voterMessageOk.value = false;
  }

  await loadVoterStats();
  voterSubmitting.value = false;
}

async function loadTransactionLogs() {
  loadingTxLogs.value = true;
  try {
    const data = await getTransactionLogs(selectedAddr.value);
    transactionLogs.value = data.logs || [];
  } catch (e) {
    console.error("加载交易日志失败:", e);
    transactionLogs.value = [];
  } finally {
    loadingTxLogs.value = false;
  }
}

async function loadSecurityLogs() {
  loadingSecLogs.value = true;
  try {
    const data = await getSecurityLogs(selectedAddr.value);
    securityLogs.value = data.logs || [];
    
    securityLogStats.total = data.total || 0;
    securityLogStats.warning = securityLogs.value.filter(l => l.severity === "warning").length;
    securityLogStats.critical = securityLogs.value.filter(l => l.severity === "critical").length;
  } catch (e) {
    console.error("加载安全日志失败:", e);
    securityLogs.value = [];
    securityLogStats.total = 0;
    securityLogStats.warning = 0;
    securityLogStats.critical = 0;
  } finally {
    loadingSecLogs.value = false;
  }
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await voting.loadElections();
});

watch(() => wallet.address, async () => {
  await voting.loadElections();
  if (selectedAddr.value) {
    await checkAdmin();
  }
});
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background-color: #f5f7fa;
}
.admin-sidebar {
  background-color: #1E222D;
  display: flex;
  flex-direction: column;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background-color: #161923;
  border-bottom: 1px solid #2C303F;
}
.sidebar-menu {
  border-right: none;
  flex: 1;
}
.admin-header {
  background-color: #fff;
  border-bottom: 1px solid #ebedf0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  align-items: center;
}
.admin-main {
  padding: 24px;
}

.alert {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  background: white;
}
.alert-error {
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
}

.context-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.data-card {
  display: flex;
  align-items: center;
  border-radius: 8px;
  margin-bottom: 24px;
}
.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 16px;
  float: left;
}
.card-info {
  display: flex;
  flex-direction: column;
}
.card-info .label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 4px;
}
.card-info .value {
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.section-card {
  margin-bottom: 24px;
  border-radius: 8px;
}
</style>
"""

with open(r"\\wsl.localhost\Ubuntu-20.04\home\mike\BlockChainVote\frontend\src\views\AdminView.vue", "w", encoding="utf-8") as f:
    f.write(file_content)
print("Updated successfully")
