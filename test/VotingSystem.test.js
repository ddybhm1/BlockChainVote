const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("VotingSystem", function () {
  let voting;
  let admin;
  let voter1;
  let voter2;
  let voter3;

  async function startVotingWindow() {
    const now = await time.latest();
    await voting.startVoting(now + 1, now + 3600);
    await time.increaseTo(now + 2);
  }

  beforeEach(async function () {
    [admin, voter1, voter2, voter3] = await ethers.getSigners();
    const VotingSystem = await ethers.getContractFactory("VotingSystem");
    voting = await VotingSystem.deploy(admin.address, "Test Election", "QmTestImageCid");
    await voting.waitForDeployment();
  });

  describe("candidate management", function () {
    it("allows the admin to add a candidate", async function () {
      await voting.addCandidate("Alice", "QmCID_Alice");

      const [name, cid, votes] = await voting.getCandidate(0);
      expect(name).to.equal("Alice");
      expect(cid).to.equal("QmCID_Alice");
      expect(votes).to.equal(0);
    });

    it("prevents non-admins from adding candidates", async function () {
      await expect(
        voting.connect(voter1).addCandidate("Alice", "QmCID")
      ).to.be.revertedWith("Not admin");
    });

    it("supports batch candidate creation", async function () {
      await voting.addCandidatesBatch(
        ["Alice", "Bob"],
        ["QmCID_A", "QmCID_B"]
      );

      expect(await voting.candidateCount()).to.equal(2);
    });

    it("blocks candidate changes once voting has started", async function () {
      await voting.addCandidate("Alice", "QmCID");
      await startVotingWindow();

      await expect(
        voting.addCandidate("Bob", "QmCID_B")
      ).to.be.revertedWith("Voting already started");
    });
  });

  describe("voter authorization", function () {
    it("authorizes a voter", async function () {
      await voting.authorizeVoter(voter1.address);

      expect(await voting.isAuthorized(voter1.address)).to.equal(true);
      expect(await voting.totalAuthorizedVoters()).to.equal(1);
    });

    it("cannot authorize the same voter twice", async function () {
      await voting.authorizeVoter(voter1.address);

      await expect(
        voting.authorizeVoter(voter1.address)
      ).to.be.revertedWith("Already authorized");
    });

    it("supports batch authorization", async function () {
      await voting.authorizeVotersBatch([voter1.address, voter2.address]);

      expect(await voting.isAuthorized(voter1.address)).to.equal(true);
      expect(await voting.isAuthorized(voter2.address)).to.equal(true);
      expect(await voting.totalAuthorizedVoters()).to.equal(2);
    });
  });

  describe("vote flow and soulbound badge", function () {
    beforeEach(async function () {
      await voting.addCandidatesBatch(["Alice", "Bob"], ["QmA", "QmB"]);
      await voting.authorizeVotersBatch([voter1.address, voter2.address]);
      await startVotingWindow();
    });

    it("allows an authorized voter to vote", async function () {
      await voting.connect(voter1).vote(0);

      expect(await voting.voteCount(0)).to.equal(1);
      expect(await voting.hasVoted(voter1.address)).to.equal(true);
    });

    it("mints a soulbound commemorative badge on vote", async function () {
      await expect(voting.connect(voter1).vote(0))
        .to.emit(voting, "BadgeMinted")
        .withArgs(voter1.address, 1, "2026 Election Witness Badge");

      expect(await voting.balanceOf(voter1.address)).to.equal(1);
      expect(await voting.ownerOf(1)).to.equal(voter1.address);
      expect(await voting.hasBadge(voter1.address)).to.equal(true);
      expect(await voting.badgeTokenOf(voter1.address)).to.equal(1);

      const tokenUri = await voting.tokenURI(1);
      expect(tokenUri).to.contain("data:application/json;base64,");
    });

    it("emits the Voted event", async function () {
      await expect(voting.connect(voter1).vote(0))
        .to.emit(voting, "Voted")
        .withArgs(voter1.address, 0);
    });

    it("prevents duplicate voting", async function () {
      await voting.connect(voter1).vote(0);

      await expect(
        voting.connect(voter1).vote(1)
      ).to.be.revertedWith("Already voted");
    });

    it("rejects unauthorized voters", async function () {
      await expect(
        voting.connect(voter3).vote(0)
      ).to.be.revertedWith("Not authorized");
    });

    it("keeps the SBT non-transferable", async function () {
      await voting.connect(voter1).vote(0);

      await expect(
        voting.connect(voter1).transferFrom(voter1.address, voter2.address, 1)
      ).to.be.revertedWith("Soulbound: non-transferable");
    });

    it("rejects votes after voting has ended", async function () {
      await voting.endVoting();

      await expect(
        voting.connect(voter1).vote(0)
      ).to.be.revertedWith("Voting not active");
    });

    it("returns correct candidate aggregates", async function () {
      await voting.connect(voter1).vote(0);
      await voting.connect(voter2).vote(1);

      const [names, cids, votes] = await voting.getAllCandidates();
      expect(names[0]).to.equal("Alice");
      expect(names[1]).to.equal("Bob");
      expect(cids[0]).to.equal("QmA");
      expect(votes[0]).to.equal(1);
      expect(votes[1]).to.equal(1);
    });

    it("returns correct voting status data", async function () {
      await voting.connect(voter1).vote(0);

      const [started, ended, candidates, voters, voted] = await voting.getVotingStatus();
      expect(started).to.equal(true);
      expect(ended).to.equal(false);
      expect(candidates).to.equal(2);
      expect(voters).to.equal(2);
      expect(voted).to.equal(1);
    });
  });
});
