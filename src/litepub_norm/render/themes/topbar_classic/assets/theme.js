/**
 * LitePub Topbar Classic Theme JavaScript
 *
 * Features:
 * - TOC active section highlighting
 * - Foldable sections
 * - Smooth scrolling
 */

(function() {
  'use strict';

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

    const topbarHeight = 60;

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

      tocLinks.forEach(function(link) {
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
    const tocLinks = document.querySelectorAll('#lp-toc a[href^="#"]');
    const topbarHeight = 60;

    tocLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        const href = link.getAttribute('href');
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const top = target.offsetTop - topbarHeight - 10;
          window.scrollTo({ top: top, behavior: 'smooth' });
          history.pushState(null, null, href);
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
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code');

      button.addEventListener('click', function() {
        navigator.clipboard.writeText(codeBlock.textContent).then(function() {
          button.textContent = 'Copied!';
          setTimeout(function() {
            button.textContent = 'Copy';
          }, 2000);
        });
      });

      button.style.cssText = 'position: absolute; top: 8px; right: 8px; padding: 4px 10px; font-size: 0.75rem; font-family: var(--font-family-heading, sans-serif); background: #fff; border: 1px solid #ccc; border-radius: 3px; cursor: pointer; opacity: 0; transition: opacity 0.2s;';

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
