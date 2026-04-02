export function createCandidateDraft() {
  return {
    name: "",
    cid: "",
    manifestoCid: "",
    uploadingImg: false,
    uploadingDoc: false,
  };
}

export function createVoterDraft() {
  return {
    studentId: "",
    password: "",
  };
}

export function formatAdminTime(ts) {
  if (!ts) return "";

  try {
    const numTs = Number(ts);
    if (!Number.isNaN(numTs)) {
      const milliseconds = numTs < 10000000000 ? numTs * 1000 : numTs;
      return new Date(milliseconds).toLocaleString("zh-CN");
    }

    return new Date(ts).toLocaleString("zh-CN");
  } catch {
    return String(ts);
  }
}

export function formatWeiValue(weiStr) {
  if (!weiStr) return "-";

  try {
    const value = BigInt(weiStr);
    if (value < 1000000000n) return `${value} Wei`;
    return `${(Number(value) / 1e18).toFixed(6)} ETH`;
  } catch {
    return String(weiStr);
  }
}
