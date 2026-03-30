/**
 * 设置投票时间（管理员操作）
 */
export async function setVotingTime(electionAddress, startTime, endTime) {
  const res = await api.post("/admin/set-voting-time", {
    election_address: electionAddress,
    start_time: startTime,
    end_time: endTime,
  });
  return res.data;
}
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000, // 链上交易可能需要较长时间
});

/**
 * 领取选票 - 向后端发送 KYC 请求
 * 后端验证身份后授权匿名地址到指定投票项目的合约，然后丢弃地址信息
 */
export async function claimTicket(studentId, password, walletAddress, electionAddress) {
  const res = await api.post("/auth/claim-ticket", {
    student_id: studentId,
    password: password,
    wallet_address: walletAddress,
    election_address: electionAddress,
  });
  return res.data;
}

/**
 * 注册选民（管理员操作）
 */
export async function registerVoter(studentId, password, electionAddress) {
  const res = await api.post("/admin/register-voter", {
    student_id: studentId,
    password: password,
    election_address: electionAddress,
  });
  return res.data;
}

/**
 * 批量导入选民（Excel）
 */
export async function uploadVotersExcel(electionAddress, file) {
  const formData = new FormData();
  formData.append("election_address", electionAddress);
  formData.append("file", file);
  
  const res = await api.post("/admin/upload-voters-excel", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return res.data;
}

/**
 * 上传文件到 IPFS，返回 CID
 */
export async function uploadToIPFS(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/admin/upload-ipfs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return res.data;
}

/**
 * 获取选民统计（支持按项目查询）
 */
export async function getVotersCount(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/voters-count", { params });
  return res.data;
}

/**
 * 记录交易日志
 */
export async function logTransaction(data) {
  const res = await api.post("/admin/log-transaction", data);
  return res.data;
}

/**
 * 记录安全日志
 */
export async function logSecurity(data) {
  const res = await api.post("/admin/log-security", data);
  return res.data;
}

/**
 * 获取交易日志
 */
export async function getTransactionLogs(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/transaction-logs", { params });
  return res.data;
}

/**
 * 获取安全日志
 */
export async function getSecurityLogs(electionAddress) {
  const params = {};
  if (electionAddress) params.election_address = electionAddress;
  const res = await api.get("/admin/security-logs", { params });
  return res.data;
}
