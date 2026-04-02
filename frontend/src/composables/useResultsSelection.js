import { computed, onMounted, ref, watch } from "vue";

export function useResultsSelection(voting, route, router) {
  const selectedElection = ref("");

  watch(selectedElection, async (address) => {
    if (!address) {
      const nextQuery = { ...route.query };
      delete nextQuery.election;
      router.replace({ query: nextQuery });
      return;
    }

    if (route.query.election !== address) {
      router.replace({ query: { ...route.query, election: address } });
    }

    await voting.selectElection(address);
  });

  const selectedTitle = computed(
    () =>
      voting.elections.find(
        (election) => election.address.toLowerCase() === selectedElection.value.toLowerCase()
      )?.title || ""
  );

  onMounted(() => {
    if (typeof route.query.election === "string" && route.query.election) {
      selectedElection.value = route.query.election;
    }
  });

  watch(
    () => voting.elections,
    (items) => {
      if (!selectedElection.value) return;

      const matched = items.find(
        (item) => item.address.toLowerCase() === selectedElection.value.toLowerCase()
      );

      if (matched && matched.address !== selectedElection.value) {
        selectedElection.value = matched.address;
      }
    },
    { deep: true }
  );

  return {
    selectedElection,
    selectedTitle,
  };
}
