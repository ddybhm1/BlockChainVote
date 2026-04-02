<template>
  <div class="candidate-card card">
    <div class="candidate-header">
      <div class="candidate-avatar">
        <img
          v-if="photoUrl"
          :src="photoUrl"
          :alt="name"
          class="avatar-img"
        />
        <div v-else class="avatar-placeholder">{{ name.charAt(0) }}</div>
      </div>
      <div class="candidate-info">
        <h3 class="candidate-name">{{ name }}</h3>
      </div>
      <div class="vote-count-badge">
        <span class="count">{{ votes }}</span>
        <span class="label">票</span>
      </div>
    </div>

    <div v-if="manifesto" class="manifesto">
      <a :href="manifesto" target="_blank" class="cid-link" title="查看竞选宣言资料">
        📄 查看竞选宣言
      </a>
    </div>

    <div class="candidate-actions">
      <template v-if="!votingEnded">
        <button
          class="btn btn-primary vote-btn"
          :disabled="!canVote"
          @click="$emit('vote', candidateId)"
        >
          {{ buttonText }}
        </button>
      </template>
      <template v-else>
        <div class="vote-ended-text">投票已经结束</div>
      </template>
      <a
        v-if="cid"
        :href="`${ipfsGateway}${cid}`"
        target="_blank"
        class="cid-link"
        title="在 IPFS 上查看原始资料"
      >
        📎 IPFS 验证
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  candidateId: { type: Number, required: true },
  name: { type: String, required: true },
  cid: { type: String, default: "" },
  votes: { type: Number, default: 0 },
  photoUrl: { type: String, default: "" },
  manifesto: { type: String, default: "" },
  canVote: { type: Boolean, default: false },
  hasVoted: { type: Boolean, default: false },
  votingActive: { type: Boolean, default: false },
  votingEnded: { type: Boolean, default: false },
});

defineEmits(["vote"]);

const ipfsGateway = import.meta.env.VITE_IPFS_GATEWAY || "https://ipfs.io/ipfs/";

const buttonText = computed(() => {
  if (props.votingEnded) return "投票已经结束";
  if (props.hasVoted) return "✓ 已投票";
  if (!props.votingActive) return "投票未开始";
  if (!props.canVote) return "无投票权";
  return "投票";
});
</script>

<style scoped>
.candidate-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.avatar-img {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), #818cf8);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
}

.candidate-info {
  flex: 1;
}

.candidate-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 2px;
}

.candidate-id {
  font-size: 13px;
  color: var(--text-secondary);
}

.vote-count-badge {
  text-align: center;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 8px 16px;
}
.vote-count-badge .count {
  display: block;
  font-size: 24px;
  font-weight: 800;
  color: #16a34a;
}
.vote-count-badge .label {
  font-size: 12px;
  color: #4ade80;
}

.manifesto {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 14px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.candidate-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vote-ended-text {
  flex: 1;
  color: #888;
  font-size: 16px;
  text-align: center;
  padding: 10px 0;
}

.vote-btn {
  flex: 1;
}

.cid-link {
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
}
.cid-link:hover {
  color: var(--primary);
}
</style>
