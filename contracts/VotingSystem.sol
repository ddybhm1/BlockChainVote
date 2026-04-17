// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./utils/Base64.sol";

/// @title VotingSystem
/// @notice 匿名投票后自动铸造与候选人直接绑定的 SBT(灵魂绑定代币)
contract VotingSystem {
    using Base64 for bytes;

    address public admin;
    address public platformServer;
    string public electionName; // 新增：投票项目名称
    string public sbtImageCid;  // 新增：项目 SBT 图片 CID
    
    bool public votingStarted;
    bool public votingEnded;
    uint256 public votingStartTime;
    uint256 public votingEndTime;
    uint256 public candidateCount;
    uint256 public totalAuthorizedVoters;
    uint256 public totalVotesCast;
    uint256 public totalAbstainVotes;

    string public constant name = "BlockChainVote SBT";
    string public constant symbol = "BCVSBT";
    string public constant BADGE_EDITION = "2026/V1";

    // 新增：候选人数据结构
    struct Candidate {
        string name;
        string imageCid;      // 候选人图片
        string manifestoCid;  // 竞选宣言文档IPFS (如PDF/TXT)
        uint256 voteCount;
    }
    
    mapping(uint256 => Candidate) public candidates;
    
    mapping(address => bool) public isAuthorized;
    mapping(address => bool) public hasVoted;
    mapping(address => bool) public hasAbstained;
    
    mapping(uint256 => address) private _badgeOwners;
    mapping(address => uint256) private _badgeBalances;
    mapping(address => uint256) private _badgeTokenIds;
    
    // 【核心新增】：将每一个铸造的 SBT Token ID 关联到对应的候选人 ID 上
    mapping(uint256 => uint256) public badgeToCandidate; 

    event VoterAuthorized(address indexed voter);
    event Voted(address indexed voter, uint256 indexed candidateId);
    event Abstained(address indexed voter);
    event CandidateAdded(uint256 indexed candidateId, string name, string imageCid, string manifestoCid);
    event VotingStarted();
    event VotingEnded();

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event BadgeMinted(address indexed voter, uint256 indexed tokenId, string badgeName);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    modifier onlyAdminOrServer() {
        require(msg.sender == admin || msg.sender == platformServer, "Not authorized to issue tickets");
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

    // 构造函数新增 _platformServer，实现独立创建者 + 平台后端双授权
    constructor(address _admin, address _platformServer, string memory _electionName, string memory _sbtImageCid) {
        require(_admin != address(0), "Zero admin");
        require(_platformServer != address(0), "Zero server");
        admin = _admin;
        platformServer = _platformServer;
        electionName = _electionName;
        sbtImageCid = _sbtImageCid;
        votingStartTime = 0;
        votingEndTime = 0;
    }

    // ==================== Admin ====================

    // 新增 _manifestoCid 参数
    function addCandidate(
        string calldata _name, 
        string calldata _imageCid, 
        string calldata _manifestoCid
    ) external onlyAdmin beforeVoting {
        require(bytes(_name).length > 0, "Empty name");
        require(bytes(_imageCid).length > 0, "Empty image CID");

        uint256 id = candidateCount;
        candidates[id] = Candidate({
            name: _name,
            imageCid: _imageCid,
            manifestoCid: _manifestoCid,
            voteCount: 0
        });
        candidateCount++;

        emit CandidateAdded(id, _name, _imageCid, _manifestoCid);
    }

    function addCandidatesBatch(
        string[] calldata _names,
        string[] calldata _imageCids,
        string[] calldata _manifestoCids
    ) external onlyAdmin beforeVoting {
        require(_names.length == _imageCids.length && _imageCids.length == _manifestoCids.length, "Length mismatch");

        for (uint256 i = 0; i < _names.length; i++) {
            require(bytes(_names[i]).length > 0, "Empty name");
            require(bytes(_imageCids[i]).length > 0, "Empty image CID");

            uint256 id = candidateCount;
            candidates[id] = Candidate({
                name: _names[i],
                imageCid: _imageCids[i],
                manifestoCid: _manifestoCids[i],
                voteCount: 0
            });
            candidateCount++;

            emit CandidateAdded(id, _names[i], _imageCids[i], _manifestoCids[i]);
        }
    }

    function authorizeVoter(address _voter) external onlyAdminOrServer {
        require(_voter != address(0), "Zero address");
        require(!isAuthorized[_voter], "Already authorized");
        isAuthorized[_voter] = true;
        totalAuthorizedVoters++;
        emit VoterAuthorized(_voter);
    }

    function authorizeVotersBatch(address[] calldata _voters) external onlyAdminOrServer {
        for (uint256 i = 0; i < _voters.length; i++) {
            if (_voters[i] != address(0) && !isAuthorized[_voters[i]]) {
                isAuthorized[_voters[i]] = true;
                totalAuthorizedVoters++;
                emit VoterAuthorized(_voters[i]);
            }
        }
    }

    function startVoting(uint256 _start, uint256 _end) external onlyAdmin beforeVoting {
        require(candidateCount > 0, "No candidates");
        require(_end > _start, "End must be after start");
        votingStarted = true;
        votingStartTime = _start;
        votingEndTime = _end;
        emit VotingStarted();
    }

    function endVoting() external onlyAdmin duringVoting {
        votingEnded = true;
        emit VotingEnded();
    }

    // ==================== Vote ====================

    function vote(uint256 _candidateId) external duringVoting {
        require(isAuthorized[msg.sender], "Not authorized");
        require(!hasVoted[msg.sender], "Already voted");
        require(_candidateId < candidateCount, "Invalid candidate");

        hasVoted[msg.sender] = true;
        hasAbstained[msg.sender] = false;
        candidates[_candidateId].voteCount++;
        totalVotesCast++;

        uint256 mintedTokenId = _mintBadge(msg.sender);
        
        // 【核心修改】：把这枚徽章 Token 与选民支持的候选人永久绑定
        badgeToCandidate[mintedTokenId] = _candidateId;

        emit Voted(msg.sender, _candidateId);
        emit BadgeMinted(msg.sender, mintedTokenId, "Voter Witness SBT");
    }

    function abstain() external duringVoting {
        require(isAuthorized[msg.sender], "Not authorized");
        require(!hasVoted[msg.sender], "Already voted");

        hasVoted[msg.sender] = true;
        hasAbstained[msg.sender] = true;
        totalVotesCast++;
        totalAbstainVotes++;

        uint256 mintedTokenId = _mintBadge(msg.sender);
        badgeToCandidate[mintedTokenId] = type(uint256).max;

        emit Abstained(msg.sender);
        emit BadgeMinted(msg.sender, mintedTokenId, "Voter Witness SBT");
    }

    // ==================== Query ====================

    function getCandidate(uint256 _id)
        external
        view
        returns (
            string memory candidateName, 
            string memory imageCid, 
            string memory manifestoCid, 
            uint256 votes
        )
    {
        require(_id < candidateCount, "Invalid candidate");
        Candidate memory c = candidates[_id];
        return (c.name, c.imageCid, c.manifestoCid, c.voteCount);
    }

    function getAllCandidates()
        external
        view
        returns (
            string[] memory names, 
            string[] memory imageCids, 
            string[] memory manifestoCids, 
            uint256[] memory votes
        )
    {
        names = new string[](candidateCount);
        imageCids = new string[](candidateCount);
        manifestoCids = new string[](candidateCount);
        votes = new uint256[](candidateCount);

        for (uint256 i = 0; i < candidateCount; i++) {
            names[i] = candidates[i].name;
            imageCids[i] = candidates[i].imageCid;
            manifestoCids[i] = candidates[i].manifestoCid;
            votes[i] = candidates[i].voteCount;
        }
    }

    function getVotingStatus()
        external view returns (bool started, bool ended, uint256 candidatesTotal, uint256 voters, uint256 voted)
    {
        bool realEnded = votingEnded || (votingStarted && block.timestamp > votingEndTime);
        return (votingStarted, realEnded, candidateCount, totalAuthorizedVoters, totalVotesCast);
    }

    // ==================== Soulbound Badge Logic ====================

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x01ffc9a7 || interfaceId == 0x80ac58cd || interfaceId == 0x5b5e139f; 
    }

    function balanceOf(address owner) public view returns (uint256) {
        require(owner != address(0), "Zero address");
        return _badgeBalances[owner];
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = _badgeOwners[tokenId];
        require(owner != address(0), "Invalid token");
        return owner;
    }

    function hasBadge(address voter) external view returns (bool) {
        return _badgeBalances[voter] > 0;
    }

    function badgeTokenOf(address voter) external view returns (uint256) {
        uint256 tokenId = _badgeTokenIds[voter];
        require(tokenId != 0, "Badge not minted");
        return tokenId;
    }

    // 动态生成 SBT 元数据，使用项目统一配置的 SBT 图片和名称，不显示序号
    function tokenURI(uint256 tokenId) public view returns (string memory) {
        ownerOf(tokenId);

        // 使用底层 abi.encodePacked 纯动态拼接
        bytes memory json = abi.encodePacked(
            '{"name":"', electionName, '",',
            '"description":"Soulbound commemorative badge for voting in \'', electionName, '\'.",',
            '"image":"https://gateway.pinata.cloud/ipfs/', sbtImageCid, '",',
            '"attributes":[',
                '{"trait_type":"Project","value":"', electionName, '"},',
                '{"trait_type":"Badge Type","value":"Soulbound"}'
            ']}'
        );

        return string(abi.encodePacked(
            "data:application/json;base64,",
            Base64.encode(json)
        ));
    }

    function approve(address, uint256) external pure { revert("Soulbound: non-transferable"); }
    function setApprovalForAll(address, bool) external pure { revert("Soulbound: non-transferable"); }
    function getApproved(uint256) external pure returns (address) { return address(0); }
    function isApprovedForAll(address, address) external pure returns (bool) { return false; }
    function transferFrom(address, address, uint256) external pure { revert("Soulbound: non-transferable"); }
    function safeTransferFrom(address, address, uint256) external pure { revert("Soulbound: non-transferable"); }
    function safeTransferFrom(address, address, uint256, bytes calldata) external pure { revert("Soulbound: non-transferable"); }

    function _mintBadge(address to) internal returns (uint256 tokenId) {
        require(_badgeBalances[to] == 0, "Badge already minted");
        tokenId = uint256(uint160(to));
        _badgeOwners[tokenId] = to;
        _badgeBalances[to] = 1;
        _badgeTokenIds[to] = tokenId;
        emit Transfer(address(0), to, tokenId);
    }

    function _toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) { digits++; temp /= 10; }
        bytes memory buffer = new bytes(digits);
        while (value != 0) { digits--; buffer[digits] = bytes1(uint8(48 + uint256(value % 10))); value /= 10; }
        return string(buffer);
    }
}
