// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./VotingSystem.sol";

/// @title ElectionFactory - 投票项目工厂合约
/// @notice 用工厂模式创建和管理多个独立投票项目，每个项目对应一个独立的 VotingSystem 合约
contract ElectionFactory {
    address public owner;

    struct ElectionInfo {
        address addr;
        string title;
        address creator;
        uint256 createdAt;
    }

    ElectionInfo[] public elections;
    mapping(address => bool) public isElection;

    event ElectionCreated(
        uint256 indexed index,
        address indexed electionAddr,
        string title,
        address indexed creator
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /// @notice 创建新的投票项目（仅 owner 可调用）
    function createElection(string calldata _title, string calldata _sbtImageCid) external onlyOwner returns (address) {
        require(bytes(_title).length > 0, "Empty title");
        
        VotingSystem election = new VotingSystem(msg.sender, _title, _sbtImageCid);
        address addr = address(election);

        elections.push(ElectionInfo({
            addr: addr,
            title: _title,
            creator: msg.sender,
            createdAt: block.timestamp
        }));
        isElection[addr] = true;

        emit ElectionCreated(elections.length - 1, addr, _title, msg.sender);
        return addr;
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
