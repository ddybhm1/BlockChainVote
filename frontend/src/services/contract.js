/**
 * 工厂合约 ABI - 用于创建和管理投票项目
 */
export const FACTORY_ABI = [
  "function owner() view returns (address)",
  "function createElection(string _title) returns (address)",
  "function getElectionCount() view returns (uint256)",
  "function getAllElections() view returns (address[] addrs, string[] titles, address[] creators, uint256[] createdAts)",
  "function isElection(address) view returns (bool)",
  "event ElectionCreated(uint256 indexed index, address indexed electionAddr, string title, address indexed creator)",
];

/**
 * 投票子合约 ABI - 单个投票项目的操作
 */
export const ELECTION_ABI = [
  // 查询方法
  "function admin() view returns (address)",
  "function candidateCount() view returns (uint256)",
  "function votingStarted() view returns (bool)",
  "function votingEnded() view returns (bool)",
  "function totalAuthorizedVoters() view returns (uint256)",
  "function totalVotesCast() view returns (uint256)",
  "function isAuthorized(address) view returns (bool)",
  "function hasVoted(address) view returns (bool)",
  "function voteCount(uint256) view returns (uint256)",
  "function candidateNames(uint256) view returns (string)",
  "function candidateCIDs(uint256) view returns (string)",
  "function getCandidate(uint256) view returns (string name, string cid, uint256 votes)",
  "function getAllCandidates() view returns (string[] names, string[] cids, uint256[] votes)",
  "function getVotingStatus() view returns (bool started, bool ended, uint256 candidates, uint256 voters, uint256 voted)",
  // 管理方法（需要签名）
  "function addCandidate(string _name, string _cid)",
  "function addCandidatesBatch(string[] _names, string[] _cids)",
  "function authorizeVoter(address _voter)",
  "function authorizeVotersBatch(address[] _voters)",
  "function startVoting()",
  "function endVoting()",
  // 投票方法（需要签名）
  "function vote(uint256 _candidateId)",
  // 事件
  "event Voted(address indexed voter, uint256 indexed candidateId)",
  "event VoterAuthorized(address indexed voter)",
  "event CandidateAdded(uint256 indexed candidateId, string name, string cid)",
  "event VotingStarted()",
  "event VotingEnded()",
];

// 向后兼容
export const VOTING_ABI = ELECTION_ABI;

export const FACTORY_ADDRESS = import.meta.env.VITE_FACTORY_ADDRESS || "";
export const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || "";
export const IPFS_GATEWAY = import.meta.env.VITE_IPFS_GATEWAY || "https://ipfs.io/ipfs/";
