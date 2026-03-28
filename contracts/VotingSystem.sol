// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @title VotingSystem - 基于区块链的安全可信电子投票合约
/// @notice 实现匿名白名单授权、防双重投票、透明计票
contract VotingSystem {
    address public admin;
    bool public votingStarted;
    bool public votingEnded;
    uint256 public votingStartTime;
    uint256 public votingEndTime;
    uint256 public candidateCount;
    uint256 public totalAuthorizedVoters;
    uint256 public totalVotesCast;

    // 核心状态映射
    mapping(address => bool) public isAuthorized;   // 匿名地址白名单
    mapping(address => bool) public hasVoted;        // 防双重投票
    mapping(uint256 => uint256) public voteCount;    // 候选人得票数
    mapping(uint256 => string) public candidateCIDs; // 候选人 IPFS CID
    mapping(uint256 => string) public candidateNames;

    // 事件
    event VoterAuthorized(address indexed voter);
    event Voted(address indexed voter, uint256 indexed candidateId);
    event CandidateAdded(uint256 indexed candidateId, string name, string cid);
    event VotingStarted();
    event VotingEnded();

    modifier onlyAdmin() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    modifier duringVoting() {
        require(votingStarted && !votingEnded, "Voting not active");
        require(block.timestamp >= votingStartTime, "Voting not started yet");
        require(block.timestamp <= votingEndTime, "Voting ended");
        _;
    }

    modifier beforeVoting() {
        require(!votingStarted, "Voting already started");
        _;
    }

    constructor(address _admin) {
        admin = _admin;
        votingStartTime = 0;
        votingEndTime = 0;
    }

    // ==================== 管理功能 ====================

    /// @notice 添加候选人（仅投票开始前）
    function addCandidate(string calldata _name, string calldata _cid)
        external onlyAdmin beforeVoting
    {
        require(bytes(_name).length > 0, "Empty name");
        require(bytes(_cid).length > 0, "Empty CID");

        uint256 id = candidateCount;
        candidateNames[id] = _name;
        candidateCIDs[id] = _cid;
        candidateCount++;

        emit CandidateAdded(id, _name, _cid);
    }

    /// @notice 批量添加候选人
    function addCandidatesBatch(
        string[] calldata _names,
        string[] calldata _cids
    ) external onlyAdmin beforeVoting {
        require(_names.length == _cids.length, "Length mismatch");
        for (uint256 i = 0; i < _names.length; i++) {
            require(bytes(_names[i]).length > 0, "Empty name");
            require(bytes(_cids[i]).length > 0, "Empty CID");

            uint256 id = candidateCount;
            candidateNames[id] = _names[i];
            candidateCIDs[id] = _cids[i];
            candidateCount++;

            emit CandidateAdded(id, _names[i], _cids[i]);
        }
    }

    /// @notice 授权匿名地址的投票权
    function authorizeVoter(address _voter) external onlyAdmin {
        require(_voter != address(0), "Zero address");
        require(!isAuthorized[_voter], "Already authorized");

        isAuthorized[_voter] = true;
        totalAuthorizedVoters++;

        emit VoterAuthorized(_voter);
    }

    /// @notice 批量授权选民
    function authorizeVotersBatch(address[] calldata _voters) external onlyAdmin {
        for (uint256 i = 0; i < _voters.length; i++) {
            if (_voters[i] != address(0) && !isAuthorized[_voters[i]]) {
                isAuthorized[_voters[i]] = true;
                totalAuthorizedVoters++;
                emit VoterAuthorized(_voters[i]);
            }
        }
    }


    /// @notice 开始投票（设置起止时间，单位为秒级时间戳）
    function startVoting(uint256 _start, uint256 _end) external onlyAdmin beforeVoting {
        require(candidateCount > 0, "No candidates");
        require(_end > _start, "End must be after start");
        votingStarted = true;
        votingStartTime = _start;
        votingEndTime = _end;
        emit VotingStarted();
    }

    /// @notice 结束投票
    function endVoting() external onlyAdmin duringVoting {
        votingEnded = true;
        emit VotingEnded();
    }

    // ==================== 投票功能 ====================

    /// @notice 投票（由匿名地址直接调用）
    function vote(uint256 _candidateId) external duringVoting {
        require(isAuthorized[msg.sender], "Not authorized");
        require(!hasVoted[msg.sender], "Already voted");
        require(_candidateId < candidateCount, "Invalid candidate");

        hasVoted[msg.sender] = true;
        voteCount[_candidateId]++;
        totalVotesCast++;

        emit Voted(msg.sender, _candidateId);
    }

    // ==================== 查询功能 ====================

    /// @notice 获取单个候选人信息
    function getCandidate(uint256 _id)
        external view
        returns (string memory name, string memory cid, uint256 votes)
    {
        require(_id < candidateCount, "Invalid candidate");
        return (candidateNames[_id], candidateCIDs[_id], voteCount[_id]);
    }

    /// @notice 获取所有候选人
    function getAllCandidates()
        external view
        returns (string[] memory names, string[] memory cids, uint256[] memory votes)
    {
        names = new string[](candidateCount);
        cids = new string[](candidateCount);
        votes = new uint256[](candidateCount);
        for (uint256 i = 0; i < candidateCount; i++) {
            names[i] = candidateNames[i];
            cids[i] = candidateCIDs[i];
            votes[i] = voteCount[i];
        }
    }

    /// @notice 获取投票状态概览
    function getVotingStatus()
        external view
        returns (bool started, bool ended, uint256 candidates, uint256 voters, uint256 voted)
    {
        return (votingStarted, votingEnded, candidateCount, totalAuthorizedVoters, totalVotesCast);
    }
}
