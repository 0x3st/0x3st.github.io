---
layout: default
title: Tags
permalink: /tags/
---

# 🏷️ Tags

{% assign tags = site.tags | sort %}

<div class="tag-cloud" id="tag-cloud">
{% for tag in tags %}
<a href="?tag={{ tag[0] | slugify }}" data-tag="{{ tag[0] | slugify }}">{{ tag[0] }} ({{ tag[1].size }})</a>
{% endfor %}
<a href="?" data-tag="all" class="show-all">All</a>
</div>

<p id="filter-info" style="display:none; margin: 1rem 0; font-style: italic;"></p>

---

{% for tag in tags %}
<div class="tag-section" data-tag="{{ tag[0] | slugify }}">

## {{ tag[0] }}

{% for post in tag[1] %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}

</div>
{% endfor %}

<script>
(function() {
  const params = new URLSearchParams(window.location.search);
  const selectedTag = params.get('tag');
  
  if (selectedTag && selectedTag !== 'all') {
    // Hide all sections
    document.querySelectorAll('.tag-section').forEach(section => {
      section.style.display = 'none';
    });
    
    // Show only matching section
    const matchingSection = document.querySelector(`.tag-section[data-tag="${selectedTag}"]`);
    if (matchingSection) {
      matchingSection.style.display = 'block';
      
      // Show filter info
      const filterInfo = document.getElementById('filter-info');
      filterInfo.style.display = 'block';
      filterInfo.innerHTML = `Showing posts tagged with "<strong>${selectedTag}</strong>" — <a href="?">show all</a>`;
    }
    
    // Highlight selected tag
    document.querySelectorAll('.tag-cloud a').forEach(a => {
      if (a.dataset.tag === selectedTag) {
        a.style.fontWeight = 'bold';
        a.style.textDecoration = 'underline';
      }
    });
  }
})();
</script>
