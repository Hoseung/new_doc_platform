/**
 * LitePub Sidebar Docs Theme JavaScript
 *
 * Features:
 * - Mobile sidebar toggle
 * - Collapsible TOC (top-level only by default)
 * - Active section highlighting in TOC
 * - Site navigation from sitemap.json
 * - Foldable sections
 * - Copy code buttons
 */

(function() {
  'use strict';

  // ==========================================================================
  // Mobile Sidebar Toggle
  // ==========================================================================

  function initSidebarToggle() {
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const overlay = document.querySelector('.sidebar-overlay');

    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', function() {
      document.body.classList.toggle('sidebar-open');
    });

    if (overlay) {
      overlay.addEventListener('click', function() {
        document.body.classList.remove('sidebar-open');
      });
    }

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
        document.body.classList.remove('sidebar-open');
      }
    });
  }

  // ==========================================================================
  // Collapsible TOC - Collapse nested items, show only top-level by default
  // ==========================================================================

  function initCollapsibleToc() {
    const toc = document.getElementById('lp-toc');
    if (!toc) return;

    // Find all nested ULs (children of LIs)
    const nestedLists = toc.querySelectorAll('li > ul');

    nestedLists.forEach(function(ul) {
      const parentLi = ul.parentElement;
      const parentLink = parentLi.querySelector(':scope > a');

      if (!parentLink) return;

      // Add collapsed class initially
      ul.classList.add('toc-collapsed');
      parentLi.classList.add('toc-has-children');

      // Create toggle button
      const toggle = document.createElement('button');
      toggle.className = 'toc-toggle';
      toggle.setAttribute('aria-label', 'Toggle subsections');
      toggle.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>';

      // Insert toggle before the link
      parentLi.insertBefore(toggle, parentLink);

      // Toggle on click
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        ul.classList.toggle('toc-collapsed');
        parentLi.classList.toggle('toc-expanded');
        toggle.classList.toggle('toc-open');
      });

      // Also expand when clicking the parent link if on same page
      parentLink.addEventListener('click', function() {
        // Expand the section when navigating to it
        ul.classList.remove('toc-collapsed');
        parentLi.classList.add('toc-expanded');
        toggle.classList.add('toc-open');
      });
    });

    // Expand the section containing the current page/anchor
    expandCurrentSection(toc);
  }

  function expandCurrentSection(toc) {
    // Find the active link based on current URL
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    const currentHash = window.location.hash;

    const allLinks = toc.querySelectorAll('a');
    let activeLink = null;

    allLinks.forEach(function(link) {
      const href = link.getAttribute('href') || '';

      // Check if this link matches current page
      if (href.includes(currentPath) || (currentHash && href === currentHash)) {
        activeLink = link;
        link.classList.add('active');
      }
    });

    // Expand all parent sections of active link
    if (activeLink) {
      let parent = activeLink.parentElement;
      while (parent && parent !== toc) {
        if (parent.tagName === 'UL' && parent.classList.contains('toc-collapsed')) {
          parent.classList.remove('toc-collapsed');
          const parentLi = parent.parentElement;
          parentLi.classList.add('toc-expanded');
          // Also update the toggle button state
          const toggle = parentLi.querySelector(':scope > .toc-toggle');
          if (toggle) {
            toggle.classList.add('toc-open');
          }
        }
        parent = parent.parentElement;
      }
    }
  }

  // ==========================================================================
  // Load Navigation from sitemap.json (for site mode chapter pages)
  // ==========================================================================

  function initSiteNavigation() {
    const sidebar = document.getElementById('lp-sidebar');
    if (!sidebar) return;

    let toc = document.getElementById('lp-toc');

    // If TOC already has content, just initialize collapsible behavior
    if (toc && toc.querySelector('ul')) {
      return;
    }

    // Try to load sitemap.json for navigation
    fetch('sitemap.json')
      .then(function(response) {
        if (!response.ok) throw new Error('No sitemap');
        return response.json();
      })
      .then(function(sitemap) {
        // Create TOC container if it doesn't exist
        if (!toc) {
          toc = document.createElement('nav');
          toc.id = 'lp-toc';
          toc.className = 'sidebar-toc';
          toc.setAttribute('role', 'doc-toc');
          sidebar.appendChild(toc);
        }

        const nav = buildNavFromSitemap(sitemap);
        toc.appendChild(nav);
        initCollapsibleToc(); // Initialize collapsible behavior
      })
      .catch(function() {
        // No sitemap available, that's OK
      });
  }

  function buildNavFromSitemap(sitemap, level) {
    level = level || 0;
    const ul = document.createElement('ul');

    if (sitemap.subsections && sitemap.subsections.length > 0) {
      sitemap.subsections.forEach(function(item) {
        const section = item.section;
        if (!section.title) return; // Skip empty titles

        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = section.path;
        a.textContent = section.title;

        // Mark current page as active
        const currentPath = window.location.pathname.split('/').pop() || 'index.html';
        if (section.path.includes(currentPath)) {
          a.classList.add('active');
        }

        li.appendChild(a);

        // Only show first 2 levels by default (chapters and sections)
        if (item.subsections && item.subsections.length > 0 && level < 2) {
          const childNav = buildNavFromSitemap(item, level + 1);
          li.appendChild(childNav);
        }

        ul.appendChild(li);
      });
    }

    return ul;
  }

  // ==========================================================================
  // TOC Active Section Highlighting
  // ==========================================================================

  function initTocHighlight() {
    const toc = document.getElementById('lp-toc');
    if (!toc) return;

    const tocLinks = toc.querySelectorAll('a[href^="#"]');
    if (tocLinks.length === 0) return;

    const sections = [];
    tocLinks.forEach(function(link) {
      const href = link.getAttribute('href');
      const target = document.querySelector(href);
      if (target) {
        sections.push({ link: link, target: target });
      }
    });

    if (sections.length === 0) return;

    function updateActive() {
      const scrollY = window.scrollY;
      const offset = 100;

      let current = null;
      sections.forEach(function(section) {
        const top = section.target.offsetTop - offset;
        if (scrollY >= top) {
          current = section;
        }
      });

      tocLinks.forEach(function(link) {
        link.classList.remove('active');
      });

      if (current) {
        current.link.classList.add('active');

        // Expand parent section if collapsed
        let parent = current.link.parentElement;
        while (parent && parent !== toc) {
          if (parent.tagName === 'UL' && parent.classList.contains('toc-collapsed')) {
            parent.classList.remove('toc-collapsed');
            const parentLi = parent.parentElement;
            parentLi.classList.add('toc-expanded');
            const toggle = parentLi.querySelector(':scope > .toc-toggle');
            if (toggle) {
              toggle.classList.add('toc-open');
            }
          }
          parent = parent.parentElement;
        }
      }
    }

    let ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          updateActive();
          ticking = false;
        });
        ticking = true;
      }
    });

    updateActive();
  }

  // ==========================================================================
  // Foldable Sections
  // ==========================================================================

  function initFoldables() {
    const foldables = document.querySelectorAll('.foldable:not(details)');

    foldables.forEach(function(foldable) {
      const header = foldable.querySelector('.foldable-header');
      if (!header) return;

      header.addEventListener('click', function() {
        foldable.classList.toggle('open');
      });

      // Accessibility
      const content = foldable.querySelector('.foldable-content');
      if (content) {
        const id = content.id || 'foldable-' + Math.random().toString(36).substr(2, 9);
        content.id = id;
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', foldable.classList.contains('open'));
        header.setAttribute('aria-controls', id);
        header.setAttribute('tabindex', '0');

        header.addEventListener('click', function() {
          header.setAttribute('aria-expanded', foldable.classList.contains('open'));
        });

        // Keyboard support
        header.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            foldable.classList.toggle('open');
            header.setAttribute('aria-expanded', foldable.classList.contains('open'));
          }
        });
      }
    });
  }

  // ==========================================================================
  // Copy Code Button
  // ==========================================================================

  function initCopyCode() {
    const codeBlocks = document.querySelectorAll('#lp-content pre > code');

    codeBlocks.forEach(function(codeBlock) {
      const pre = codeBlock.parentElement;

      const button = document.createElement('button');
      button.className = 'copy-code-btn';
      button.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"/><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"/></svg>';
      button.setAttribute('aria-label', 'Copy code');
      button.title = 'Copy code';

      button.addEventListener('click', function() {
        navigator.clipboard.writeText(codeBlock.textContent).then(function() {
          button.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/></svg>';
          setTimeout(function() {
            button.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"/><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"/></svg>';
          }, 2000);
        });
      });

      // Style the button
      button.style.cssText = 'position: absolute; top: 8px; right: 8px; padding: 4px 8px; background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 4px; cursor: pointer; opacity: 0; transition: opacity 0.2s; color: #586069;';

      pre.style.position = 'relative';
      pre.appendChild(button);

      pre.addEventListener('mouseenter', function() {
        button.style.opacity = '1';
      });
      pre.addEventListener('mouseleave', function() {
        button.style.opacity = '0';
      });
    });
  }

  // ==========================================================================
  // Smooth Scroll
  // ==========================================================================

  function initSmoothScroll() {
    const tocLinks = document.querySelectorAll('#lp-toc a[href^="#"]');

    tocLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        const href = link.getAttribute('href');
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          history.pushState(null, null, href);

          // Close mobile sidebar after clicking link
          document.body.classList.remove('sidebar-open');
        }
      });
    });
  }

  // ==========================================================================
  // Initialize
  // ==========================================================================

  function init() {
    initSidebarToggle();
    initSiteNavigation(); // Load sitemap.json if needed
    initCollapsibleToc(); // Make TOC collapsible
    initTocHighlight();
    initFoldables();
    initSmoothScroll();

    if (navigator.clipboard) {
      initCopyCode();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
