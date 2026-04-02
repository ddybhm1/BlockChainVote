<template>
  <div class="admin-view">
    <div class="card">
      <h2>⚙️ 管理员面板</h2>
      <p class="desc">基于工厂模式：创建独立投票项目，每个项目拥有独立合约。</p>

      <AdminAccessPanel
        :wallet-address="wallet.address"
        :wallet-loading="wallet.loading"
        :is-factory-owner="wallet.isFactoryOwner"
        @connect="wallet.connect()"
        @disconnect="wallet.disconnect()"
      />

      <template v-if="wallet.address && wallet.isFactoryOwner">
        <!-- 全局消息 -->
        <div v-if="globalMsg" :class="['alert', globalMsgOk ? 'alert-success' : 'alert-error']">
          {{ globalMsg }}
        </div>

        <AdminProjectSidebar
          :title="newTitle"
          :creating="creating"
          :elections="myElections"
          :selected-addr="selectedAddr"
          @update:title="newTitle = $event"
          @create="handleCreate"
          @select="handleSelect"
        />

        <!-- ==================== 选中项目操作面板 ==================== -->
        <template v-if="selectedAddr">
          <div class="section selected-header">
            <h3>📋 当前项目：{{ selectedTitle }}</h3>
            <div class="el-addr-full">合约地址：{{ selectedAddr }}</div>
          </div>

          <div v-if="!isAdmin" class="alert alert-error">
            当前钱包地址不是该项目的管理员，无法操作
          </div>

          <div v-else>
            <!-- 投票状态 -->
            <div class="status-bar">
              <span>投票状态：</span>
              <span v-if="!status.started" class="badge badge-warn">未开始</span>
              <span v-else-if="!status.ended" class="badge badge-ok">进行中</span>
              <span v-else class="badge badge-error">投票已经结束</span>
              <span style="margin-left:12px">候选人数：{{ status.candidates }}</span>
            </div>

            <!-- 操作消息 -->
            <div v-if="message" :class="['alert', messageOk ? 'alert-success' : 'alert-error']">
              {{ message }}
            </div>

            <AdminCandidateManager
              :status-started="status.started"
              :submitting="submitting"
              :candidates="candidates"
              :reset-key="candidateResetKey"
              @submit="handleBatchAdd"
            />

            <!-- 投票控制 -->
            <div class="section control-section">
              <div class="control-header">
                <h3>投票控制</h3>
              </div>
              <div class="time-inputs" style="margin-bottom:12px;display:flex;gap:16px;align-items:center;">
                <label>开始时间：
                  <input type="datetime-local" v-model="startTime" :disabled="submitting || deployed" style="margin-left:4px;" />
                </label>
                <label>截止时间：
                  <input type="datetime-local" v-model="endTime" :disabled="submitting || deployed" style="margin-left:4px;" />
                </label>
              </div>
              <div v-if="deployed" class="alert alert-info" style="margin-top:0;">
                当前项目已部署投票窗口时间，不能更改。
              </div>
              <div class="btn-group">
                <button
                  class="btn btn-primary"
                  :disabled="deployed || submitting || !candidates.length || !startTime || !endTime"
                  @click="handleSaveVotingTime"
                >
                  {{ submitting ? '部署中...' : (deployed ? '部署成功' : '部署') }}
                </button>
              </div>
            </div>

            <AdminVoterManager
              :submitting="voterSubmitting"
              :message="voterMessage"
              :message-ok="voterMessageOk"
              :voter-stats="voterStats"
              :reset-key="voterResetKey"
              @submit="handleBatchRegister"
              @import-excel="handleExcelImport"
            />

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
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ethers } from "ethers";
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

const startTime = ref("");
const endTime = ref("");
const deployed = ref(false);
const deployedStartTs = ref(0);
const deployedEndTs = ref(0);

const wallet = useWalletStore();
const voting = useVotingStore();

// 创建项目
const newTitle = ref("");
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
  if (!newTitle.value.trim()) return;
  creating.value = true;
  globalMsg.value = "";
  try {
    const factory = await voting.getFactoryWriteContract();
    const tx = await factory.createElection(newTitle.value.trim());
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
    await voting.loadElections();
    if (newAddr) {
      handleSelect(newAddr);
    }
  } catch (e) {
    // 更详细的错误信息处理
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
  // 切换项目时自动加载对应日志
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

    // 记录交易日志（Pending）
    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "ADD_CANDIDATES",
      status: "pending"
    });

    const receipt = await tx.wait();

    // 更新记录（Success）
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
    
    // 统计日志
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
  // 不再初始加载钱包余额
});

watch(() => wallet.address, async () => {
  await voting.loadElections();
  if (selectedAddr.value) {
    await checkAdmin();
  }
});
</script>

<style scoped>
.admin-view {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease-out;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.card {
  padding: 32px;
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: var(--radius);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

.card h2 {
  font-size: 28px;
  margin: 0 0 12px;
  font-weight: 800;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 12px;
}

.desc {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.section {
  padding: 24px;
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.section:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.selected-header {
  background: linear-gradient(to right, #f8fafc, #ffffff);
  border-left: 4px solid var(--primary);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-header h3 {
  margin: 0;
  font-size: 20px;
  color: var(--primary);
  font-weight: 700;
}

.el-addr-full {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 14px;
  color: #4b5563;
  word-break: break-all;
  background: rgba(255,255,255,0.8);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: var(--radius);
  margin-bottom: 24px;
  font-weight: 500;
}

.badge {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.badge-warn {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}
.badge-ok {
  background: #dcfce3;
  color: #047857;
  border: 1px solid #bbf7d0;
}
.badge-error {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.control-section {
  background: #fafafa;
}

.control-header h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: #111827;
  font-weight: 600;
}

.time-inputs label {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 14px;
  color: #4b5563;
}

.time-inputs input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: all 0.2s;
  background: white;
}
.time-inputs input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}
.time-inputs input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.btn-group {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}
</style>
