# Markdown-only Blog

A simple, elegant blogging system using pure markdown files and GitHub Actions.

## 📁 Project Structure

```
├── _posts/              # Your raw markdown articles (write here!)
├── _templates/          # Header and footer templates
│   ├── header.md
│   └── footer.md
├── posts/               # Generated processed articles (auto-generated)
├── .github/
│   └── workflows/
│       └── deploy.yml   # GitHub Actions workflow
├── build.py             # Build script
├── config.json          # Site configuration
└── README.md            # This file (auto-generated)
```

## 🚀 Getting Started

1. **Write articles**: Create markdown files in `_posts/` directory
2. **Push to GitHub**: Commit and push your changes
3. **Automatic build**: GitHub Actions will automatically run `build.py`
4. **Done!**: Your blog is updated

## 🛠️ Local Development

To build the blog locally:

```bash
python build.py
```

This will:
- Clean and recreate the `posts/` directory
- Process all articles in `_posts/`
- Combine each article with header and footer templates
- Generate a new `README.md` with the article index

## 📝 Writing Articles

1. Create a new markdown file in `_posts/` (e.g., `2026-01-26-my-article.md`)
2. Write your content in markdown
3. The build script will automatically add header and footer
4. Links in templates (like `[Home](../README.md)`) are relative-path safe

## ⚙️ Configuration

Edit `config.json` to customize:
- `site_title`: Your blog's title
- `site_description`: A brief description

## 📦 What Gets Generated

- **`posts/`**: Processed articles with header and footer
- **`README.md`**: Homepage with sorted article index (newest first)

## 🔧 Customization

- **Header**: Edit `_templates/header.md` for navigation and branding
- **Footer**: Edit `_templates/footer.md` for copyright and links
- **Styling**: Since this is markdown, you can use GitHub's built-in markdown rendering

## 📄 License

This project is dual-licensed under **MIT License** and **[Anti-996 License](https://github.com/996icu/996.ICU)**.

[![996.icu](https://img.shields.io/badge/link-996.icu-red.svg)](https://996.icu)
[![LICENSE](https://img.shields.io/badge/license-Anti%20996-blue.svg)](https://github.com/996icu/996.ICU/blob/master/LICENSE)

- ✅ Free to use, modify, and distribute
- ❌ Cannot be used by organizations enforcing "996" or involuntary overtime
- 💪 Support workers' rights and healthy work-life balance

See [LICENSE](LICENSE) for full details.
