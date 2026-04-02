const fs = require(fs);
const path = /home/mike/BlockChainVote/frontend/src/views/VoteView.vue;
let text = fs.readFileSync(path, utf-8);

text = text.replace(
  /<div v-else class=election-grid>[\s\S]*?<\/div>\n      <\/section>/,
  `<div v-else class=election-grid>
          <ElectionSummaryCard
            v-for=item
