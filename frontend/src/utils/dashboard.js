export function isTodoItem(item) {
  return item.eligible && item.phase !== "ENDED" && item.status !== "VOTED";
}

export function isHistoryItem(item) {
  return item.phase === "ENDED" || item.status === "VOTED";
}

export function sortDashboardItems(items) {
  const rank = { ACTIVE: 0, PENDING: 1, ENDED: 2 };
  return [...items].sort((left, right) => {
    const phaseGap = (rank[left.phase] ?? 9) - (rank[right.phase] ?? 9);
    if (phaseGap !== 0) return phaseGap;
    return (left.start_time || 0) - (right.start_time || 0);
  });
}

export function matchesDashboardSearch(item, keyword) {
  const query = keyword?.trim().toLowerCase();
  if (!query) return true;

  const title = displayTitle(item.title).toLowerCase();
  const address = (item.election_address || "").toLowerCase();
  return title.includes(query) || address.includes(query);
}

export function displayTitle(title) {
  return title?.trim() || "未命名投票项目";
}

export function shortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function formatDateTime(timestamp) {
  if (!timestamp) return "待公布";

  const date = new Date(Number(timestamp) * 1000);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${month}-${day} ${hours}:${minutes}`;
}

export function formatRangeCompact(startTime, endTime) {
  if (!startTime || !endTime) return "时间待公布";

  const now = Math.floor(Date.now() / 1000);
  if (now >= startTime && now <= endTime) {
    const hoursLeft = Math.ceil((endTime - now) / 3600);
    if (hoursLeft > 0 && hoursLeft <= 24) {
      return `剩余 ${hoursLeft} 小时`;
    }
  }

  return `${formatDateTime(startTime)} 至 ${formatDateTime(endTime)}`;
}

export function formatRangeFull(startTime, endTime) {
  if (!startTime || !endTime) return "时间待公布";

  return `${new Date(Number(startTime) * 1000).toLocaleString()} 至 ${new Date(Number(endTime) * 1000).toLocaleString()}`;
}

export function phaseLabel(phase) {
  if (phase === "ACTIVE") return "进行中";
  if (phase === "PENDING") return "未开始";
  return "已结束";
}

export function phaseBadgeClass(phase) {
  if (phase === "ACTIVE") return "badge-phase-active";
  if (phase === "PENDING") return "badge-phase-pending";
  return "badge-phase-ended";
}

export function ticketLabel(status) {
  if (status === "RESTRICTED") return "暂无票权";
  if (status === "AVAILABLE") return "未领票";
  if (status === "CLAIMED") return "已领票";
  return "已投票";
}

export function ticketBadgeClass(status) {
  if (status === "RESTRICTED") return "badge-ticket-restricted";
  if (status === "AVAILABLE") return "badge-ticket-available";
  if (status === "CLAIMED") return "badge-ticket-claimed";
  return "badge-ticket-voted";
}

export function unifiedBadge(item) {
  if (item.status === "VOTED") {
    return { label: "已参与", class: "badge-ticket-voted" };
  }

  if (item.phase === "ACTIVE") {
    return { label: "进行中", class: "badge-phase-active" };
  }

  if (item.phase === "ENDED") {
    return { label: "已结束", class: "badge-phase-ended" };
  }

  return { label: "未开始", class: "badge-phase-pending" };
}

export function cardCta(item) {
  if (item.eligible) {
    if (item.phase === "ACTIVE" && item.status === "AVAILABLE") {
      return { label: "申请投票权", className: "cta-claim", disabled: false, action: "claim" };
    }

    if (item.phase === "ACTIVE" && item.status === "CLAIMED") {
      return { label: "立即投票", className: "cta-vote", disabled: false, action: "vote" };
    }

    if (item.phase === "PENDING") {
      return { label: "敬请期待", className: "cta-disabled", disabled: true, action: "pending" };
    }

    return { label: "查看结果", className: "cta-result", disabled: false, action: "results" };
  }

  if (item.phase === "ENDED") {
    return { label: "查看结果", className: "cta-result", disabled: false, action: "results" };
  }

  return { label: "查看详情", className: "cta-result", disabled: false, action: "details" };
}
