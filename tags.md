---
layout: default
title: Tags
permalink: /tags/
---

# 🏷️ Tags

{% assign tags = site.tags | sort %}

<div class="tag-cloud" id="tag-cloud">
{% for tag in tags %}
<a href="javascript:void(0)" onclick="filterByTag('{{ tag[0] | slugify }}')" data-tag="{{ tag[0] | slugify }}">{{ tag[0] }} ({{ tag[1].size }})</a>
{% endfor %}
<a href="javascript:void(0)" onclick="filterByTag('all')" data-tag="all" class="show-all">All</a>
</div>

<p id="filter-info" style="display:none; margin: 1rem 0; font-style: italic;"></p>

<hr>

{% for tag in tags %}
<div class="tag-section" data-tag="{{ tag[0] | slugify }}">
<h2>{{ tag[0] }}</h2>
<ul>
{% for post in tag[1] %}
<li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> — {{ post.date | date: "%Y-%m-%d" }}</li>
{% endfor %}
</ul>
</div>
{% endfor %}

<script>
function filterByTag(tag) {
  const url = new URL(window.location);
  if (tag === 'all') {
    url.searchParams.delete('tag');
  } else {
    url.searchParams.set('tag', tag);
  }
  window.history.pushState({}, '', url);
  applyFilter();
}

function applyFilter() {
  const params = new URLSearchParams(window.location.search);
  const selectedTag = params.get('tag');
  
  // Reset all sections
  document.querySelectorAll('.tag-section').forEach(section => {
    section.style.display = (selectedTag && selectedTag !== 'all') ? 'none' : 'block';
  });
  
  // Reset tag highlighting
  document.querySelectorAll('.tag-cloud a').forEach(a => {
    a.style.fontWeight = '';
    a.style.textDecoration = '';
  });
  
  const filterInfo = document.getElementById('filter-info');
  
  if (selectedTag && selectedTag !== 'all') {
    // Show only matching section
    const matchingSection = document.querySelector(`.tag-section[data-tag="${selectedTag}"]`);
    if (matchingSection) {
      matchingSection.style.display = 'block';
    }
    
    // Show filter info
    filterInfo.style.display = 'block';
    filterInfo.innerHTML = `Showing posts tagged with "<strong>${selectedTag}</strong>" — <a href="javascript:void(0)" onclick="filterByTag('all')">show all</a>`;
    
    // Highlight selected tag
    document.querySelectorAll('.tag-cloud a').forEach(a => {
      if (a.dataset.tag === selectedTag) {
        a.style.fontWeight = 'bold';
        a.style.textDecoration = 'underline';
      }
    });
  } else {
    filterInfo.style.display = 'none';
  }
}

// Apply filter on page load
applyFilter();

// Handle browser back/forward
window.addEventListener('popstate', applyFilter);
</script>
