<template>
  <div class="governance-page">
    <div class="page-header">
      <div>
        <h1>管理员控制台</h1>
        <p>模块一：链上治理 · 模块二：内容审核信誉 · 模块三：数据看板</p>
      </div>
      <div class="wallet-panel">
        <el-tag :type="wallet.address ? 'success' : 'info'" size="large">
          {{ wallet.address ? shortAddress(wallet.address) : '未连接钱包' }}
        </el-tag>
        <el-button v-if="!wallet.address" type="primary" @click="wallet.connect">连接钱包</el-button>
        <el-button v-else @click="wallet.disconnect">断开</el-button>
      </div>
    </div>

    <el-alert
      v-if="!wallet.isFactoryOwner"
      title="当前钱包不是工厂合约 Owner，链上治理按钮将不可用。"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    />

    <div class="module-switcher">
      <el-card
        shadow="hover"
        :class="['module-card', { active: activeModule === 'governance' }]"
        @click="activeModule = 'governance'"
      >
        <h3>模块一</h3>
        <p>链上治理</p>
      </el-card>
      <el-card
        shadow="hover"
        :class="['module-card', { active: activeModule === 'moderation' }]"
        @click="activeModule = 'moderation'"
      >
        <h3>模块二</h3>
        <p>内容审核信誉</p>
      </el-card>
      <el-card
        shadow="hover"
        :class="['module-card', { active: activeModule === 'analytics' }]"
        @click="activeModule = 'analytics'"
      >
        <h3>模块三</h3>
        <p>数据看板</p>
      </el-card>
    </div>

    <el-card v-if="activeModule === 'governance'" shadow="hover">
      <template #header>
        <div class="section-title">链上治理</div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="Factory Owner">{{ governance.owner || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否暂停">{{ governance.paused ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="后端代签地址">{{ governance.backend_server_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建费用">{{ governance.create_fee_eth ?? 0 }} ETH</el-descriptions-item>
        <el-descriptions-item label="Treasury 余额">{{ governance.treasury_eth ?? 0 }} ETH</el-descriptions-item>
      </el-descriptions>

      <div class="action-grid">
        <el-card>
          <h4>调控创建费</h4>
          <el-input v-model="feeEth" placeholder="例如 0.01" />
          <el-button type="primary" :disabled="!wallet.isFactoryOwner" :loading="txLoading" @click="updateCreateFee">
            设置创建费
          </el-button>
        </el-card>

        <el-card>
          <h4>后端代签地址</h4>
          <el-input v-model="backendServerAddressInput" placeholder="0x..." />
          <el-button type="primary" :disabled="!wallet.isFactoryOwner" :loading="txLoading" @click="updateBackendServerAddress">
            更新代签地址
          </el-button>
        </el-card>

        <el-card>
          <h4>紧急熔断</h4>
          <el-switch v-model="pausedValue" active-text="暂停" inactive-text="启用" />
          <el-button type="warning" :disabled="!wallet.isFactoryOwner" :loading="txLoading" @click="updatePaused">
            提交暂停状态
          </el-button>
        </el-card>

        <el-card>
          <h4>金库提现</h4>
          <el-input v-model="withdrawTo" placeholder="提现地址" />
          <el-input v-model="withdrawEth" placeholder="ETH 数量" style="margin-top: 8px" />
          <el-button type="danger" :disabled="!wallet.isFactoryOwner" :loading="txLoading" @click="withdrawTreasury">
            提现
          </el-button>
        </el-card>
      </div>
    </el-card>

    <el-card v-if="activeModule === 'moderation'" shadow="hover">
      <template #header>
        <div class="section-title">内容审核信誉</div>
      </template>

      <div class="toolbar">
        <el-input v-model="projectSearch" clearable placeholder="搜索项目名/地址/创建者" style="max-width: 340px" />
        <el-select v-model="visibilityFilter" style="width: 180px">
          <el-option label="全部状态" value="ALL" />
          <el-option label="可见" value="VISIBLE" />
          <el-option label="已隐藏" value="HIDDEN" />
        </el-select>
      </div>

      <el-table :data="pagedProjects" border>
        <el-table-column prop="title" label="项目名称" min-width="180" />
        <el-table-column prop="address" label="合约地址" min-width="180" />
        <el-table-column prop="creator" label="创建者" min-width="180" />
        <el-table-column label="蓝V" width="90">
          <template #default="scope">
            <el-tag v-if="scope.row.creator_verified" type="primary">蓝V</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.visibility === 'HIDDEN' ? 'danger' : 'success'">
              {{ scope.row.visibility === 'HIDDEN' ? '已隐藏' : '可见' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              :type="scope.row.visibility === 'HIDDEN' ? 'success' : 'danger'"
              :disabled="!wallet.isFactoryOwner"
              @click="toggleProjectVisibility(scope.row)"
            >
              {{ scope.row.visibility === 'HIDDEN' ? '恢复' : '下架' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="projectPage"
          :page-size="5"
          layout="prev, pager, next, total"
          :total="filteredProjects.length"
        />
      </div>

      <el-divider />

      <div class="reputation-grid">
        <el-card>
          <h4>官方蓝V白名单</h4>
          <el-input v-model="verifyWallet" placeholder="钱包地址" />
          <el-input v-model="verifyNote" placeholder="备注（可选）" style="margin-top: 8px" />
          <el-button type="primary" style="margin-top: 8px" :disabled="!wallet.isFactoryOwner" @click="addVerify">添加蓝V</el-button>
          <el-table :data="verifiedWallets" size="small" style="margin-top: 10px" max-height="220">
            <el-table-column prop="wallet_address" label="钱包" min-width="170" />
            <el-table-column prop="note" label="备注" min-width="110" />
            <el-table-column width="88" label="操作">
              <template #default="scope">
                <el-button size="small" type="danger" text :disabled="!wallet.isFactoryOwner" @click="removeVerify(scope.row.wallet_address)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card>
          <h4>恶意钱包黑名单</h4>
          <el-input v-model="blackWallet" placeholder="钱包地址" />
          <el-input v-model="blackReason" placeholder="封禁原因" style="margin-top: 8px" />
          <el-button type="danger" style="margin-top: 8px" :disabled="!wallet.isFactoryOwner" @click="addBlacklist">加入黑名单</el-button>
          <el-table :data="blacklistWallets" size="small" style="margin-top: 10px" max-height="220">
            <el-table-column prop="wallet_address" label="钱包" min-width="170" />
            <el-table-column prop="reason" label="原因" min-width="110" />
            <el-table-column width="88" label="操作">
              <template #default="scope">
                <el-button size="small" type="success" text :disabled="!wallet.isFactoryOwner" @click="removeBlacklist(scope.row.wallet_address)">解除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-card>

    <el-card v-if="activeModule === 'analytics'" shadow="hover">
      <template #header>
        <div class="section-title">数据看板</div>
      </template>

      <div class="metrics-grid">
        <el-card><h4>总项目数</h4><p class="metric">{{ analytics.total_elections || 0 }}</p></el-card>
        <el-card><h4>总投票人次</h4><p class="metric">{{ analytics.total_votes_cast || 0 }}</p></el-card>
        <el-card><h4>累计平台收益</h4><p class="metric">{{ analytics.total_revenue_eth || 0 }} ETH</p></el-card>
      </div>

      <el-divider content-position="left">实时活动流（创建项目）</el-divider>
      <el-table :data="analytics.activity || []" border>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="scope">{{ formatTs(scope.row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="项目" min-width="160" />
        <el-table-column prop="creator" label="创建者" min-width="170" />
        <el-table-column prop="address" label="合约地址" min-width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { ethers } from 'ethers';
import {
  addBlacklistWallet,
  addVerifiedWallet,
  getAnalyticsOverview,
  getBlacklistWallets,
  getGovernanceState,
  getModerationProjects,
  getVerifiedWallets,
  removeBlacklistWallet,
  removeVerifiedWallet,
  setModerationProjectVisibility,
} from '../services/api.js';
import { FACTORY_ABI, FACTORY_ADDRESS } from '../services/contract.js';
import { useWalletStore } from '../stores/wallet.js';

const wallet = useWalletStore();

const activeModule = ref('governance');
const txLoading = ref(false);

const governance = ref({});
const feeEth = ref('');
const pausedValue = ref(false);
const backendServerAddressInput = ref('');
const withdrawTo = ref('');
const withdrawEth = ref('');

const projects = ref([]);
const projectSearch = ref('');
const visibilityFilter = ref('ALL');
const projectPage = ref(1);

const verifyWallet = ref('');
const verifyNote = ref('');
const verifiedWallets = ref([]);

const blackWallet = ref('');
const blackReason = ref('');
const blacklistWallets = ref([]);

const analytics = ref({});

const filteredProjects = computed(() => {
  const q = projectSearch.value.trim().toLowerCase();
  return projects.value.filter((item) => {
    if (visibilityFilter.value !== 'ALL' && item.visibility !== visibilityFilter.value) {
      return false;
    }
    if (!q) return true;
    return (
      (item.title || '').toLowerCase().includes(q) ||
      (item.address || '').toLowerCase().includes(q) ||
      (item.creator || '').toLowerCase().includes(q)
    );
  });
});

const pagedProjects = computed(() => {
  const start = (projectPage.value - 1) * 5;
  return filteredProjects.value.slice(start, start + 5);
});

function shortAddress(value) {
  if (!value || value.length < 10) return value || '';
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

function formatTs(value) {
  if (!value) return '-';
  return new Date(Number(value) * 1000).toLocaleString();
}

async function loadGovernance() {
  if (!wallet.address) {
    governance.value = {};
    pausedValue.value = false;
    backendServerAddressInput.value = '';
    return;
  }
  governance.value = await getGovernanceState(wallet.address);
  pausedValue.value = !!governance.value.paused;
  backendServerAddressInput.value = governance.value.backend_server_address || '';
}

async function loadModeration() {
  if (!wallet.address) {
    projects.value = [];
    verifiedWallets.value = [];
    blacklistWallets.value = [];
    return;
  }
  const [projectRes, verifiedRes, blacklistRes] = await Promise.all([
    getModerationProjects(wallet.address),
    getVerifiedWallets(wallet.address),
    getBlacklistWallets(wallet.address),
  ]);
  projects.value = projectRes.items || [];
  verifiedWallets.value = verifiedRes.items || [];
  blacklistWallets.value = blacklistRes.items || [];
}

async function loadAnalytics() {
  if (!wallet.address) {
    analytics.value = {};
    return;
  }
  analytics.value = await getAnalyticsOverview(wallet.address);
}

async function getFactoryWithSigner() {
  if (!wallet.address) {
    await wallet.connect();
  }
  const signer = await wallet.getSigner();
  if (!signer) {
    throw new Error('钱包签名器不可用');
  }
  return new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, signer);
}

async function updateCreateFee() {
  if (!feeEth.value) {
    ElMessage.warning('请输入创建费用');
    return;
  }
  txLoading.value = true;
  try {
    const factory = await getFactoryWithSigner();
    const tx = await factory.setCreateFee(ethers.parseEther(feeEth.value.trim()));
    await tx.wait();
    ElMessage.success('创建费已更新');
    await loadGovernance();
  } catch (err) {
    ElMessage.error(err?.reason || err?.message || '设置创建费失败');
  } finally {
    txLoading.value = false;
  }
}

async function updatePaused() {
  txLoading.value = true;
  try {
    const factory = await getFactoryWithSigner();
    const tx = await factory.setPaused(!!pausedValue.value);
    await tx.wait();
    ElMessage.success('暂停状态已更新');
    await loadGovernance();
  } catch (err) {
    ElMessage.error(err?.reason || err?.message || '更新暂停状态失败');
  } finally {
    txLoading.value = false;
  }
}

async function updateBackendServerAddress() {
  const nextAddress = backendServerAddressInput.value.trim();
  if (!nextAddress) {
    ElMessage.warning('请输入后端代签地址');
    return;
  }
  if (!ethers.isAddress(nextAddress)) {
    ElMessage.warning('地址格式无效');
    return;
  }
  txLoading.value = true;
  try {
    const factory = await getFactoryWithSigner();
    const tx = await factory.setBackendServerAddress(nextAddress);
    await tx.wait();
    ElMessage.success('后端代签地址已更新');
    await loadGovernance();
  } catch (err) {
    ElMessage.error(err?.reason || err?.message || '更新后端代签地址失败');
  } finally {
    txLoading.value = false;
  }
}

async function withdrawTreasury() {
  if (!withdrawTo.value || !withdrawEth.value) {
    ElMessage.warning('请输入提现地址和数量');
    return;
  }
  txLoading.value = true;
  try {
    const factory = await getFactoryWithSigner();
    const tx = await factory.withdrawTreasury(withdrawTo.value.trim(), ethers.parseEther(withdrawEth.value.trim()));
    await tx.wait();
    ElMessage.success('提现成功');
    await loadGovernance();
  } catch (err) {
    ElMessage.error(err?.reason || err?.message || '提现失败');
  } finally {
    txLoading.value = false;
  }
}

async function toggleProjectVisibility(project) {
  if (!wallet.isFactoryOwner) {
    ElMessage.warning('当前钱包不是工厂 Owner，无法执行该操作');
    return;
  }
  const next = project.visibility === 'HIDDEN' ? 'VISIBLE' : 'HIDDEN';
  await setModerationProjectVisibility(project.address, next, wallet.address);
  ElMessage.success(next === 'HIDDEN' ? '项目已下架' : '项目已恢复');
  await loadModeration();
}

async function addVerify() {
  if (!wallet.isFactoryOwner) {
    ElMessage.warning('当前钱包不是工厂 Owner，无法执行该操作');
    return;
  }
  await addVerifiedWallet(verifyWallet.value.trim(), verifyNote.value.trim(), wallet.address);
  verifyWallet.value = '';
  verifyNote.value = '';
  ElMessage.success('已加入蓝V');
  await loadModeration();
}

async function removeVerify(walletAddress) {
  if (!wallet.isFactoryOwner) {
    ElMessage.warning('当前钱包不是工厂 Owner，无法执行该操作');
    return;
  }
  await removeVerifiedWallet(walletAddress, wallet.address);
  ElMessage.success('蓝V已移除');
  await loadModeration();
}

async function addBlacklist() {
  if (!wallet.isFactoryOwner) {
    ElMessage.warning('当前钱包不是工厂 Owner，无法执行该操作');
    return;
  }
  await addBlacklistWallet(blackWallet.value.trim(), blackReason.value.trim(), wallet.address);
  blackWallet.value = '';
  blackReason.value = '';
  ElMessage.success('已加入黑名单');
  await loadModeration();
}

async function removeBlacklist(walletAddress) {
  if (!wallet.isFactoryOwner) {
    ElMessage.warning('当前钱包不是工厂 Owner，无法执行该操作');
    return;
  }
  await removeBlacklistWallet(walletAddress, wallet.address);
  ElMessage.success('黑名单已解除');
  await loadModeration();
}

onMounted(async () => {
  if (wallet.address) {
    await wallet.checkFactoryOwner();
  }
  try {
    await Promise.all([loadGovernance(), loadModeration(), loadAnalytics()]);
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.message || '管理员数据加载失败');
  }
});

watch(
  () => wallet.address,
  async () => {
    try {
      await wallet.checkFactoryOwner();
      await Promise.all([loadGovernance(), loadModeration(), loadAnalytics()]);
    } catch (err) {
      ElMessage.error(err?.response?.data?.detail || err?.message || '钱包切换后管理员数据刷新失败');
    }
  }
);
</script>

<style scoped>
.governance-page {
  padding: 20px;
  background: linear-gradient(160deg, #f7fbff 0%, #f0f7ff 45%, #eef4ff 100%);
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h1 {
  margin: 0;
  color: #163a5f;
}

.page-header p {
  margin: 6px 0 0;
  color: #5f7286;
}

.wallet-panel {
  display: flex;
  align-items: center;
  gap: 10px;
}

.module-switcher {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.module-card {
  cursor: pointer;
  border: 1px solid #d4e4f4;
}

.module-card.active {
  border: 2px solid #1d78ff;
  box-shadow: 0 8px 18px rgba(28, 120, 255, 0.2);
}

.module-card h3 {
  margin: 0;
  color: #1f3f6b;
}

.module-card p {
  margin: 6px 0 0;
  color: #6380a1;
}

.section-title {
  font-weight: 700;
  color: #20466f;
}

.action-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.action-grid h4 {
  margin-top: 0;
}

.action-grid .el-button {
  margin-top: 8px;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.reputation-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 8px;
}

.metric {
  font-size: 24px;
  font-weight: 700;
  margin: 6px 0 0;
  color: #17406b;
}

@media (max-width: 960px) {
  .module-switcher,
  .action-grid,
  .reputation-grid,
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
