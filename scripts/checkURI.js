const { ethers } = require('hardhat');

async function main() {
    const factory = await ethers.getContractAt('ElectionFactory', '0x5FbDB2315678afecb367f032d93F642f64180aa3');
    const elections = await factory.getDeployedElections();
    if(elections.length === 0) {
        console.log('No elections found'); return;
    }
    const votingAddr = elections[0];
    const voting = await ethers.getContractAt('VotingSystem', votingAddr);
    try {
        const uri = await voting.tokenURI(1);
        console.log('URI:', uri.substring(0, 100) + '...');
        const jsonStr = Buffer.from(uri.split(',')[1], 'base64').toString('utf-8');
        console.log('\nJSON:', jsonStr);
        const jsonObj = JSON.parse(jsonStr);
        console.log('\nParsed JSON keys:', Object.keys(jsonObj));
        if(jsonObj.image) {
             const svg = Buffer.from(jsonObj.image.split(',')[1], 'base64').toString('utf-8');
             console.log('\nSVG starts with:', svg.substring(0, 50));
        }
    } catch(e) {
        console.error('Error fetching tokenURI 1:', e.message);
    }
}

main().catch(console.error);
