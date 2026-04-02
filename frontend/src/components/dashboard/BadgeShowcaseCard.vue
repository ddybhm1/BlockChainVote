<template>
  <section class="card badge-showcase">
    <div class="badge-copy">
      <p class="detail-kicker">Soulbound Token</p>
      <h3>我的投票纪念徽章</h3>
      <p class="badge-desc">只有成功完成投票的钱包才能领取，适合作为本次参与的链上纪念。</p>

      <div class="badge-meta">
        <div class="meta-chip">
          <span>徽章名称</span>
          <strong>{{ badge.name }}</strong>
        </div>
        <div class="meta-chip">
          <span>Token ID</span>
          <strong>#{{ badge.tokenId }}</strong>
        </div>
        <div class="meta-chip">
          <span>绑定地址</span>
          <strong>{{ shortAddress(walletAddress) }}</strong>
        </div>
      </div>

      <p class="badge-detail">{{ badge.description }}</p>
    </div>

    <div class="badge-card">
      <img v-if="badge.image" :src="badge.image" :alt="badge.name" class="badge-image" />

      <div class="badge-footer">
        <span class="badge-pill">SBT · Non-transferable</span>
        <span class="badge-pill">{{ displayTitle(title) }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { displayTitle, shortAddress } from "../../utils/dashboard.js";

defineProps({
  badge: { type: Object, required: true },
  walletAddress: { type: String, default: "" },
  title: { type: String, default: "" },
});
</script>

<style scoped>
.badge-showcase {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 420px);
  gap: 20px;
  align-items: center;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.14), transparent 30%),
    #ffffff;
}

.detail-kicker {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 11px;
  color: #0f766e;
  font-weight: 700;
}

.badge-desc,
.badge-detail {
  color: var(--text-secondary);
}

.badge-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0;
}

.meta-chip {
  min-width: 140px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid var(--border);
}

.meta-chip span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.badge-card {
  padding: 22px;
  border-radius: 22px;
  background: linear-gradient(180deg, #0f172a, #111827);
  color: #ffffff;
}

.badge-image {
  width: 100%;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
}

.badge-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.badge-pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 12px;
}

@media (max-width: 960px) {
  .badge-showcase {
    grid-template-columns: 1fr;
  }
}
</style>
