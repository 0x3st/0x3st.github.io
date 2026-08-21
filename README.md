# 吃货的运行时笔记

一个使用 [Quarto](https://quarto.org/) 构建的中文博客。

## 本地预览

```bash
quarto preview
```

## 构建

```bash
quarto render
```

静态站点会生成到 `_site/`。构建前会自动检查段落级英文译文；未修改的段落会复用已有译文，只把新增或变化的段落发送给翻译 API。

可使用 DeepSeek、OpenAI 或其他兼容 OpenAI Chat Completions 的服务：

```bash
# DeepSeek（默认模型：deepseek-chat）
export DEEPSEEK_API_KEY="..."

# 或 OpenAI（默认模型：gpt-4o-mini）
export OPENAI_API_KEY="..."

# 或自定义兼容服务
export TRANSLATION_API_KEY="..."
export TRANSLATION_API_BASE="https://example.com/v1"
export TRANSLATION_MODEL="model-name"
```

仅检查译文是否同步，不调用 API：

```bash
python3 scripts/update_translations.py --check
```

## 发布

配置好对应平台后，可选择：

```bash
# Quarto Pub
quarto publish quarto-pub

# GitHub Pages（需先创建 Git 仓库并配置远程仓库）
quarto publish gh-pages
```
