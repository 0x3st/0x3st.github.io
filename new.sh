#!/bin/bash
# 新建博客文章脚本
# Usage: ./new_post.sh "文章标题" [tag1,tag2,tag3]

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POSTS_DIR="$SCRIPT_DIR/_posts"

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./new_post.sh \"文章标题\" [tag1,tag2,tag3]${NC}"
    echo ""
    read -p "请输入文章标题: " TITLE
else
    TITLE="$1"
fi

if [ -z "$TITLE" ]; then
    echo "错误: 文章标题不能为空"
    exit 1
fi

# 处理标签
if [ -z "$2" ]; then
    read -p "请输入标签 (用逗号分隔，可留空): " TAGS_INPUT
else
    TAGS_INPUT="$2"
fi

# 生成文件名
DATE=$(date +%Y-%m-%d)
# 将标题转为文件名格式（小写，空格变短横线，移除特殊字符）
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9\u4e00-\u9fa5-]//g')
FILENAME="${DATE}-${SLUG}.md"
FILEPATH="$POSTS_DIR/$FILENAME"

# 检查文件是否已存在
if [ -f "$FILEPATH" ]; then
    echo "错误: 文件已存在: $FILEPATH"
    exit 1
fi

# 格式化标签
if [ -n "$TAGS_INPUT" ]; then
    # 将 "tag1,tag2" 转为 "[tag1, tag2]"
    TAGS_FORMATTED=$(echo "$TAGS_INPUT" | sed 's/,/, /g')
    TAGS_LINE="tags: [$TAGS_FORMATTED]"
else
    TAGS_LINE=""
fi

# 创建文章
cat > "$FILEPATH" << EOF
---
layout: default
title: $TITLE
${TAGS_LINE}
---

# $TITLE


EOF

echo ""
echo -e "${GREEN}✅ 文章创建成功!${NC}"
echo ""
echo "📄 文件: $FILEPATH"
echo "🔗 URL:  https://by530.com/${SLUG}.html"
echo ""

# 用 vim 打开编辑
vim "$FILEPATH"
