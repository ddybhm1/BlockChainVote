# -*- coding: utf-8 -*-
import re

with open(r'\\wsl.localhost\Ubuntu-20.04\home\mike\BlockChainVote\contracts\VotingSystem.sol', 'r', encoding='gbk') as f:
    text = f.read()

old_func_pattern = r'    // 动态生成 SBT 元数据。直接使用对应候选人的图片和宣言.*?data:application/json;base64.*?encode\(\)\);\n    \}'

new_func = r"""    // 动态生成 SBT 的 SVG
    function badgeImageURI(uint256 tokenId, string memory candidateName) public pure returns (string memory) {
        string memory svg = string.concat(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720" width="720" height="720">',
            '<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
            '<stop offset="0%" stop-color="#081826"/><stop offset="55%" stop-color="#0f3a57"/>',
            '<stop offset="100%" stop-color="#1fbf9f"/></linearGradient></defs>',
            '<rect width="720" height="720" rx="40" fill="url(#bg)"/>',
            '<circle cx="580" cy="130" r="92" fill="#fbbf24" opacity="0.18"/>',
            '<circle cx="150" cy="600" r="120" fill="#3b82f6" opacity="0.18"/>',
            '<text x="64" y="110" fill="#7dd3fc" font-size="28" font-family="sans-serif">Witness SBT</text>',
            '<text x="64" y="205" fill="#f8fafc" font-size="56" font-weight="bold" font-family="sans-serif">I Voted For</text>',
            '<text x="64" y="280" fill="#fbbf24" font-size="64" font-weight="bold" font-family="sans-serif">', candidateName, '</text>',
            '<rect x="64" y="460" width="592" height="148" rx="28" fill="#081826" stroke="#ffffff" opacity="0.34"/>',
            '<text x="96" y="520" fill="#f8fafc" font-size="26" font-family="sans-serif">Non-transferable commemorative badge</text>',
            '<text x="96" y="566" fill="#bbf7d0" font-size="24" font-family="sans-serif">One wallet - One vote - One memory</text>',
            '<text x="96" y="612" fill="#e2e8f0" font-size="24" font-family="sans-serif">Token #',
            _toString(tokenId),
            '</text></svg>'
        );
        return string.concat("data:image/svg+xml;base64,", Base64.encode(bytes(svg)));
    }

    // 动态生成 SBT 元数据
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        uint256 candidateId = badgeToCandidate[tokenId];
        Candidate memory c = candidates[candidateId];

        string memory manifestoPart = bytes(c.manifestoCid).length > 0 
            ? string.concat(',"external_url":"ipfs://', c.manifestoCid, '"') 
            : "";

        string memory json = string.concat(
            '{"name":"', electionName, ' Witness Badge #', _toString(tokenId), '",',
            '"description":"Soulbound commemorative badge for voting in ', electionName, '. Supported Candidate: ', c.name, '.",',
            '"image":"', badgeImageURI(tokenId, c.name), '"',
            manifestoPart,
            ',"attributes":[',
                '{"trait_type":"Project","value":"', electionName, '"},',
                '{"trait_type":"Supported Candidate","value":"', c.name, '"},',
                '{"trait_type":"Candidate Image CID","value":"', c.imageCid, '"},',
                '{"trait_type":"Badge Type","value":"Soulbound"}'
            ']}'
        );

        return string.concat("data:application/json;base64,", Base64.encode(bytes(json)));
    }"""

text = re.sub(old_func_pattern, new_func, text, flags=re.DOTALL)
with open(r'\\wsl.localhost\Ubuntu-20.04\home\mike\BlockChainVote\contracts\VotingSystem.sol', 'w', encoding='utf-8') as f:
    f.write(text)
