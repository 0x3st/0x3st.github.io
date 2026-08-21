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

静态站点会生成到 `_site/`。构建前会自动识别文章的主要语言：中文原文生成英文译文，英文原文生成简体中文译文。未修改的段落会复用已有译文，只翻译新增或变化的段落。

语言通常无需配置；如自动识别不符合预期，可在文章 YAML 中指定：

```yaml
translation-source: en  # 可选 en 或 zh
```

不希望翻译某篇文章时使用 `translation: false`。

### 使用本地 DLX（优先）

[DLX](https://github.com/OwO-Network/DLX)（原 DeepLX）是非官方的本地翻译 API 网关。它在本地运行服务，但正文仍会发送至 DeepL，并非离线翻译。

```bash
docker run -d --rm \
  -p 127.0.0.1:1188:1188 \
  ghcr.io/owo-network/deeplx:latest

quarto render
```

脚本会自动检测 `http://127.0.0.1:1188/translate`。也可通过 `DLX_URL` 指定其他地址。

发布时临时启动 DLX、更新译文并在结束后关闭：

```bash
scripts/publish_with_dlx.sh
```

该命令需要本机安装 `deeplx` 可执行文件或 Docker。如果译文没有变化，则不会启动 DLX。需要代理时可设置 `DLX_PROXY`（例如 `http://127.0.0.1:7890`）；临时服务只绑定到 `127.0.0.1`，不会暴露到局域网。

### API 回退

本地 DLX 未运行时，也可使用 DeepSeek、OpenAI 或其他兼容 OpenAI Chat Completions 的服务：

```bash
export DEEPSEEK_API_KEY="..."      # 默认 deepseek-chat
# 或：export OPENAI_API_KEY="..."  # 默认 gpt-4o-mini

# 自定义兼容服务
export TRANSLATION_API_KEY="..."
export TRANSLATION_API_BASE="https://example.com/v1"
export TRANSLATION_MODEL="model-name"
```

仅检查译文是否同步，不调用任何翻译服务：

```bash
python3 scripts/update_translations.py --check
```

## 发布

配置好对应平台后，可选择：

```bash
# Quarto Pub
quarto publish quarto-pub

# GitHub Pages（自动检查译文并按需临时启动 DLX）
scripts/publish_with_dlx.sh
```
