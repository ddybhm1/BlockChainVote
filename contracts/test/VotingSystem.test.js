const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("VotingSystem", function () {
  let voting, admin, voter1, voter2, voter3;

  beforeEach(async function () {
    [admin, voter1, voter2, voter3] = await ethers.getSigners();
    const VotingSystem = await ethers.getContractFactory("VotingSystem");
    voting = await VotingSystem.deploy();
    await voting.waitForDeployment();
  });

  describe("候选人管理", function () {
    it("管理员可以添加候选人", async function () {
      await voting.addCandidate("Alice", "QmCID_Alice");
      const [name, cid, votes] = await voting.getCandidate(0);
      expect(name).to.equal("Alice");
      expect(cid).to.equal("QmCID_Alice");
      expect(votes).to.equal(0);
    });

    it("非管理员不能添加候选人", async function () {
      await expect(
        voting.connect(voter1).addCandidate("Alice", "QmCID")
      ).to.be.revertedWith("Not admin");
    });

    it("可以批量添加候选人", async function () {
      await voting.addCandidatesBatch(
        ["Alice", "Bob"],
        ["QmCID_A", "QmCID_B"]
      );
      expect(await voting.candidateCount()).to.equal(2);
    });

    it("投票开始后不能添加候选人", async function () {
      await voting.addCandidate("Alice", "QmCID");
      await voting.startVoting();
      await expect(
        voting.addCandidate("Bob", "QmCID_B")
      ).to.be.revertedWith("Voting already started");
    });
  });

  describe("选民授权", function () {
    it("管理员可以授权选民", async function () {
      await voting.authorizeVoter(voter1.address);
      expect(await voting.isAuthorized(voter1.address)).to.be.true;
      expect(await voting.totalAuthorizedVoters()).to.equal(1);
    });

    it("不能重复授权", async function () {
      await voting.authorizeVoter(voter1.address);
      await expect(
        voting.authorizeVoter(voter1.address)
      ).to.be.revertedWith("Already authorized");
    });

    it("可以批量授权", async function () {
      await voting.authorizeVotersBatch([voter1.address, voter2.address]);
      expect(await voting.isAuthorized(voter1.address)).to.be.true;
      expect(await voting.isAuthorized(voter2.address)).to.be.true;
      expect(await voting.totalAuthorizedVoters()).to.equal(2);
    });
  });

  describe("投票流程", function () {
    beforeEach(async function () {
      await voting.addCandidatesBatch(["Alice", "Bob"], ["QmA", "QmB"]);
      await voting.authorizeVotersBatch([voter1.address, voter2.address]);
      await voting.startVoting();
    });

    it("授权选民可以投票", async function () {
      await voting.connect(voter1).vote(0);
      expect(await voting.voteCount(0)).to.equal(1);
      expect(await voting.hasVoted(voter1.address)).to.be.true;
    });

    it("不能重复投票", async function () {
      await voting.connect(voter1).vote(0);
      await expect(
        voting.connect(voter1).vote(1)
      ).to.be.revertedWith("Already voted");
    });

    it("未授权地址不能投票", async function () {
      await expect(
        voting.connect(voter3).vote(0)
      ).to.be.revertedWith("Not authorized");
    });

    it("投票触发 Voted 事件", async function () {
      await expect(voting.connect(voter1).vote(0))
        .to.emit(voting, "Voted")
        .withArgs(voter1.address, 0);
    });

    it("投票结束后不能投票", async function () {
      await voting.endVoting();
      await expect(
        voting.connect(voter1).vote(0)
      ).to.be.revertedWith("Voting not active");
    });

    it("getAllCandidates 返回正确数据", async function () {
      await voting.connect(voter1).vote(0);
      await voting.connect(voter2).vote(1);

      const [names, cids, votes] = await voting.getAllCandidates();
      expect(names[0]).to.equal("Alice");
      expect(names[1]).to.equal("Bob");
      expect(votes[0]).to.equal(1);
      expect(votes[1]).to.equal(1);
    });

    it("getVotingStatus 返回正确状态", async function () {
      await voting.connect(voter1).vote(0);
      const [started, ended, candidates, voters, voted] =
        await voting.getVotingStatus();
      expect(started).to.be.true;
      expect(ended).to.be.false;
      expect(candidates).to.equal(2);
      expect(voters).to.equal(2);
      expect(voted).to.equal(1);
    });
  });
});
