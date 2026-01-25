#!/usr/bin/env python3
"""
Markdown-only Blog Builder
Processes raw markdown articles and generates a static blog structure.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime


def load_config():
    """Load configuration from config.json if it exists."""
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"site_title": "My Blog", "site_description": "A markdown-only blog"}


def clean_and_create_posts_dir():
    """Delete and recreate the posts/ directory."""
    posts_dir = Path("posts")
    if posts_dir.exists():
        shutil.rmtree(posts_dir)
    posts_dir.mkdir(exist_ok=True)
    print(f"✓ Created clean posts/ directory")


def read_template(template_name):
    """Read a template file from _templates/."""
    template_path = Path("_templates") / template_name
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def process_article(article_path, header_content, footer_content):
    """
    Process a single article: combine with header and footer.
    Returns the processed content and the output filename.
    """
    # Read the article content
    with open(article_path, 'r', encoding='utf-8') as f:
        article_content = f.read()
    
    # Combine header + article + footer
    combined_content = f"{header_content}\n\n{article_content}\n\n{footer_content}"
    
    # Output filename (same as input)
    output_filename = article_path.name
    output_path = Path("posts") / output_filename
    
    # Write to posts/ directory
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    return output_filename


def generate_cname(config):
    """Generate CNAME file for custom domain if configured."""
    domain = config.get("domain", "").strip()
    if domain:
        with open("CNAME", 'w', encoding='utf-8') as f:
            f.write(domain)
        print(f"✓ Generated CNAME file for domain: {domain}")
        return True
    return False


def generate_readme(article_filenames, config):
    """
    Generate the README.md homepage with a list of articles.
    Articles are sorted by filename in descending order.
    """
    site_title = config.get("site_title", "My Blog")
    site_description = config.get("site_description", "")
    
    # Sort filenames in descending order
    sorted_filenames = sorted(article_filenames, reverse=True)
    
    # Build the article list
    article_links = []
    for filename in sorted_filenames:
        # Extract title from filename (remove .md extension)
        title = filename.replace('.md', '').replace('-', ' ').replace('_', ' ')
        article_links.append(f"- [{title}](posts/{filename})")
    
    # Build README content
    readme_content = f"""# {site_title}

{site_description}

## Articles

"""
    readme_content += "\n".join(article_links)
    readme_content += f"\n\n---\n\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # Write README.md
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ Generated README.md with {len(article_links)} articles")


def main():
    """Main build process."""
    print("Starting blog build process...\n")
    
    # Load configuration
    config = load_config()
    print(f"✓ Loaded configuration: {config['site_title']}")
    
    # Clean and recreate posts directory
    clean_and_create_posts_dir()
    
    # Load templates
    header_content = read_template("header.md")
    footer_content = read_template("footer.md")
    print(f"✓ Loaded templates (header: {len(header_content)} chars, footer: {len(footer_content)} chars)")
    
    # Process all articles in _posts/
    posts_dir = Path("_posts")
    if not posts_dir.exists():
        print("⚠ Warning: _posts/ directory does not exist!")
        posts_dir.mkdir(exist_ok=True)
        print("✓ Created _posts/ directory")
    
    article_files = list(posts_dir.glob("*.md"))
    if not article_files:
        print("⚠ Warning: No markdown files found in _posts/")
    
    processed_filenames = []
    for article_path in article_files:
        filename = process_article(article_path, header_content, footer_content)
        processed_filenames.append(filename)
        print(f"✓ Processed: {filename}")
    
    # Generate README.md
    generate_readme(processed_filenames, config)
    
    # Generate CNAME file for custom domain
    generate_cname(config)
    
    print(f"\n✅ Build completed successfully!")
    print(f"   - {len(processed_filenames)} articles processed")
    print(f"   - Output directory: posts/")
    print(f"   - Homepage: README.md")


if __name__ == "__main__":
    main()
