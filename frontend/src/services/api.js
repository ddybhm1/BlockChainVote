import axios from "axios";

export const AUTH_TOKEN_KEY = "bcv_auth_token";
export const AUTH_STUDENT_KEY = "bcv_student_id";

// 存储各个投票项目的投票交易哈希，防止依赖后端
const TX_HASH_PREFIX = "voted_tx_hash_";

export function saveLocalVoteTxHash(electionAddress, txHash) {
  window.localStorage.setItem(TX_HASH_PREFIX + electionAddress.toLowerCase(), txHash);
}

export function getLocalVoteTxHash(electionAddress) {
  return window.localStorage.getItem(TX_HASH_PREFIX + electionAddress.toLowerCase());
}

const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
});

function getStoredToken() {
  return window.localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function setAuthToken(token) {
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  delete api.defaults.headers.common.Authorization;
}

export function setStoredStudentId(studentId) {
  if (studentId) {
    window.localStorage.setItem(AUTH_STUDENT_KEY, studentId);
    return;
  }
  window.localStorage.removeItem(AUTH_STUDENT_KEY);
}

export function getStoredStudentId() {
  return window.localStorage.getItem(AUTH_STUDENT_KEY) || "";
}

const initialToken = getStoredToken();
if (initialToken) {
  api.defaults.headers.common.Authorization = `Bearer ${initialToken}`;
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      setAuthToken("");
      setStoredStudentId("");
    }
    return Promise.reject(error);
  }
);

export async function loginStudent(studentId, password) {
  const res = await api.post("/auth/login", {
    student_id: studentId,
    password,
  });
  return res.data;
}

export async function getSession() {
  const res = await api.get("/auth/me");
  return res.data;
}

export async function getMyElections() {
  const res = await api.get("/auth/my-elections");
  return res.data;
}

export const getMyElectionsPage = async ({ page = 1, pageSize = 12, search = '', bucket = 'all' } = {}) => {
  const response = await api.get('/auth/my-elections-page', {
    params: {
      page,
      page_size: pageSize,
      search,
      bucket,
    },
  });
  return (
    response.data || {
      items: [],
      total: 0,
      page,
      page_size: pageSize,
      has_more: false,
    }
  );
}

export async function getElectionTicketStatus(electionAddress) {
  const res = await api.get(`/auth/ticket-status/${electionAddress}`);
  return res.data;
}

export async function authorizeTicket(electionAddress, walletAddress) {
  const res = await api.post("/auth/authorize-ticket", {
    election_address: electionAddress,
    wallet_address: walletAddress,
  });
  return res.data;
}

export async function markVoted(electionAddress, walletAddress) {
  const res = await api.post("/auth/mark-voted", {
    election_address: electionAddress,
    wallet_address: walletAddress,
  });
  return res.data;
}

export async function claimTicket(studentId, password, walletAddress, electionAddress) {
  const res = await api.post("/auth/claim-ticket", {
    student_id: studentId,
    password,
    wallet_address: walletAddress,
    election_address: electionAddress,
  });
  return res.data;
}

export async function setVotingTime(electionAddress, startTime, endTime) {
  const res = await api.post("/admin/set-voting-time", {
    election_address: electionAddress,
    start_time: startTime,
    end_time: endTime,
  });
  return res.data;
}

export async function registerVoter(studentId, password, electionAddress) {
  const res = await api.post("/admin/register-voter", {
    student_id: studentId,
    password,
    election_address: electionAddress,
  });
  return res.data;
}

export async function uploadVotersExcel(electionAddress, file) {
  const formData = new FormData();
  formData.append("election_address", electionAddress);
  formData.append("file", file);

  const res = await api.post("/admin/upload-voters-excel", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res.data;
}

export async function uploadToIPFS(file, options = {}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("purpose", options.purpose || "generic");
  const res = await api.post("/admin/upload-ipfs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return res.data;
}

export async function syncElectionToBackend(electionAddress, title, startTime, endTime) {
  const res = await api.post("/admin/sync-election", {
    election_address: electionAddress,
    title,
    start_time: startTime,
    end_time: endTime
  });
  return res.data;
}

export async function getVotersCount(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/voters-count", { params });
  return res.data;
}

export async function logTransaction(data) {
  const res = await api.post("/admin/log-transaction", data);
  return res.data;
}

export async function logSecurity(data) {
  const res = await api.post("/admin/log-security", data);
  return res.data;
}

export async function getTransactionLogs(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/transaction-logs", { params });
  return res.data;
}

export async function getSecurityLogs(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/security-logs", { params });
  return res.data;
}

export default api;
