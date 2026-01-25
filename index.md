---
layout: default
title: by530 Home Page
---

👋 **Hey there, welcome to my corner of the internet!**

I'm **Wu Lei**, an undergraduate student in Quantitative Finance at CUHK-Shenzhen. I write about things I find interesting — from Python automation to financial modeling, data analysis, and random thoughts on life.

---

## 📂 Latest Articles {#articles}

{% for post in site.posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.tags.size > 0 %} · {% for tag in post.tags %}`{{ tag }}`{% unless forloop.last %} {% endunless %}{% endfor %}{% endif %}
{% endfor %}

[🏷️ Browse by Tags]({{ '/tags/' | relative_url }})

---

## ℹ️ About {#about}

I love building tools that automate boring tasks and using data to uncover insights in financial markets.

- 🔭 **Currently working on:** [Nage](https://github.com/0x3st/nage) — an AI-assisted terminal tool
- 🌱 **Learning:** Machine Learning algorithms & Advanced Data Analysis
- 💬 **Ask me about:** Python, Financial Modeling, and Web Scraping

### 💻 Technical Skills

| Category | Tools |
|----------|-------|
| Languages | Python, SQL |
| Data Science | Pandas, NumPy, Matplotlib, Scikit-learn, BeautifulSoup |
| Dev Tools | Git, GitHub Actions, VS Code, Jupyter Notebooks |

### 📬 Connect

- GitHub: [@0x3st](https://github.com/0x3st)
- LinkedIn: [Wu Lei](https://www.linkedin.com/in/maybe-dr-lei-wu/)
- Twitter/X: [@0x00LW](https://twitter.com/0x00LW)
- Email: [findmethroughemail@gmail.com](mailto:530@linux.do)

---

## 📡 Subscribe {#subscribe}

Don't miss out on new posts! Subscribe via:

- 📰 **RSS Feed:** [feed.xml]({{ '/feed.xml' | relative_url }}) — Add to your favorite RSS reader([Follow](https://app.folo.is/share/feeds/238304858090830848) link is suggested)
- ⭐ **Star this repo:** [0x3st.github.io](https://github.com/0x3st/0x3st.github.io) — Get notified on GitHub

---

> *"Carpe diem."*