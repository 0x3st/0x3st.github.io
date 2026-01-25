# 530(0x3st) Blog

A reserved domain for 530. Some diary, journal, collections.

🌐 **Live site:** [by530.com](https://by530.com)

---

## 🛠️ Tech Stack

- **Static Site Generator:** [Jekyll](https://jekyllrb.com/)
- **Hosting:** [GitHub Pages](https://pages.github.com/)
- **CI/CD:** GitHub Actions

## 📁 Structure

```
├── _config.yml      # Site configuration
├── _layouts/        # Custom HTML layouts
├── _posts/          # Blog posts (markdown)
├── index.md         # Homepage
└── .github/         # GitHub Actions workflow
```

## ✍️ Writing a New Post

1. Create a new file in `_posts/` with format: `YYYY-MM-DD-post-title.md`
2. Add front matter:
   ```yaml
   ---
   layout: default
   title: Your Post Title
   ---
   ```
3. Write your content in Markdown
4. Push to `main` branch — the site will auto-deploy!

## 📄 License

MIT License
