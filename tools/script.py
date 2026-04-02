import sys

file_path = /home/mike/BlockChainVote/frontend/src/views/VoteView.vue
with open(file_path, r, encoding=utf-8) as f:
    text = f.read()

replacement = "        <div v-else class=election-grid>
          <ElectionSummaryCard
            v-for=item
