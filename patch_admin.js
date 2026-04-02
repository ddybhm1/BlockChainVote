const fs = require('fs');
const path = require('path');

const targetFile = path.join(__dirname, 'frontend', 'src', 'views', 'AdminView.vue');

let content = fs.readFileSync(targetFile, 'utf8');

// Replace template
const newTemplate = `<template>
  <el-container class="admin-layout">
    <!-- Sidebar -->
    <el-aside width="250px" class="admin-sidebar">
      <div class="sidebar-logo">
        <el-icon :size="24" color="#fff" style="margin-right: 8px"><Monitor /></el-icon>
        <span style="color:#fff;font-weight:600;font-size:16px;">投票管理后台</span>
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

      <!-- Main -->
      <el-main class="admin-main">
        <div v-if="!wallet.address || !wallet.isFactoryOwner" class="alert alert-error">
          <el-empty description="请先连接管理员钱包 (Wallet Connect)" />
        </div>
        <div v-else>
          <el-alert v-if="globalMsg" :title="globalMsg" :type="globalMsgOk ? 'success' : 'error'" show-icon style="margin-bottom: 20px" />

          <el-card shadow="hover" class="context-card" v-if="activeMenu !== 'overview'">
             <span style="font-weight:bold;margin-right:12px;">当前管理项目</span>
             <el-tag v-if="selectedTitle" type="primary" size="large" style="margin-right:12px;">{{ selectedTitle }}</el-tag>
             <el-tag v-else type="info" size="large" style="margin-right:12px;">未选择</el-tag>
             <span v-if="selectedAddr" style="font-family:monospace; color:#6b7280; font-size:13px; margin-right:12px;">{{ selectedAddr }}</span>
             <el-tag :type="status.ended ? 'danger' : (status.started ? 'success' : 'warning')" v-if="selectedAddr">
               {{ status.ended ? '已结束' : (status.started ? '进行中' : '未开始') }}
             </el-tag>
          </el-card>

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

          <div v-show="activeMenu === 'projects'">
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
            
            <el-card shadow="hover" style="margin-top:20px" v-if="selectedAddr" header="部署投票时间">
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
            </el-card>
          </div>

          <div v-show="activeMenu === 'candidates'">
            <AdminCandidateManager
              :status-started="status.started"
              :submitting="submitting"
              :candidates="candidates"
              :reset-key="candidateResetKey"
              @submit="handleBatchAdd"
            />
          </div>

          <div v-show="activeMenu === 'voters'">
            <AdminVoterManager
              :submitting="voterSubmitting"
              :message="voterMessage"
              :message-ok="voterMessageOk"
              :voter-stats="voterStats"
              :reset-key="voterResetKey"
              @submit="handleBatchRegister"
              @import-excel="handleExcelImport"
            />
          </div>

          <div v-show="activeMenu === 'logs'">
            <AdminLogsPanel
              class="console-panel"
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
      </el-main>
    </el-container>
  </el-container>
</template>
`;

const newStyle = `
<style scoped>
.admin-layout { height: 100vh; background-color: #F4F7FE; }
.admin-sidebar { background-color: #1E222D; display: flex; flex-direction: column; }
.sidebar-logo { height: 60px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid rgba(255,255,255,0.05); }
.sidebar-menu { border-right: none; }
.sidebar-menu .el-menu-item.is-active { background-color: #409EFF; color: #fff !important; }
.admin-header { background-color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; box-shadow: 0 1px 4px rgba(0,21,41,.08); z-index: 1; }
.admin-main { padding: 24px; overflow-y: auto; }
.context-card { margin-bottom: 20px; border-radius: 8px; }
.data-card { display: flex; align-items: center; padding: 12px; border-radius: 12px; margin-bottom: 20px; }
.card-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin-right: 16px; }
.card-info { display: flex; flex-direction: column; }
.label { font-size: 13px; color: #909399; margin-bottom: 4px; }
.value { font-size: 24px; font-weight: 700; color: #303133; }
.console-panel :deep(.card) { background: #1e1e1e; color: #a6e22e; border: 1px solid #333; }
.console-panel :deep(.log-table) { background: transparent !important; color: #a6e22e !important; font-family: Consolas, monospace !important; }
</style>
`;

content = content.replace(/<template>[\s\S]*?<\/template>/, newTemplate);

const scriptAdd = `
const activeMenu = ref('overview');
const activeMenuName = computed(() => {
  const map = { overview: '概览看板', projects: '项目管理', candidates: '候选人管理', voters: '选票管理', logs: '交易与安全' };
  return map[activeMenu.value];
});
function handleMenuSelect(index) { activeMenu.value = index; }
`;

content = content.replace('const startTime = ref("");', scriptAdd + '\nconst startTime = ref("");');

content += '\n' + newStyle;

fs.writeFileSync(targetFile, content, 'utf8');
console.log('Script updated AdminView.vue');
