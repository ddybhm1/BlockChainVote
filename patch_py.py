import os
import re

with open('create_admin.js', 'r', encoding='utf-8') as f:
    t = f.read()

# extract template part
content = t.split('const fullContent = `')[1].split('`;\nconst fs = require')[0]

with open('frontend/src/views/AdminView.vue', 'w', encoding='utf-8') as fw:
    fw.write(content)
