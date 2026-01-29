#!/usr/bin/env python3
# 新建博客文章脚本（Python 版）
import os
import sys
import re
from datetime import datetime

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(SCRIPT_DIR, '_posts')

# 检查参数
if len(sys.argv) < 2:
    print('Usage: python new_post.py "文章标题" [tag1,tag2,tag3]')
    title = input('请输入文章标题: ').strip()
else:
    title = sys.argv[1].strip()

if not title:
    print('错误: 文章标题不能为空')
    sys.exit(1)

# 处理标签
if len(sys.argv) < 3:
    tags_input = input('请输入标签 (用逗号分隔，可留空): ').strip()
else:
    tags_input = sys.argv[2].strip()

# 生成文件名
DATE = datetime.now().strftime('%Y-%m-%d')
# 将标题转为文件名格式（小写，空格变短横线，移除特殊字符）
slug = re.sub(r'[^a-z0-9\u4e00-\u9fa5-]', '', title.lower().replace(' ', '-'))
filename = f"{DATE}-{slug}.md"
filepath = os.path.join(POSTS_DIR, filename)

# 检查文件是否已存在
if os.path.exists(filepath):
    print(f'错误: 文件已存在: {filepath}')
    sys.exit(1)

# 格式化标签
if tags_input:
    tags_formatted = ', '.join([tag.strip() for tag in tags_input.split(',') if tag.strip()])
    tags_line = f"tags: [{tags_formatted}]"
else:
    tags_line = ''

# 创建文章内容
content = f'''---
layout: default
title: {title}
{tags_line}
---

# {title}

'''

# 写入文件
os.makedirs(POSTS_DIR, exist_ok=True)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ 文章创建成功!\n\n📄 文件: {filepath}\n🔗 URL:  https://by530.com/{slug}.html\n")

# 可选：用 vim 打开编辑
try:
    os.system(f'vim "{filepath}"')
except Exception:
    pass
