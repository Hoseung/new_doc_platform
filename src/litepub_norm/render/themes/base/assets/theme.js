/**
 * LitePub Base Theme JavaScript
 *
 * Provides optional interactive features:
 * - Foldable sections toggle
 * - TOC active section highlighting
 * - Copy code button (optional)
 */

(function() {
  'use strict';

  // ==========================================================================
  // Foldable Sections
  // ==========================================================================

  /**
   * Initialize foldable sections with click-to-toggle behavior.
   * Works with div.foldable > .foldable-header + .foldable-content
   */
  function initFoldables() {
    const foldables = document.querySelectorAll('.foldable:not(details)');

    foldables.forEach(function(foldable) {
      const header = foldable.querySelector('.foldable-header');
      if (!header) return;

      header.addEventListener('click', function() {
        foldable.classList.toggle('open');
      });

      // Set aria attributes for accessibility
      const content = foldable.querySelector('.foldable-content');
      if (content) {
        const id = content.id || 'foldable-' + Math.random().toString(36).substr(2, 9);
        content.id = id;
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', foldable.classList.contains('open'));
        header.setAttribute('aria-controls', id);

        // Update aria-expanded on toggle
        header.addEventListener('click', function() {
          header.setAttribute('aria-expanded', foldable.classList.contains('open'));
        });
      }
    });
  }

  // ==========================================================================
  // TOC Active Section Highlighting
  // ==========================================================================

  /**
   * Highlight the current section in the table of contents.
   */
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
      const offset = 100; // Offset from top of viewport

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

    // Debounce scroll handler
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
  // Copy Code Button (Optional)
  // ==========================================================================

  /**
   * Add copy-to-clipboard buttons to code blocks.
   */
  function initCopyCode() {
    const codeBlocks = document.querySelectorAll('#lp-content pre > code');

    codeBlocks.forEach(function(codeBlock) {
      const pre = codeBlock.parentElement;

      // Create copy button
      const button = document.createElement('button');
      button.className = 'copy-code-button';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');

      button.addEventListener('click', function() {
        const text = codeBlock.textContent;
        navigator.clipboard.writeText(text).then(function() {
          button.textContent = 'Copied!';
          setTimeout(function() {
            button.textContent = 'Copy';
          }, 2000);
        }).catch(function() {
          button.textContent = 'Failed';
          setTimeout(function() {
            button.textContent = 'Copy';
          }, 2000);
        });
      });

      // Position the button
      pre.style.position = 'relative';
      button.style.cssText = 'position: absolute; top: 0.5rem; right: 0.5rem; ' +
        'padding: 0.25rem 0.5rem; font-size: 0.75rem; ' +
        'background: var(--color-background, #fff); ' +
        'border: 1px solid var(--color-border, #e1e4e8); ' +
        'border-radius: 3px; cursor: pointer; opacity: 0; transition: opacity 0.2s;';

      pre.appendChild(button);

      // Show button on hover
      pre.addEventListener('mouseenter', function() {
        button.style.opacity = '1';
      });
      pre.addEventListener('mouseleave', function() {
        button.style.opacity = '0';
      });
    });
  }

  // ==========================================================================
  // Smooth Scroll for TOC Links
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
          // Update URL hash without jumping
          history.pushState(null, null, href);
        }
      });
    });
  }

  // ==========================================================================
  // Initialize on DOM Ready
  // ==========================================================================

  function init() {
    initFoldables();
    initTocHighlight();
    initSmoothScroll();

    // Only enable copy code if clipboard API is available
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
