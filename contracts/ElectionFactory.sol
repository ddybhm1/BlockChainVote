// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./VotingSystem.sol";

/// @title ElectionFactory - 投票项目工厂合约
/// @notice 用工厂模式创建和管理多个独立投票项目，每个项目对应一个独立的 VotingSystem 合约
contract ElectionFactory {
    address public owner;
    address public backendServerAddress;
    uint256 public createFee;
    bool public paused;

    struct ElectionInfo {
        address addr;
        string title;
        address creator;
        uint256 createdAt;
    }

    ElectionInfo[] public elections;
    mapping(address => bool) public isElection;
    mapping(address => mapping(bytes32 => bool)) private creatorTitleUsed;

    event ElectionCreated(
        uint256 indexed index,
        address indexed electionAddr,
        string title,
        address indexed creator
    );
    event CreateFeeUpdated(uint256 oldFee, uint256 newFee);
    event BackendServerAddressUpdated(address indexed oldAddress, address indexed newAddress);
    event TreasuryWithdrawn(address indexed to, uint256 amount);
    event FactoryPaused(bool paused);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Factory paused");
        _;
    }

    constructor(address _backendServerAddress) {
        require(_backendServerAddress != address(0), "Zero backend server");
        owner = msg.sender;
        backendServerAddress = _backendServerAddress;
        createFee = 0.005 ether;
        paused = false;
    }

    /// @notice 创建新的投票项目（需支付开站费）
    function createElection(string calldata _title, string calldata _sbtImageCid) external payable whenNotPaused returns (address) {
        require(bytes(_title).length > 0, "Empty title");
        require(msg.value >= createFee, "Insufficient create fee");
        bytes32 titleHash = keccak256(bytes(_title));
        require(!creatorTitleUsed[msg.sender][titleHash], "Duplicate title by creator");
        
        VotingSystem election = new VotingSystem(msg.sender, backendServerAddress, _title, _sbtImageCid);
        address addr = address(election);

        elections.push(ElectionInfo({
            addr: addr,
            title: _title,
            creator: msg.sender,
            createdAt: block.timestamp
        }));
        isElection[addr] = true;
        creatorTitleUsed[msg.sender][titleHash] = true;

        emit ElectionCreated(elections.length - 1, addr, _title, msg.sender);
        return addr;
    }

    function hasCreatorTitle(address _creator, string calldata _title) external view returns (bool) {
        return creatorTitleUsed[_creator][keccak256(bytes(_title))];
    }

    function setCreateFee(uint256 _newFee) external onlyOwner {
        uint256 oldFee = createFee;
        createFee = _newFee;
        emit CreateFeeUpdated(oldFee, _newFee);
    }

    function setBackendServerAddress(address _newAddress) external onlyOwner {
        require(_newAddress != address(0), "Zero backend server");
        address oldAddress = backendServerAddress;
        backendServerAddress = _newAddress;
        emit BackendServerAddressUpdated(oldAddress, _newAddress);
    }

    function setPaused(bool _paused) external onlyOwner {
        paused = _paused;
        emit FactoryPaused(_paused);
    }

    function withdrawTreasury(address payable _to, uint256 _amount) external onlyOwner {
        require(_to != address(0), "Zero address");
        require(_amount <= address(this).balance, "Insufficient treasury");
        (bool ok, ) = _to.call{value: _amount}("");
        require(ok, "Withdraw failed");
        emit TreasuryWithdrawn(_to, _amount);
    }

    /// @notice 获取所有投票项目数量
    function getElectionCount() external view returns (uint256) {
        return elections.length;
    }

    /// @notice 获取所有投票项目信息
    function getAllElections()
        external view
        returns (
            address[] memory addrs,
            string[] memory titles,
            address[] memory creators,
            uint256[] memory createdAts
        )
    {
        uint256 len = elections.length;
        addrs = new address[](len);
        titles = new string[](len);
        creators = new address[](len);
        createdAts = new uint256[](len);

        for (uint256 i = 0; i < len; i++) {
            addrs[i] = elections[i].addr;
            titles[i] = elections[i].title;
            creators[i] = elections[i].creator;
            createdAts[i] = elections[i].createdAt;
        }
    }
}
