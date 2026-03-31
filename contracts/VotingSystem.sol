// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./utils/Base64.sol";

/// @title VotingSystem
/// @notice Anonymous voting with a soulbound commemorative badge minted after a successful vote
contract VotingSystem {
    using Base64 for bytes;

    address public admin;
    bool public votingStarted;
    bool public votingEnded;
    uint256 public votingStartTime;
    uint256 public votingEndTime;
    uint256 public candidateCount;
    uint256 public totalAuthorizedVoters;
    uint256 public totalVotesCast;

    string public constant name = "BlockChainVote Soulbound Badge";
    string public constant symbol = "BCVSBT";
    string public constant BADGE_EDITION = "2026";

    mapping(address => bool) public isAuthorized;
    mapping(address => bool) public hasVoted;
    mapping(uint256 => uint256) public voteCount;
    mapping(uint256 => string) public candidateCIDs;
    mapping(uint256 => string) public candidateNames;

    mapping(uint256 => address) private _badgeOwners;
    mapping(address => uint256) private _badgeBalances;
    mapping(address => uint256) private _badgeTokenIds;
    uint256 private _nextBadgeTokenId = 1;

    event VoterAuthorized(address indexed voter);
    event Voted(address indexed voter, uint256 indexed candidateId);
    event CandidateAdded(uint256 indexed candidateId, string name, string cid);
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

    // ==================== Admin ====================

    function addCandidate(string calldata _name, string calldata _cid)
        external
        onlyAdmin
        beforeVoting
    {
        require(bytes(_name).length > 0, "Empty name");
        require(bytes(_cid).length > 0, "Empty CID");

        uint256 id = candidateCount;
        candidateNames[id] = _name;
        candidateCIDs[id] = _cid;
        candidateCount++;

        emit CandidateAdded(id, _name, _cid);
    }

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

    function authorizeVoter(address _voter) external onlyAdmin {
        require(_voter != address(0), "Zero address");
        require(!isAuthorized[_voter], "Already authorized");

        isAuthorized[_voter] = true;
        totalAuthorizedVoters++;

        emit VoterAuthorized(_voter);
    }

    function authorizeVotersBatch(address[] calldata _voters) external onlyAdmin {
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
        voteCount[_candidateId]++;
        totalVotesCast++;

        uint256 mintedTokenId = _mintBadge(msg.sender);

        emit Voted(msg.sender, _candidateId);
        emit BadgeMinted(msg.sender, mintedTokenId, badgeDisplayName());
    }

    // ==================== Query ====================

    function getCandidate(uint256 _id)
        external
        view
        returns (string memory candidateName, string memory cid, uint256 votes)
    {
        require(_id < candidateCount, "Invalid candidate");
        return (candidateNames[_id], candidateCIDs[_id], voteCount[_id]);
    }

    function getAllCandidates()
        external
        view
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

    function getVotingStatus()
        external
        view
        returns (
            bool started,
            bool ended,
            uint256 candidates,
            uint256 voters,
            uint256 voted
        )
    {
        bool realEnded = votingEnded || (votingStarted && block.timestamp > votingEndTime);
        return (votingStarted, realEnded, candidateCount, totalAuthorizedVoters, totalVotesCast);
    }

    // ==================== Soulbound Badge ====================

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return
            interfaceId == 0x01ffc9a7 || // ERC165
            interfaceId == 0x80ac58cd || // ERC721
            interfaceId == 0x5b5e139f;   // ERC721Metadata
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

    function badgeDisplayName() public pure returns (string memory) {
        return string.concat(BADGE_EDITION, " Election Witness Badge");
    }

    function badgeDescription() public pure returns (string memory) {
        return "A soulbound commemorative badge minted immediately after a verified on-chain vote.";
    }

    function badgeImageURI(uint256 tokenId) public view returns (string memory) {
        ownerOf(tokenId);

        string memory svg = string.concat(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720">',
            '<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
            '<stop offset="0%" stop-color="#081826"/><stop offset="55%" stop-color="#0f3a57"/>',
            '<stop offset="100%" stop-color="#1fbf9f"/></linearGradient></defs>',
            '<rect width="720" height="720" rx="40" fill="url(#bg)"/>',
            '<circle cx="580" cy="130" r="92" fill="rgba(251,191,36,0.18)"/>',
            '<circle cx="150" cy="600" r="120" fill="rgba(59,130,246,0.18)"/>',
            '<text x="64" y="110" fill="#7dd3fc" font-size="28" font-family="Verdana">Soulbound Vote Badge</text>',
            '<text x="64" y="205" fill="#f8fafc" font-size="56" font-weight="700" font-family="Verdana">2026 Witness</text>',
            '<text x="64" y="270" fill="#dbeafe" font-size="30" font-family="Verdana">Vote recorded on-chain</text>',
            '<text x="64" y="390" fill="#fbbf24" font-size="120" font-weight="700" font-family="Verdana">SBT</text>',
            '<rect x="64" y="460" width="592" height="148" rx="28" fill="rgba(8,24,38,0.34)" stroke="rgba(255,255,255,0.18)"/>',
            '<text x="96" y="520" fill="#f8fafc" font-size="26" font-family="Verdana">Non-transferable commemorative badge</text>',
            '<text x="96" y="566" fill="#bbf7d0" font-size="24" font-family="Verdana">One wallet - One vote - One memory</text>',
            '<text x="96" y="612" fill="#e2e8f0" font-size="24" font-family="Verdana">Token #',
            _toString(tokenId),
            "</text></svg>"
        );

        return string.concat(
            "data:image/svg+xml;base64,",
            bytes(svg).encode()
        );
    }

    function tokenURI(uint256 tokenId) public view returns (string memory) {
        ownerOf(tokenId);

        string memory json = string.concat(
            '{"name":"',
            badgeDisplayName(),
            " #",
            _toString(tokenId),
            '","description":"',
            badgeDescription(),
            '","image":"',
            badgeImageURI(tokenId),
            '","attributes":[',
            '{"trait_type":"Edition","value":"',
            BADGE_EDITION,
            '"},',
            '{"trait_type":"Badge Type","value":"Soulbound"},',
            '{"trait_type":"Transferability","value":"Non-transferable"}',
            "]}"
        );

        return string.concat(
            "data:application/json;base64,",
            bytes(json).encode()
        );
    }

    function approve(address, uint256) external pure {
        revert("Soulbound: non-transferable");
    }

    function setApprovalForAll(address, bool) external pure {
        revert("Soulbound: non-transferable");
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        ownerOf(tokenId);
        return address(0);
    }

    function isApprovedForAll(address, address) external pure returns (bool) {
        return false;
    }

    function transferFrom(address, address, uint256) external pure {
        revert("Soulbound: non-transferable");
    }

    function safeTransferFrom(address, address, uint256) external pure {
        revert("Soulbound: non-transferable");
    }

    function safeTransferFrom(address, address, uint256, bytes calldata) external pure {
        revert("Soulbound: non-transferable");
    }

    function _mintBadge(address to) internal returns (uint256 tokenId) {
        require(_badgeBalances[to] == 0, "Badge already minted");

        tokenId = _nextBadgeTokenId;
        _nextBadgeTokenId++;

        _badgeOwners[tokenId] = to;
        _badgeBalances[to] = 1;
        _badgeTokenIds[to] = tokenId;

        emit Transfer(address(0), to, tokenId);
    }

    function _toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }

        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }

        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits--;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }

        return string(buffer);
    }
}
