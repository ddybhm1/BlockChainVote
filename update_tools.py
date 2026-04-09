import os, glob

for f in glob.glob("/home/mike/BlockChainVote/backend/tools/*.py"):
    with open(f, 'r') as file:
        content = file.read()
    
    if "'/home/mike/BlockChainVote/backend'" in content:
        content = content.replace("'/home/mike/BlockChainVote/backend'", 
                                  "__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))")
        with open(f, 'w') as file:
            file.write(content)
