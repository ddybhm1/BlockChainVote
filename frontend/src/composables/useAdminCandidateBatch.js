import { computed, ref, watch } from "vue";
import { uploadToIPFS } from "../services/api.js";
import { createCandidateDraft } from "../utils/admin.js";

function createInitialItems() {
  return [createCandidateDraft(), createCandidateDraft(), createCandidateDraft()];
}

export function useAdminCandidateBatch(resetSource) {
  const batchItems = ref(createInitialItems());
  const uploadMessage = ref("");
  const uploadMessageOk = ref(true);

  const validItems = computed(() =>
    batchItems.value
      .filter((item) => item.name.trim() && item.cid.trim() && item.manifestoCid.trim())
      .map((item) => ({
        name: item.name.trim(),
        cid: item.cid.trim(),
        manifestoCid: item.manifestoCid.trim(),
      }))
  );

  const validCount = computed(() => validItems.value.length);
  const hasValidItems = computed(() => validCount.value > 0);

  function resetItems() {
    batchItems.value = createInitialItems();
    uploadMessage.value = "";
    uploadMessageOk.value = true;
  }

  function addItem() {
    batchItems.value.push(createCandidateDraft());
  }

  function removeItem(index) {
    if (batchItems.value.length <= 1) return;
    batchItems.value.splice(index, 1);
  }

  async function handleFileUpload(event, index, type) {
    const file = event.target.files?.[0];
    if (!file) return;

    const item = batchItems.value[index];
    if (!item) return;

    if (type === 'image') item.uploadingImg = true;
    if (type === 'document') item.uploadingDoc = true;
    
    uploadMessage.value = "";

    try {
      const result = await uploadToIPFS(file);
      if (type === 'image') item.cid = result.cid;
      if (type === 'document') item.manifestoCid = result.cid;
      
      uploadMessage.value = "文件已上传到 IPFS，可继续配置候选人。";
      uploadMessageOk.value = true;
    } catch (error) {
      uploadMessage.value = `文件上传失败：${error.response?.data?.detail || error.message}`;
      uploadMessageOk.value = false;
    } finally {
      if (type === 'image') item.uploadingImg = false;
      if (type === 'document') item.uploadingDoc = false;
      event.target.value = "";
    }
  }

  watch(resetSource, resetItems);

  return {
    batchItems,
    uploadMessage,
    uploadMessageOk,
    validItems,
    validCount,
    hasValidItems,
    addItem,
    removeItem,
    handleFileUpload,
    resetItems,
  };
}
