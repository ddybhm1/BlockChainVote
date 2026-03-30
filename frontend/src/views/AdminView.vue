<template>
  <div class="admin-view">
    <div class="card">
      <h2>⚙️ 管理员面板</h2>
      <p class="desc">基于工厂模式：创建独立投票项目，每个项目拥有独立合约。</p>

      <!-- ==================== 钱包连接区域 ==================== -->
      <div class="wallet-section">
        <template v-if="!wallet.address">
          <div class="alert alert-info">
            <p>👛 <strong>需要连接钱包</strong></p>
            <p style="margin: 8px 0 0 0; font-size: 13px;">
              请连接您的 MetaMask 钱包来管理投票项目。只有工厂合约的拥有者才可以执行管理操作。
            </p>
            <button class="btn btn-primary" @click="wallet.connect()" :disabled="wallet.loading" style="margin-top: 12px;">
              {{ wallet.loading ? '连接中...' : '🦊 连接 MetaMask 钱包' }}
            </button>
          </div>
        </template>
        <template v-else>
          <div :class="['wallet-info', { 'is-owner': wallet.isFactoryOwner }]">
            <div class="wallet-header">
              <span class="wallet-badge">
                <span v-if="wallet.isFactoryOwner" class="badge-owner">👑 工厂拥有者</span>
                <span v-else class="badge-error">❌ 非拥有者</span>
              </span>
              <span class="wallet-address" :title="wallet.address">
                {{ wallet.address.slice(0, 6) }}...{{ wallet.address.slice(-4) }}
              </span>
            </div>
            <div v-if="!wallet.isFactoryOwner" class="alert alert-error">
              当前钱包地址不是工厂合约的拥有者，无法执行管理操作。请切换到拥有者账户。
            </div>
            <div v-else class="alert alert-success">
              ✓ 您是工厂合约的拥有者，可以创建和管理投票项目。
            </div>
            <button class="btn btn-secondary" @click="wallet.disconnect()" style="margin-top: 8px;">
              断开钱包
            </button>
          </div>
        </template>
      </div>

      <template v-if="wallet.address && wallet.isFactoryOwner">
        <!-- 全局消息 -->
        <div v-if="globalMsg" :class="['alert', globalMsgOk ? 'alert-success' : 'alert-error']">
          {{ globalMsg }}
        </div>

        <!-- ==================== 创建投票项目 ==================== -->
        <div class="section">
          <h3>🏭 创建新投票项目</h3>
          <div class="create-row">
            <input
              class="input-field"
              v-model="newTitle"
              placeholder="请输入投票项目名称"
              style="flex:1"
            />
            <button
              class="btn btn-primary"
              :disabled="creating || !newTitle.trim()"
              @click="handleCreate"
            >
              {{ creating ? '创建中...(等待链上确认)' : '创建项目' }}
            </button>
          </div>
        </div>

        <!-- ==================== 项目列表 ==================== -->
        <div class="section">
          <h3>📁 我的投票项目</h3>
          <div v-if="!myElections.length" class="alert alert-info">
            暂无投票项目。请先创建一个新项目。
          </div>
          <div v-else class="election-list">
            <div
              v-for="el in myElections"
              :key="el.address"
              :class="['election-item', { active: selectedAddr === el.address }]"
              @click="handleSelect(el.address)"
            >
              <div class="el-title">{{ el.title }}</div>
              <div class="el-meta">
                <span class="el-addr" :title="el.address">{{ el.address.slice(0, 10) }}...{{ el.address.slice(-6) }}</span>
                <span class="el-time">{{ formatTime(el.createdAt) }}</span>
              </div>
            </div>
          </div>
        </div>

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

            <!-- 批量添加候选人 -->
            <div class="section">
              <h3>📋 批量添加投票项目</h3>
              <template v-if="status.started">
                <div class="alert alert-info">
                  投票已开始，无法添加候选人。如需重新配置，请创建新项目。
                </div>
              </template>
              <template v-else>
                <div class="batch-list">
                  <div v-for="(item, idx) in batchItems" :key="idx" class="batch-row">
                    <input
                      class="input-field"
                      v-model="item.name"
                      placeholder="候选人名称"
                    />
                    <div class="cid-input-group">
                      <input
                        class="input-field"
                        v-model="item.cid"
                        :placeholder="item.uploading ? '上传中...' : 'IPFS CID 或点右侧上传'"
                        :disabled="item.uploading"
                      />
                      <label class="btn-icon btn-upload" :title="item.uploading ? '上传中...' : '上传文件到 IPFS'">
                        <span v-if="item.uploading" class="spinner"></span>
                        <span v-else>📁</span>
                        <input
                          type="file"
                          class="file-hidden"
                          @change="handleFileUpload($event, idx)"
                          :disabled="item.uploading"
                        />
                      </label>
                    </div>
                    <button
                      type="button"
                      class="btn-icon btn-remove"
                      @click="removeItem(idx)"
                      :disabled="batchItems.length <= 1"
                      title="删除"
                    >✕</button>
                  </div>
                </div>
                <div class="batch-actions">
                  <button type="button" class="btn btn-secondary" @click="addItem">
                    + 新增一行
                  </button>
                  <button
                    class="btn btn-primary"
                    :disabled="submitting || !hasValidItems"
                    @click="handleBatchAdd"
                  >
                    {{ submitting ? '提交中...(等待链上确认)' : `提交 ${validCount} 个候选人` }}
                  </button>
                </div>
              </template>
            </div>

            <!-- 已有候选人列表 -->
            <div v-if="candidates.length" class="section">
              <h3>已添加的候选人</h3>
              <table class="candidate-table">
                <thead>
                  <tr><th>ID</th><th>名称</th><th>CID</th><th>得票</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(c, i) in candidates" :key="i">
                    <td>{{ i }}</td>
                    <td>{{ c.name }}</td>
                    <td class="cid-cell">{{ c.cid }}</td>
                    <td>{{ c.votes }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

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

            <!-- 选民管理 -->
            <div class="section voter-management">
              <div class="section-header-row">
                <h3>👤 投票人员管理</h3>
                <div class="header-actions">
                  <label class="btn btn-excel" :class="{ 'btn-loading': voterSubmitting }" title="支持 .xlsx 格式，需包含“学号”和“初始密码”列">
                    <span v-if="voterSubmitting" class="spinner-small"></span>
                    <span v-else>📥</span>
                    Excel 一键导入
                    <input type="file" class="file-hidden" accept=".xlsx, .xls" @change="handleExcelImport" :disabled="voterSubmitting" />
                  </label>
                </div>
              </div>
              <div class="voter-stats" v-if="voterStats.total >= 0">
                已注册：<strong>{{ voterStats.total }}</strong> 人 ｜
                已领票（本项目）：<strong>{{ voterStats.claimed }}</strong> 人
              </div>

              <div class="batch-list">
                <div class="batch-header">
                  <span class="header-label">学号</span>
                  <span class="header-label">密码</span>
                  <span style="width:32px"></span>
                </div>
                <div v-for="(v, idx) in voterItems" :key="idx" class="batch-row">
                  <input
                    class="input-field"
                    v-model="v.studentId"
                    placeholder="学号"
                  />
                  <input
                    class="input-field"
                    v-model="v.password"
                    :placeholder="'密码'"
                  />
                  <button
                    type="button"
                    class="btn-icon btn-remove"
                    @click="removeVoter(idx)"
                    :disabled="voterItems.length <= 1"
                    title="删除"
                  >✕</button>
                </div>
              </div>
              <div class="batch-actions">
                <button type="button" class="btn btn-secondary" @click="addVoter">
                  + 新增一行
                </button>
                <button
                  class="btn btn-primary"
                  :disabled="voterSubmitting || !hasValidVoters"
                  @click="handleBatchRegister"
                >
                  {{ voterSubmitting ? '注册中...' : `注册 ${validVoterCount} 个选民` }}
                </button>
              </div>
              <div v-if="voterMessage" :class="['alert', voterMessageOk ? 'alert-success' : 'alert-error']" style="margin-top:12px">
                {{ voterMessage }}
              </div>
            </div>

            <!-- 财务与安全监控 -->
            <div class="section">
              <h3>系统监控日志看板</h3>
              
              <!-- 交易日志 -->
              <div class="subsection">
                <h4>📝 交易日志 (Gas 费用记录)</h4>
                <div class="log-controls">
                  <div class="log-stats">
                    总交易：<strong>{{ transactionLogs.length }}</strong> | 
                    平均 Gas：<strong>{{ avgGasUsed }}</strong>
                  </div>
                  <button class="btn btn-secondary" @click="loadTransactionLogs" :disabled="loadingTxLogs">
                    {{ loadingTxLogs ? '加载中...' : '刷新日志' }}
                  </button>
                </div>
                <div v-if="transactionLogs.length === 0" class="alert alert-info">
                  暂无交易日志
                </div>
                <div v-else class="table-container">
                  <table class="logs-table">
                    <thead>
                      <tr>
                        <th>操作类型</th>
                        <th>Gas 消耗</th>
                        <th>总费用 (Wei)</th>
                        <th>交易哈希</th>
                        <th>状态</th>
                        <th>时间</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="log in transactionLogs.slice(0, 15)" :key="log.id">
                        <td><strong>{{ log.operation_type }}</strong></td>
                        <td>{{ log.gas_used || '-' }}</td>
                        <td class="tx-cost" :title="log.total_cost">{{ formatWei(log.total_cost) }}</td>
                        <td class="tx-hash">
                          <a v-if="log.tx_hash" :href="'https://sepolia.etherscan.io/tx/' + log.tx_hash" target="_blank">
                            {{ log.tx_hash.slice(0, 10) }}...
                          </a>
                          <span v-else>-</span>
                        </td>
                        <td><span :class="['status-badge', 'status-' + log.status]">{{ log.status }}</span></td>
                        <td class="time-cell">{{ formatTime(log.created_at) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 安全日志 -->
              <div class="subsection">
                <h4>🔒 安全拦截日志</h4>
                <div class="log-controls">
                  <span class="log-stats">
                    总事件：<strong>{{ securityLogStats.total }}</strong> |
                    警告：<strong>{{ securityLogStats.warning }}</strong> |
                    严重：<strong>{{ securityLogStats.critical }}</strong>
                  </span>
                  <button class="btn btn-secondary" @click="loadSecurityLogs" :disabled="loadingSecLogs">
                    {{ loadingSecLogs ? '加载中...' : '刷新日志' }}
                  </button>
                </div>
                <div v-if="securityLogs.length === 0" class="alert alert-info">
                  暂无安全事件
                </div>
                <table v-else class="logs-table">
                  <thead>
                    <tr>
                      <th>事件类型</th>
                      <th>学号/地址</th>
                      <th>详情</th>
                      <th>严重程度</th>
                      <th>时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="log in securityLogs.slice(0, 10)" :key="log.id" :class="'severity-' + log.severity">
                      <td><strong>{{ log.event_type }}</strong></td>
                      <td>{{ log.student_id || '-' }}</td>
                      <td class="details-cell">{{ log.details }}</td>
                      <td><span :class="['severity-badge', 'severity-' + log.severity]">{{ log.severity }}</span></td>
                      <td class="time-cell">{{ formatTime(log.created_at) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ethers } from "ethers";
import { useWalletStore } from "../stores/wallet.js";
import { useVotingStore } from "../stores/voting.js";
import { ELECTION_ABI } from "../services/contract.js";
import { 
  registerVoter, 
  getVotersCount,
  uploadVotersExcel,
  uploadToIPFS,
  getTransactionLogs,
  getSecurityLogs,
  logTransaction,
  logSecurity,
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

// 批量添加候选人
const batchItems = ref([
  { name: "", cid: "", uploading: false },
  { name: "", cid: "", uploading: false },
  { name: "", cid: "", uploading: false },
]);

function addItem() { batchItems.value.push({ name: "", cid: "", uploading: false }); }
function removeItem(idx) { if (batchItems.value.length > 1) batchItems.value.splice(idx, 1); }

const validItems = computed(() => batchItems.value.filter(i => i.name.trim() && i.cid.trim()));
const validCount = computed(() => validItems.value.length);
const hasValidItems = computed(() => validCount.value > 0);

// IPFS 文件上传
async function handleFileUpload(event, idx) {
  const file = event.target.files?.[0];
  if (!file) return;
  const item = batchItems.value[idx];
  item.uploading = true;
  try {
    const res = await uploadToIPFS(file);
    item.cid = res.cid;
  } catch (e) {
    message.value = `文件上传失败: ${e.response?.data?.detail || e.message}`;
    messageOk.value = false;
  } finally {
    item.uploading = false;
    event.target.value = "";
  }
}

// 选民管理
const voterItems = ref([
  { studentId: "", password: "" },
  { studentId: "", password: "" },
  { studentId: "", password: "" },
]);
const voterSubmitting = ref(false);
const voterMessage = ref("");
const voterMessageOk = ref(false);
const voterStats = reactive({ total: -1, claimed: 0 });

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

function formatWei(weiStr) {
  if (!weiStr) return "-";
  try {
    const val = BigInt(weiStr);
    if (val < 1000000000n) return `${val} Wei`;
    return `${(Number(val) / 1e18).toFixed(6)} ETH`;
  } catch (e) {
    return weiStr;
  }
}

function addVoter() { voterItems.value.push({ studentId: "", password: "" }); }
function removeVoter(idx) { if (voterItems.value.length > 1) voterItems.value.splice(idx, 1); }

const validVoters = computed(() => voterItems.value.filter(v => v.studentId.trim() && v.password.trim()));
const validVoterCount = computed(() => validVoters.value.length);
const hasValidVoters = computed(() => validVoterCount.value > 0);

// 我创建的项目
const myElections = computed(() =>
  voting.elections.filter(e => e.creator.toLowerCase() === wallet.address?.toLowerCase())
);

function formatTime(ts) {
  if (!ts) return "";
  try {
    const numTs = Number(ts);
    if (!isNaN(numTs)) {
      // 若是10位级的时间戳（秒），转为毫秒
      const ms = numTs < 10000000000 ? numTs * 1000 : numTs;
      return new Date(ms).toLocaleString("zh-CN");
    }
    const date = new Date(ts);
    return date.toLocaleString("zh-CN");
  } catch (e) {
    return ts;
  }
}

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
async function handleBatchAdd() {
  const items = validItems.value;
  if (!items.length) return;
  submitting.value = true;
  message.value = "";
  try {
    const contract = await getWriteContract(selectedAddr.value);
    const names = items.map(i => i.name.trim());
    const cids = items.map(i => i.cid.trim());

    let tx;
    if (items.length === 1) {
      tx = await contract.addCandidate(names[0], cids[0]);
    } else {
      tx = await contract.addCandidatesBatch(names, cids);
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
    batchItems.value = [{ name: "", cid: "", uploading: false }, { name: "", cid: "", uploading: false }, { name: "", cid: "", uploading: false }];
    await loadData();
    await loadTransactionLogs();
  } catch (e) {
    message.value = e.reason || e.message || "添加失败";
    messageOk.value = false;
  } finally {
    submitting.value = false;
  }
}

async function handleStartVoting() {
  submitting.value = true;
  message.value = "";
  try {
    const contract = await getWriteContract(selectedAddr.value);
    // 转为秒级时间戳
    const start = Math.floor(new Date(startTime.value).getTime() / 1000);
    const end = Math.floor(new Date(endTime.value).getTime() / 1000);
    if (!start || !end || end <= start) {
      message.value = "请正确设置开始和截止时间";
      messageOk.value = false;
      submitting.value = false;
      return;
    }
    const tx = await contract.startVoting(start, end);
    message.value = "交易已发送，等待链上确认...";
    messageOk.value = true;

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "START_VOTING",
      status: "pending"
    });

    const receipt = await tx.wait();

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "START_VOTING",
      gas_used: Number(receipt.gasUsed),
      total_cost: receipt.fee.toString(),
      status: "success"
    });

    message.value = "投票已开始！";
    await loadData();
    await loadTransactionLogs();
  } catch (e) {
    message.value = e.reason || e.message || "操作失败";
    messageOk.value = false;
  } finally {
    submitting.value = false;
  }
}

async function handleEndVoting() {
  submitting.value = true;
  message.value = "";
  try {
    const contract = await getWriteContract(selectedAddr.value);
    const tx = await contract.endVoting();
    message.value = "交易已发送，等待链上确认...";
    messageOk.value = true;

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "END_VOTING",
      status: "pending"
    });

    const receipt = await tx.wait();

    await logTransaction({
      tx_hash: tx.hash,
      election_address: selectedAddr.value,
      operation_type: "END_VOTING",
      gas_used: Number(receipt.gasUsed),
      total_cost: receipt.fee.toString(),
      status: "success"
    });

    message.value = "投票已结束！";
    await loadData();
    await loadTransactionLogs();
  } catch (e) {
    message.value = e.reason || e.message || "操作失败";
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

async function handleExcelImport(event) {
  const file = event.target.files?.[0];
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
    event.target.value = ""; // 重置 input
  }
}

async function handleBatchRegister() {
  const items = validVoters.value;
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
    voterItems.value = [{ studentId: "", password: "" }, { studentId: "", password: "" }, { studentId: "", password: "" }];
  } else {
    voterMessage.value = `成功 ${success} 个，失败 ${failed} 个：${errors.join("；")}`;
    voterMessageOk.value = false;
  }

  await loadVoterStats();
  voterSubmitting.value = false;
}

