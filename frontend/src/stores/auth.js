import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  AUTH_STUDENT_KEY,
  getMyElections,
  getMyElectionsPage,
  getSession,
  getStoredStudentId,
  loginStudent,
  setAuthToken,
  setStoredStudentId,
} from "../services/api.js";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(window.localStorage.getItem("bcv_auth_token") || "");
  const studentId = ref(getStoredStudentId() || window.localStorage.getItem(AUTH_STUDENT_KEY) || "");
  const loading = ref(false);
  const sessionReady = ref(false);
  const myElections = ref([]);
  const myElectionsPage = ref([]);
  const myElectionsTotal = ref(0);
  const myElectionsHasMore = ref(false);

  const isAuthenticated = computed(() => Boolean(token.value && studentId.value));

  async function login(studentIdInput, password) {
    loading.value = true;
    try {
      const data = await loginStudent(studentIdInput, password);
      token.value = data.token;
      studentId.value = data.student_id;
      setAuthToken(data.token);
      setStoredStudentId(data.student_id);
      sessionReady.value = true;
      return data;
    } finally {
      loading.value = false;
    }
  }

  async function hydrate() {
    if (!token.value) {
      sessionReady.value = true;
      return false;
    }

    try {
      const data = await getSession();
      studentId.value = data.student_id;
      setStoredStudentId(data.student_id);
      sessionReady.value = true;
      return true;
    } catch {
      logout();
      sessionReady.value = true;
      return false;
    }
  }

  function logout() {
    token.value = "";
    studentId.value = "";
    myElections.value = [];
    setAuthToken("");
    setStoredStudentId("");
    sessionReady.value = true;
  }

  async function loadMyElections() {
    if (!isAuthenticated.value) {
      myElections.value = [];
      return [];
    }
    const data = await getMyElections();
    myElections.value = data;
    return data;
  }

  async function loadMyElectionsPage({ page = 1, pageSize = 12, search = "", bucket = "all" } = {}) {
    try {
      const result = await getMyElectionsPage({ page, pageSize, search, bucket });
      myElectionsPage.value = result.items || [];
      myElectionsTotal.value = Number(result.total || 0);
      myElectionsHasMore.value = Boolean(result.has_more);
      return result;
    } catch (error) {
      console.error("Failed to load paged elections:", error);
      myElectionsPage.value = [];
      myElectionsTotal.value = 0;
      myElectionsHasMore.value = false;
      return {
        items: [],
        total: 0,
        page,
        page_size: pageSize,
        has_more: false,
      };
    }
  }

  return {
    token,
    studentId,
    loading,
    sessionReady,
    myElections,
    myElectionsPage,
    myElectionsTotal,
    myElectionsHasMore,
    isAuthenticated,
    login,
    hydrate,
    logout,
    loadMyElections,
    loadMyElectionsPage,
  };
});
