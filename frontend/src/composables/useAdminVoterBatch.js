import { computed, ref, watch } from "vue";
import { createVoterDraft } from "../utils/admin.js";

function createInitialItems() {
  return [createVoterDraft(), createVoterDraft(), createVoterDraft()];
}

export function useAdminVoterBatch(resetSource) {
  const voterItems = ref(createInitialItems());

  const validVoters = computed(() =>
    voterItems.value
      .filter((item) => item.studentId.trim() && item.password.trim())
      .map((item) => ({
        studentId: item.studentId.trim(),
        password: item.password.trim(),
      }))
  );

  const validVoterCount = computed(() => validVoters.value.length);
  const hasValidVoters = computed(() => validVoterCount.value > 0);

  function resetItems() {
    voterItems.value = createInitialItems();
  }

  function addVoter() {
    voterItems.value.push(createVoterDraft());
  }

  function removeVoter(index) {
    if (voterItems.value.length <= 1) return;
    voterItems.value.splice(index, 1);
  }

  watch(resetSource, resetItems);

  return {
    voterItems,
    validVoters,
    validVoterCount,
    hasValidVoters,
    addVoter,
    removeVoter,
    resetItems,
  };
}
