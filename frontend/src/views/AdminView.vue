<template>
  <el-container class="admin-layout">
    <!-- Sidebar -->
    <el-aside width="250px" class="admin-sidebar">
      <div class="sidebar-logo">
        <el-icon :size="24" color="#fff" style="margin-right: 8px"><Monitor /></el-icon>
        <span style="color:#fff;font-weight:600;font-size:16px;">{{ isCreatorMode ? '自治投票站' : '电子投票控制台' }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1E222D"
        text-color="#A3A6B0"
        active-text-color="#fff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="project-board">
          <el-icon><DataLine /></el-icon>
          <span>管理项目</span>
        </el-menu-item>
        <el-menu-item index="create-project">
          <el-icon><FolderOpened /></el-icon>
          <span>创建新项目</span>
        </el-menu-item>
        <el-menu-item index="candidates">
          <el-icon><UserFilled /></el-icon>
          <span>候选人管理</span>
        </el-menu-item>
        <el-menu-item index="voters">
          <el-icon><Tickets /></el-icon>
          <span>选票管理</span>
        </el-menu-item>
        <el-menu-item v-if="!isCreatorMode" index="logs">
          <el-icon><List /></el-icon>
          <span>交易与安全</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- Header -->
      <el-header class="admin-header">
        <div class="header-left" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ isCreatorMode ? '自治投票站' : '管理面板' }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ activeMenuName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main class="admin-main">
        <div v-if="accessDenied" class="alert alert-error">
          <el-empty :description="accessDeniedText" />
        </div>
        <div v-else>
          <!-- Global Message -->
          <el-alert v-if="globalMsg" :title="globalMsg" :type="globalMsgOk ? 'success' : 'error'" show-icon style="margin-bottom: 20px" />

          <!-- Context Selector -->
          <el-card shadow="hover" class="context-card" v-if="activeMenu !== 'project-board' && activeMenu !== 'create-project'">
             <div style="display: flex; justify-content: space-between; align-items: center;">
               <div style="display: flex; align-items: center;">
                 <span style="font-weight:bold;margin-right:12px;">当前管理项目</span>
                 <el-tag v-if="selectedTitle" type="primary" size="large" style="margin-right:12px;">{{ selectedTitle }}</el-tag>
                 <el-tag v-else type="info" size="large" style="margin-right:12px;">未选择</el-tag>
                 <span v-if="selectedAddr" style="font-family:monospace; color:#6b7280; font-size:13px; margin-right:12px;">{{ selectedAddr }}</span>
                 <el-tag :type="status.ended ? 'danger' : (status.started ? 'success' : 'warning')" v-if="selectedAddr">
                   {{ status.ended ? '已结束' : (status.started ? '进行中' : '未开始') }}
                 </el-tag>
               </div>
             </div>
          </el-card>

          <!-- Warning for empty project -->
          <el-alert v-if="activeMenu !== 'project-board' && activeMenu !== 'create-project' && !selectedAddr" 
                    title="请先在【管理项目】中选中一个项目，然后再进行对应数据管理" 
                    type="warning" show-icon style="margin-bottom: 20px" />

          <!-- 1. Project Board -->
          <div v-show="activeMenu === 'project-board'">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-card shadow="hover" :class="['data-card', 'clickable-card', { 'active-module': activeProjectModule === 'all' }]" @click="selectProjectModule('all')">
                  <div class="card-icon" style="background:#EEF2FF;color:#4F46E5;"><el-icon><DataLine /></el-icon></div>
                  <div class="card-info">
                    <div class="label">{{ isCreatorMode ? '我的项目' : '所有项目' }}</div>
                    <div class="value">{{ dashboardStats.total }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" :class="['data-card', 'clickable-card', { 'active-module': activeProjectModule === 'not_started' }]" @click="selectProjectModule('not_started')">
                  <div class="card-icon" style="background:#FAECD8;color:#E6A23C;"><el-icon><FolderOpened /></el-icon></div>
                  <div class="card-info">
                    <div class="label">未开始的投票项目</div>
                    <div class="value">{{ dashboardStats.notStarted }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" :class="['data-card', 'clickable-card', { 'active-module': activeProjectModule === 'in_progress' }]" @click="selectProjectModule('in_progress')">
                  <div class="card-icon" style="background:#E1F3D8;color:#67C23A;"><el-icon><VideoPlay /></el-icon></div>
                  <div class="card-info">
                    <div class="label">已开始的投票项目</div>
                    <div class="value">{{ dashboardStats.inProgress }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover" :class="['data-card', 'clickable-card', { 'active-module': activeProjectModule === 'ended' }]" @click="selectProjectModule('ended')">
                  <div class="card-icon" style="background:#D9ECFF;color:#409EFF;"><el-icon><DataLine /></el-icon></div>
                  <div class="card-info">
                    <div class="label">已结束的投票项目</div>
                    <div class="value">{{ dashboardStats.ended }}</div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-card shadow="hover" class="context-card" style="margin-bottom: 20px;">
              <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                <span style="font-weight: 700;">按模块筛选项目</span>
                <el-input
                  v-model="globalSearchQuery"
                  placeholder="搜索项目名称或合约地址..."
                  style="max-width: 320px;"
                  clearable
                />
              </div>
            </el-card>

            <div style="margin-bottom:20px;">
              <AdminProjectSidebar
                :elections="paginatedProjects"
                :selected-addr="selectedAddr"
                :project-statuses="projectStatuses"
                :project-times="projectTimes"
                search-query=""
                @select="handleSelect"
              />
            </div>

            <el-card shadow="hover" class="section-card" v-if="selectedAddr">
              <template #header>
                <div style="font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
                  <span>继续设置并启动项目</span>
                  <el-tag :type="deployed ? 'success' : 'warning'" size="small">
                    {{ deployed ? '已设置时间' : '未设置时间' }}
                  </el-tag>
                </div>
              </template>

              <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <el-tag v-if="selectedTitle" type="info" size="large">{{ selectedTitle }}</el-tag>
                <span style="font-family: monospace; color: #6b7280; font-size: 12px;">{{ selectedAddr }}</span>
              </div>

              <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-top: 14px;">
                <el-date-picker
                  v-model="startTime"
                  type="datetime"
                  placeholder="开票时间"
                  :disabled="submitting || deployed"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                />
                <span style="color:#909399">至</span>
                <el-date-picker
                  v-model="endTime"
                  type="datetime"
                  placeholder="截止时间"
                  :disabled="submitting || deployed"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                />
                <el-button
                  type="primary"
                  :disabled="submitting || deployed || !startTime || !endTime"
                  @click="handleSaveVotingTime"
                >
                  {{ submitting ? '启动中...' : '设置时间并启动项目' }}
                </el-button>
              </div>

              <el-alert
                v-if="deployed"
                title="该项目已完成时间设置并正式启动。"
                type="success"
                show-icon
                :closable="false"
                style="margin-top: 12px;"
              />
              <el-alert
                v-else
                title="即使中途退出创建流程，也可以在这里补设开始/结束时间并启动项目。"
                type="warning"
                show-icon
                :closable="false"
                style="margin-top: 12px;"
              />
            </el-card>

            <div style="display: flex; justify-content: flex-end; margin-top: 12px;" v-if="filteredProjects.length > 5">
              <el-pagination
                v-model:current-page="projectPage"
                :page-size="5"
                layout="prev, pager, next, total"
                :total="filteredProjects.length"
              />
            </div>
          </div>

          <!-- 2. Create Project -->
          <div v-show="activeMenu === 'create-project'">
            <el-card shadow="hover" class="section-card">
              <template #header>
                <div style="font-weight: bold;">创建新项目</div>
              </template>
              <div style="display: grid; gap: 14px; max-width: 680px;">
                <el-alert
                  :title="factoryPaused ? '平台当前已暂停创建新项目，请稍后再试。' : `当前开站费：${createFeeText}（不含 Gas）`"
                  :type="factoryPaused ? 'warning' : 'info'"
                  show-icon
                  :closable="false"
                />
                <el-input v-model="newTitle" placeholder="输入项目名称（例如：第十二届学生会主席投票）" clearable />
                <div style="display: flex; align-items: center; gap: 10px;">
                  <el-input v-model="newSbtImageCid" placeholder="输入项目 SBT 图片 CID（IPFS）" clearable />
                  <label class="upload-chip" :class="{ disabled: sbtImageUploading }" title="上传图片到 IPFS 并自动填入 CID">
                    <span v-if="sbtImageUploading">上传中...</span>
                    <span v-else>上传图片</span>
                    <input
                      type="file"
                      accept="image/*"
                      class="file-hidden"
                      :disabled="sbtImageUploading"
                      @change="handleUploadSbtImage"
                    />
                  </label>
                </div>
                <div>
                  <el-button type="primary" :loading="creating" :disabled="creating || factoryPaused || !newTitle.trim() || !newSbtImageCid.trim()" @click="handleCreate">
                    {{ creating ? '创建中...' : '创建新项目' }}
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 3. Candidates -->
          <div v-show="activeMenu === 'candidates' && selectedAddr">
            <div v-if="message" class="alert" :class="messageOk ? 'alert-success' : 'alert-error'" style="margin-bottom: 12px">
              {{ message }}
            </div>
            <AdminCandidateManager
              :candidates="candidatesList"
              :status-started="status.started"
              :submitting="submitting"
              :reset-key="candidateResetKey"
              @submit="handleBatchAdd"
            />
          </div>

          <!-- 4. Voters -->
          <div v-show="activeMenu === 'voters' && selectedAddr">
            <div v-if="voterMessage" class="alert" :class="voterMessageOk ? 'alert-success' : 'alert-error'" style="margin-bottom: 12px">
              {{ voterMessage }}
            </div>
            <AdminVoterManager
              :voter-stats="voterStats"
              :submitting="voterSubmitting"
              :reset-key="voterResetKey"
              @submit="handleBatchRegister"
              @import-excel="handleExcelImport"
            />
          </div>

          <!-- 5. Logs Console -->
          <div v-if="!isCreatorMode" v-show="activeMenu === 'logs' && selectedAddr">
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
import { useRoute, useRouter } from "vue-router";
import { Monitor, DataLine, FolderOpened, UserFilled, Tickets, List, VideoPlay, User, Cpu, WarnTriangleFilled } from '@element-plus/icons-vue';

import AdminLogsPanel from "../components/admin/AdminLogsPanel.vue";
import AdminProjectSidebar from "../components/admin/AdminProjectSidebar.vue";
import AdminCandidateManager from "../components/admin/AdminCandidateManager.vue";
import AdminVoterManager from "../components/admin/AdminVoterManager.vue";
import { useWalletStore } from "../stores/wallet.js";
import { useVotingStore } from "../stores/voting.js";
import { ELECTION_ABI } from "../services/contract.js";
import { 
  getTransactionLogs,
  getSecurityLogs,
  logTransaction,
  uploadToIPFS,
  syncElectionToBackend,
  getVotersCount,
  uploadVotersExcel,
  registerVoter
} from "../services/api.js";

// Layout state
const activeMenu = ref('project-board');
const route = useRoute();
const router = useRouter();
const isCreatorMode = computed(() => route.path?.startsWith('/creator'));
const activeMenuName = computed(() => {
  const map = {
    'project-board': '管理项目',
    'create-project': '创建新项目',
    candidates: '候选人管理',
    voters: '选票管理',
    logs: '交易与安全'
  };
  if (isCreatorMode.value && activeMenu.value === 'logs') return '项目治理';
  return map[activeMenu.value] || '管理项目';
});

function handleMenuSelect(index) {
  if (index === "create-project") {
    router.push(isCreatorMode.value ? '/creator/create/step1' : '/admin/create/step1');
    return;
  }
  activeMenu.value = index;
}

const startTime = ref("");
const endTime = ref("");
const deployed = ref(false);
const deployedStartTs = ref(0);
const deployedEndTs = ref(0);

const wallet = useWalletStore();
const voting = useVotingStore();

const showCreateForm = ref(false);
const globalSearchQuery = ref("");
const activeProjectModule = ref("all");
const projectPage = ref(1);

function selectProjectModule(module) {
  activeProjectModule.value = module;
  projectPage.value = 1;
}

// ==================== 项目与表单状态 ====================
// 选中项目
const selectedAddr = ref("");
const selectedTitle = ref("");
const isAdmin = ref(false);
const status = reactive({ started: false, ended: false, candidates: 0 });

const newTitle = ref("");
const newSbtImageCid = ref("");
const sbtImageUploading = ref(false);
const createFeeWei = ref(0n);
const factoryPaused = ref(false);
const creating = ref(false);
const globalMsg = ref("");
const globalMsgOk = ref(true);
const submitting = ref(false);
const message = ref("");
const messageOk = ref(false);

// ==================== 候选人与选民状态 ====================
const candidatesList = ref([]);
const candidateResetKey = ref(0);

const voterStats = reactive({ total: 0, claimed: 0 });
const voterSubmitting = ref(false);
const voterMessage = ref("");
const voterMessageOk = ref(false);
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

// 当前工厂合约下的所有子合约项目
const factoryElections = computed(() => voting.elections || []);
const managedElections = computed(() => {
  if (!isCreatorMode.value) return factoryElections.value;
  const me = (wallet.address || '').toLowerCase();
  return factoryElections.value.filter((e) => (e.creator || '').toLowerCase() === me);
});
const createFeeText = computed(() => `${ethers.formatEther(createFeeWei.value)} ETH`);
const accessDenied = computed(() => !wallet.address || (!isCreatorMode.value && !wallet.isFactoryOwner));
const accessDeniedText = computed(() => {
  if (!wallet.address) return "请先通过顶部 Wallet Connect 连接钱包后再进入控制台";
  if (!isCreatorMode.value) return "管理员中心仅通过钱包地址认证，请连接具有管理员权限的钱包";
  return "请先连接钱包";
});

const dashboardStats = reactive({
  total: 0,
  notStarted: 0,
  inProgress: 0,
  ended: 0
});

const projectStatuses = reactive({});
const projectTimes = reactive({});

async function loadDashboardStats() {
  let notStarted = 0;
  let inProgress = 0;
  let ended = 0;
  
  const now = Math.floor(Date.now() / 1000);
  
  if (managedElections.value && managedElections.value.length > 0) {
    for (const e of managedElections.value) {
      try {
        const contract = getReadContract(e.address);
        const [startTsRaw, endTsRaw] = await Promise.all([
          contract.votingStartTime(),
          contract.votingEndTime(),
        ]);
        const startTs = Number(startTsRaw);
        const endTs = Number(endTsRaw);
        
        let s = 'not_started';
        if (startTs === 0 && endTs === 0) {
          s = 'not_started';
          notStarted++;
        } else if (now < startTs) {
          s = 'not_started';
          notStarted++;
        } else if (now >= startTs && now <= endTs) {
          s = 'in_progress';
          inProgress++;
        } else {
          s = 'ended';
          ended++;
        }
        
        projectStatuses[e.address] = s;
        projectTimes[e.address] = { start: startTs, end: endTs };
      } catch (err) {
        console.error("加载项目状态失败:", err);
        projectStatuses[e.address] = 'error';
      }
    }
  }
  
  dashboardStats.total = managedElections.value.length;
  dashboardStats.notStarted = notStarted;
  dashboardStats.inProgress = inProgress;
  dashboardStats.ended = ended;
}

watch([factoryElections, () => wallet.address, isCreatorMode], () => {
  loadDashboardStats();
}, { immediate: true });

const filteredProjects = computed(() => {
  const normalizedQuery = globalSearchQuery.value.trim().toLowerCase();

  let list = managedElections.value.filter((e) => {
    const status = projectStatuses[e.address] || "loading";
    if (activeProjectModule.value === "all") return true;
    return status === activeProjectModule.value;
  });

  if (!normalizedQuery) return list;

  return list.filter((e) => {
    const title = (e.title || "").toLowerCase();
    const addr = (e.address || "").toLowerCase();
    return title.includes(normalizedQuery) || addr.includes(normalizedQuery);
  });
});

const paginatedProjects = computed(() => {
  const start = (projectPage.value - 1) * 5;
  return filteredProjects.value.slice(start, start + 5);
});

watch([activeProjectModule, globalSearchQuery], () => {
  projectPage.value = 1;
});

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

    const targetAddr = selectedAddr.value;
    const targetTitle = selectedTitle.value || (voting.elections.find((e) => e.address === targetAddr)?.title || "");

    const writeContract = await getWriteContract(targetAddr);
    const tx = await writeContract.startVoting(startTs, endTs);
    const receipt = await tx.wait();
    if (receipt.status !== 1) {
      throw new Error("链上设置投票时间失败");
    }

    await syncElectionToBackend(targetAddr, targetTitle, startTs, endTs);

    deployed.value = true;
    deployedStartTs.value = startTs;
    deployedEndTs.value = endTs;
    startTime.value = toDatetimeLocal(startTs);
    endTime.value = toDatetimeLocal(endTs);
    message.value = '部署成功，区块链将自动控制投票窗口。TxHash: ' + (tx.hash || '');
    messageOk.value = true;
    await voting.loadElections();
    await loadDashboardStats();
    await loadData();
    await voting.selectElection(targetAddr);
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
    const fee = await factory.createFee();
    const isPaused = await factory.paused();
    if (isPaused) throw new Error("平台当前暂停了新项目创建");
    const tx = await factory.createElection(newTitle.value.trim(), newSbtImageCid.value.trim(), { value: fee });
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

async function handleUploadSbtImage(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  sbtImageUploading.value = true;
  globalMsg.value = "";

  try {
    const result = await uploadToIPFS(file, { purpose: "image" });
    newSbtImageCid.value = result.cid;
    globalMsg.value = "项目图片已上传到 IPFS，CID 已自动填入。";
    globalMsgOk.value = true;
  } catch (e) {
    globalMsg.value = `项目图片上传失败：${e.response?.data?.detail || e.message}`;
    globalMsgOk.value = false;
  } finally {
    sbtImageUploading.value = false;
    event.target.value = "";
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
  if (!isCreatorMode.value) {
    await loadTransactionLogs();
    await loadSecurityLogs();
  }
}

async function loadFactoryPolicy() {
  try {
    const factory = voting.getFactoryReadContract();
    const [fee, paused] = await Promise.all([factory.createFee(), factory.paused()]);
    createFeeWei.value = fee;
    factoryPaused.value = paused;
  } catch (e) {
    console.warn('读取工厂费率/暂停状态失败', e);
    createFeeWei.value = 0n;
    factoryPaused.value = false;
  }
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

    const [names, cids, manifestoCids, votes] = all;
    status.candidates = names.length;
    
    candidatesList.value = names.map((n, i) => ({
      name: n,
      cid: cids[i],
      manifestoCid: manifestoCids[i],
      votes: Number(votes[i]),
      isActive: true
    }));
  } catch (e) {
    console.error("加载数据失败:", e);
  }
}

// ==================== 候选人与选民管理 ====================
async function handleBatchAdd(items) {
  if (!items.length) return;
  const targetAddr = selectedAddr.value;
  if (!targetAddr) {
    message.value = "请先选择项目";
    messageOk.value = false;
    return;
  }

  submitting.value = true;
  message.value = "";
  try {
    const contract = await getWriteContract(targetAddr);
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
      election_address: targetAddr,
      operation_type: "ADD_CANDIDATES",
      status: "pending"
    });

    const receipt = await tx.wait();

    await logTransaction({
      tx_hash: tx.hash,
      election_address: targetAddr,
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

async function loadVoterStats() {
  const targetAddr = selectedAddr.value;
  if (!targetAddr) return;

  try {
    const data = await getVotersCount(targetAddr);
    voterStats.total = data.total_registered;
    voterStats.claimed = data.total_claimed;
  } catch (e) {
    console.error("获取选民统计失败:", e);
  }
}

async function handleExcelImport(file) {
  if (!file) return;

  const targetAddr = selectedAddr.value;
  if (!targetAddr) {
    voterMessage.value = "请先选择项目";
    voterMessageOk.value = false;
    return;
  }

  voterSubmitting.value = true;
  voterMessage.value = "Excel 正在导入中...";
  voterMessageOk.value = true;

  try {
    const res = await uploadVotersExcel(targetAddr, file);
    if (res.success) {
      voterMessage.value = res.message;
      voterMessageOk.value = true;
      if (res.errors && res.errors.length > 0) {
        voterMessage.value += ` (部分错误: ${res.errors.join('; ')})`;
        voterMessageOk.value = false;
      }
      voterResetKey.value += 1;
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

  const targetAddr = selectedAddr.value;
  if (!targetAddr) {
    voterMessage.value = "请先选择项目";
    voterMessageOk.value = false;
    return;
  }

  voterSubmitting.value = true;
  voterMessage.value = "";
  let success = 0;
  let failed = 0;
  const errors = [];

  for (const v of items) {
    try {
      await registerVoter(v.studentId.trim(), v.password.trim(), targetAddr);
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

// ==================== 监控日志 ====================
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
  await loadFactoryPolicy();
  
  if (route.query.menu && route.query.addr) {
    const menu = String(route.query.menu);
    if (menu === "overview") {
      activeMenu.value = "project-board";
    } else if (menu === "projects") {
      activeMenu.value = "project-board";
    } else if (menu === "create-project") {
      router.replace({ query: {} });
      router.push(isCreatorMode.value ? '/creator/create/step1' : '/admin/create/step1');
      return;
    } else {
      activeMenu.value = menu;
    }
    handleSelect(route.query.addr);
    router.replace({ query: {} }); // remove query after init
  }
});

watch(() => wallet.address, async () => {
  await voting.loadElections();
  await loadFactoryPolicy();
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

.clickable-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.clickable-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.active-module {
  border: 1px solid #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.18);
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

.upload-chip {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #1d4ed8;
  background: #dbeafe;
  border: 1px solid #93c5fd;
  cursor: pointer;
  white-space: nowrap;
}

.upload-chip.disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.file-hidden {
  display: none;
}
</style>
