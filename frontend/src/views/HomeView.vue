<template>
  <div class="home">
    <div class="hero card">
      <h1>⛓️ 基于区块链的安全可信电子投票系统</h1>
      <p class="subtitle">
        利用以太坊智能合约实现透明计票，IPFS 确保资料防篡改，<br />
        创新性"单向授权解耦"机制兼顾身份防伪与投票匿名。
      </p>
      <div class="hero-actions">
        <router-link to="/auth" class="btn btn-primary">领取选票</router-link>
        <router-link to="/vote" class="btn btn-success">进入投票大厅</router-link>
        <router-link to="/results" class="btn btn-secondary">📊 公众审计入口</router-link>
      </div>
    </div>

    <div class="features">
      <div class="feature card">
        <div class="feature-icon">🔒</div>
        <h3>身份防伪 + 绝对匿名</h3>
        <p>学号实名验证拦截假选民，匿名钱包地址投票。后端"阅后即焚"，不留任何身份-地址映射。</p>
      </div>
      <div class="feature card">
        <div class="feature-icon">📦</div>
        <h3>IPFS 资料防篡改</h3>
        <p>候选人资料存入 IPFS，CID 写入智能合约。任何篡改都将导致哈希不匹配，被前端立即识别。</p>
      </div>
      <div class="feature card">
        <div class="feature-icon">📊</div>
        <h3>链上透明计票</h3>
        <p>选票直接上链，任何人可通过 Etherscan 实时查阅交易记录与精准票数，100% 公开透明。</p>
      </div>
    </div>

    <div class="card">
      <h3>📋 投票流程</h3>
      <ol class="steps">
        <li><strong>连接钱包</strong> — 点击右上角「连接钱包」唤起 MetaMask</li>
        <li><strong>领取选票</strong> — 输入学号、密码进行身份验证，授权当前匿名地址</li>
        <li><strong>进入大厅</strong> — 查看候选人资料（来自 IPFS），选择心仪候选人</li>
        <li><strong>签名投票</strong> — MetaMask 签名确认，选票直接上链</li>
        <li><strong>查看结果</strong> — 实时链上计票，可在 Etherscan 独立验证</li>
      </ol>
    </div>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 48px 24px;
}
.hero h1 {
  font-size: 28px;
  margin-bottom: 12px;
}
.subtitle {
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: 24px;
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.feature {
  text-align: center;
}
.feature-icon {
  font-size: 36px;
  margin-bottom: 10px;
}
.feature h3 {
  font-size: 16px;
  margin-bottom: 8px;
}
.feature p {
  font-size: 13px;
  color: var(--text-secondary);
}
.steps {
  padding-left: 20px;
}
.steps li {
  padding: 8px 0;
  font-size: 14px;
}

@media (max-width: 640px) {
  .features {
    grid-template-columns: 1fr;
  }
}
</style>
