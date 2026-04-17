/**
 * Factory contract ABI
 */
export const FACTORY_ABI = [
  "function owner() view returns (address)",
  "function backendServerAddress() view returns (address)",
  "function createFee() view returns (uint256)",
  "function paused() view returns (bool)",
  "function createElection(string _title, string _sbtImageCid) payable returns (address)",
  "function setCreateFee(uint256 _newFee)",
  "function setBackendServerAddress(address _newAddress)",
  "function setPaused(bool _paused)",
  "function withdrawTreasury(address _to, uint256 _amount)",
  "function hasCreatorTitle(address _creator, string _title) view returns (bool)",
  "function getElectionCount() view returns (uint256)",
  "function getAllElections() view returns (address[] addrs, string[] titles, address[] creators, uint256[] createdAts)",
  "function isElection(address) view returns (bool)",
  "event ElectionCreated(uint256 indexed index, address indexed electionAddr, string title, address indexed creator)",
  "event CreateFeeUpdated(uint256 oldFee, uint256 newFee)",
  "event BackendServerAddressUpdated(address indexed oldAddress, address indexed newAddress)",
  "event TreasuryWithdrawn(address indexed to, uint256 amount)",
  "event FactoryPaused(bool paused)",
];

/**
 * Election contract ABI
 */
export const ELECTION_ABI = [
  "function admin() view returns (address)",
  "function platformServer() view returns (address)",
  "function candidateCount() view returns (uint256)",
  "function votingStarted() view returns (bool)",
  "function votingEnded() view returns (bool)",
  "function votingStartTime() view returns (uint256)",
  "function votingEndTime() view returns (uint256)",
  "function totalAuthorizedVoters() view returns (uint256)",
  "function totalVotesCast() view returns (uint256)",
  "function totalAbstainVotes() view returns (uint256)",
  "function isAuthorized(address) view returns (bool)",
  "function hasVoted(address) view returns (bool)",
  "function hasAbstained(address) view returns (bool)",
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function supportsInterface(bytes4 interfaceId) view returns (bool)",
  "function balanceOf(address owner) view returns (uint256)",
  "function ownerOf(uint256 tokenId) view returns (address)",
  "function voteCount(uint256) view returns (uint256)",
  "function candidateNames(uint256) view returns (string)",
  "function candidateCIDs(uint256) view returns (string)",
  "function getCandidate(uint256) view returns (string name, string imageCid, string manifestoCid, uint256 votes)",
  "function getAllCandidates() view returns (string[] names, string[] imageCids, string[] manifestoCids, uint256[] votes)",
  "function getVotingStatus() view returns (bool started, bool ended, uint256 candidates, uint256 voters, uint256 voted)",
  "function hasBadge(address voter) view returns (bool)",
  "function badgeTokenOf(address voter) view returns (uint256)",
  "function badgeDisplayName() view returns (string)",
  "function badgeDescription() view returns (string)",
  "function badgeImageURI(uint256 tokenId) view returns (string)",
  "function tokenURI(uint256 tokenId) view returns (string)",
  "function addCandidate(string _name, string _imageCid, string _manifestoCid)",
  "function addCandidatesBatch(string[] _names, string[] _imageCids, string[] _manifestoCids)",
  "function authorizeVoter(address _voter)",
  "function authorizeVotersBatch(address[] _voters)",
  "function startVoting(uint256 _start, uint256 _end)",
  "function endVoting()",
  "function abstain()",
  "function approve(address to, uint256 tokenId)",
  "function setApprovalForAll(address operator, bool approved)",
  "function getApproved(uint256 tokenId) view returns (address)",
  "function isApprovedForAll(address owner, address operator) view returns (bool)",
  "function transferFrom(address from, address to, uint256 tokenId)",
  "function safeTransferFrom(address from, address to, uint256 tokenId)",
  "function safeTransferFrom(address from, address to, uint256 tokenId, bytes data)",
  "function vote(uint256 _candidateId)",
  "event Voted(address indexed voter, uint256 indexed candidateId)",
  "event Abstained(address indexed voter)",
  "event VoterAuthorized(address indexed voter)",
  "event CandidateAdded(uint256 indexed candidateId, string name, string cid)",
  "event VotingStarted()",
  "event VotingEnded()",
  "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)",
  "event BadgeMinted(address indexed voter, uint256 indexed tokenId, string badgeName)",
];

export const VOTING_ABI = ELECTION_ABI;

export const FACTORY_ADDRESS = import.meta.env.VITE_FACTORY_ADDRESS || "";
export const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || "";
export const IPFS_GATEWAY = import.meta.env.VITE_IPFS_GATEWAY || "https://ipfs.io/ipfs/";
