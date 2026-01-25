---
layout: default
title: Home
---

## 📂 Articles {#articles}

{% for post in site.posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) - {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}

---

## ℹ️ About {#about}

Welcome to {{ site.title }}!

This is a simple, elegant blog powered by markdown files and GitHub Pages. No complex build tools needed - just write markdown and push to GitHub.

### Features

- ✅ Pure Markdown writing experience
- ✅ Automatic dark/light mode
- ✅ Mobile responsive design
- ✅ Fast and lightweight
- ✅ Free hosting on GitHub Pages