// ==================== 监控日志 ====================

async function refreshBalance() {
  // 此功能已移除
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
.admin-view h2 { margin-bottom: 8px; }
.desc { color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; }

/* 钱包连接区域 */
.wallet-section {
  margin-bottom: 24px;
}
.wallet-section .alert {
  padding: 16px;
  border-radius: 8px;
  margin: 0;
}
.wallet-section .alert p {
  margin: 0;
}
.wallet-info {
  padding: 12px 16px;
  background: #f8f9fb;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 0;
}
.wallet-info.is-owner {
  background: #f0fdf4;
  border-color: #86efac;
}
.wallet-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}
.wallet-badge {
  display: flex;
  gap: 8px;
  align-items: center;
}
.badge-owner {
  display: inline-block;
  background: #fbbf24;
  color: #78350f;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.wallet-address {
  font-family: monospace;
  font-size: 13px;
  color: var(--text);
  flex: 1;
  text-align: right;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
}

/* 创建项目 */
.create-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 项目列表 */
.election-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.election-item {
  padding: 12px 16px;
  border: 2px solid var(--border, #e5e5e5);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.election-item:hover { border-color: var(--primary, #4f46e5); background: #f8f7ff; }
.election-item.active { border-color: var(--primary, #4f46e5); background: #eef2ff; }
.el-title { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
.el-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary, #888); }
.el-addr { font-family: monospace; }
.selected-header { padding-bottom: 0; }
.el-addr-full { font-size: 12px; color: var(--text-secondary); font-family: monospace; word-break: break-all; margin-top: 4px; }

.status-bar {
  padding: 12px 16px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.badge-warn { background: #fff3cd; color: #856404; }
.badge-ok { background: #d4edda; color: #155724; }
.badge-error { background: #f8d7da; color: #721c24; }
.section { margin-top: 24px; }
.section h3 { margin-bottom: 12px; font-size: 16px; margin-top: 0; }

.btn-excel {
  background-color: #217346; /* Excel Green */
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(33, 115, 70, 0.2);
}
.btn-excel:hover {
  background-color: #1a5c38;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(33, 115, 70, 0.3);
}
.btn-excel.btn-loading {
  opacity: 0.7;
  cursor: not-allowed;
}
.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: rgba(0, 0, 0, 0.02);
  padding: 10px 14px;
  border-radius: 8px;
  border-left: 4px solid var(--primary);
}

.batch-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}
.batch-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.batch-num {
  width: 24px;
  text-align: center;
  font-weight: 600;
  color: var(--text-secondary, #888);
  flex-shrink: 0;
}
.batch-row .input-field { flex: 1; }
.cid-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}
.cid-input-group .input-field { flex: 1; }
.btn-upload {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #e8f4fd;
  color: #0d6efd;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  font-size: 14px;
  transition: background 0.15s;
}
.btn-upload:hover { background: #cce5ff; }
.file-hidden { display: none; }
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #ccc;
  border-top-color: #0d6efd;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.btn-remove { background: #f8d7da; color: #721c24; }
.btn-remove:hover { background: #f5c6cb; }
.btn-remove:disabled { opacity: 0.3; cursor: not-allowed; }
.batch-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.btn-secondary {
  padding: 10px 20px;
  border: 1px dashed var(--border, #ccc);
  border-radius: 8px;
  background: transparent;
  font-size: 14px;
  cursor: pointer;
  color: var(--text-secondary, #666);
}
.btn-secondary:hover { background: var(--bg-secondary, #f5f5f5); }

.candidate-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.candidate-table th, .candidate-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border, #e5e5e5);
  text-align: left;
}
.candidate-table th { font-weight: 600; background: var(--bg-secondary, #f5f5f5); }
.cid-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.control-section { padding-top: 8px; }
.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.btn-group { display: flex; gap: 12px; }
.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  background: #dc3545;
  color: white;
}
.btn-danger:hover { background: #c82333; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.voter-stats {
  padding: 10px 14px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 14px;
}
.batch-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border, #e5e5e5);
  margin-bottom: 6px;
}
.header-label {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #888);
}

/* ===== 财务监控样式 ===== */
.subsection {
  margin-top: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 4px solid var(--primary);
}
.subsection h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: var(--text);
}

.balance-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.balance-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.balance-item:last-child {
  border-bottom: none;
}
.balance-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}
.balance-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  font-family: monospace;
}
.balance-value.low-balance {
  color: #dc2626;
}

.log-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
}
.log-stats {
  font-size: 13px;
  color: var(--text-secondary);
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.logs-table thead {
  background: var(--bg-secondary, #f5f5f5);
}
.logs-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}
.logs-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}
.logs-table tbody tr:hover {
  background: #f9fafb;
}
.tx-hash {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.time-cell {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.details-cell {
  max-width: 300px;
  word-break: break-word;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.status-success {
  background: #d4edda;
  color: #155724;
}
.status-pending {
  background: #fff3cd;
  color: #856404;
}
.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.severity-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.severity-info {
  background: #d1ecf1;
  color: #0c5460;
}
.severity-warning {
  background: #fff3cd;
  color: #856404;
}
.severity-critical {
  background: #f8d7da;
  color: #721c24;
}

.logs-table tbody tr.severity-critical {
  background: #fff5f5;
}
</style>
