/**
 * LitePub Book Tutorial Theme JavaScript
 *
 * Features:
 * - Mobile sidebar toggle
 * - "On This Page" TOC generation
 * - Active section highlighting
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

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
        document.body.classList.remove('sidebar-open');
      }
    });
  }

  // ==========================================================================
  // Generate "On This Page" TOC
  // ==========================================================================

  function initPageToc() {
    const pageTocNav = document.querySelector('.page-toc-nav');
    const content = document.getElementById('lp-content');

    if (!pageTocNav || !content) return;

    // Find all headings in content
    const headings = content.querySelectorAll('h2, h3');
    if (headings.length === 0) {
      // Hide page TOC if no headings
      const pageToc = document.querySelector('.page-toc');
      if (pageToc) pageToc.style.display = 'none';
      return;
    }

    const ul = document.createElement('ul');

    headings.forEach(function(heading, index) {
      // Ensure heading has an ID
      if (!heading.id) {
        heading.id = 'section-' + index;
      }

      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#' + heading.id;
      a.textContent = heading.textContent;

      // Indent h3
      if (heading.tagName === 'H3') {
        li.style.paddingLeft = '1rem';
      }

      li.appendChild(a);
      ul.appendChild(li);
    });

    pageTocNav.appendChild(ul);
  }

  // ==========================================================================
  // Active Section Highlighting (both TOCs)
  // ==========================================================================

  function initTocHighlight() {
    const chapterToc = document.getElementById('lp-toc');
    const pageTocNav = document.querySelector('.page-toc-nav');

    const allTocLinks = [];

    if (chapterToc) {
      chapterToc.querySelectorAll('a[href^="#"]').forEach(function(link) {
        allTocLinks.push(link);
      });
    }

    if (pageTocNav) {
      pageTocNav.querySelectorAll('a[href^="#"]').forEach(function(link) {
        allTocLinks.push(link);
      });
    }

    if (allTocLinks.length === 0) return;

    const sections = [];
    allTocLinks.forEach(function(link) {
      const href = link.getAttribute('href');
      const target = document.querySelector(href);
      if (target) {
        sections.push({ link: link, target: target });
      }
    });

    if (sections.length === 0) return;

    const topbarHeight = 56;

    function updateActive() {
      const scrollY = window.scrollY;
      const offset = topbarHeight + 20;

      let current = null;
      sections.forEach(function(section) {
        const top = section.target.offsetTop - offset;
        if (scrollY >= top) {
          current = section;
        }
      });

      allTocLinks.forEach(function(link) {
        link.classList.remove('active');
      });

      if (current) {
        current.link.classList.add('active');
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
  // Smooth Scroll
  // ==========================================================================

  function initSmoothScroll() {
    const allTocLinks = document.querySelectorAll('#lp-toc a[href^="#"], .page-toc-nav a[href^="#"]');
    const topbarHeight = 56;

    allTocLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        const href = link.getAttribute('href');
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const top = target.offsetTop - topbarHeight - 10;
          window.scrollTo({ top: top, behavior: 'smooth' });
          history.pushState(null, null, href);

          // Close mobile sidebar
          document.body.classList.remove('sidebar-open');
        }
      });
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
      button.innerHTML = 'Copy';
      button.setAttribute('aria-label', 'Copy code');

      button.addEventListener('click', function() {
        navigator.clipboard.writeText(codeBlock.textContent).then(function() {
          button.textContent = 'Copied!';
          setTimeout(function() {
            button.textContent = 'Copy';
          }, 2000);
        });
      });

      button.style.cssText = 'position: absolute; top: 8px; right: 8px; padding: 4px 12px; font-size: 0.75rem; background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; cursor: pointer; opacity: 0; transition: opacity 0.2s;';

      pre.style.position = 'relative';
      pre.appendChild(button);

      pre.addEventListener('mouseenter', function() { button.style.opacity = '1'; });
      pre.addEventListener('mouseleave', function() { button.style.opacity = '0'; });
    });
  }

  // ==========================================================================
  // Initialize
  // ==========================================================================

  function init() {
    initSidebarToggle();
    initPageToc();
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
