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

静态站点会生成到 `_site/`。

## 发布

配置好对应平台后，可选择：

```bash
# Quarto Pub
quarto publish quarto-pub

# GitHub Pages（需先创建 Git 仓库并配置远程仓库）
quarto publish gh-pages
```
