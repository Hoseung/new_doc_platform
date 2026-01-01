/**
 * LitePub Norm - Theme JavaScript
 *
 * Handles interactive features:
 * - Foldable sections (already handled by <details>)
 * - Anchor link generation
 * - Code copy buttons (optional)
 */

(function() {
  'use strict';

  /**
   * Add anchor links to headings
   */
  function addAnchorLinks() {
    const headings = document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]');

    headings.forEach(function(heading) {
      const link = document.createElement('a');
      link.href = '#' + heading.id;
      link.className = 'anchor-link';
      link.setAttribute('aria-hidden', 'true');
      link.textContent = '#';
      link.style.cssText = 'opacity: 0; margin-left: 0.5em; text-decoration: none; color: #999;';

      heading.appendChild(link);

      heading.addEventListener('mouseenter', function() {
        link.style.opacity = '1';
      });

      heading.addEventListener('mouseleave', function() {
        link.style.opacity = '0';
      });
    });
  }

  /**
   * Add copy buttons to code blocks
   */
  function addCodeCopyButtons() {
    const codeBlocks = document.querySelectorAll('pre > code');

    codeBlocks.forEach(function(codeBlock) {
      const pre = codeBlock.parentElement;

      // Create button
      const button = document.createElement('button');
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.style.cssText = 'position: absolute; top: 0.5em; right: 0.5em; padding: 0.25em 0.5em; font-size: 0.75rem; background: #fff; border: 1px solid #ddd; border-radius: 3px; cursor: pointer; opacity: 0; transition: opacity 0.2s;';

      // Wrap pre in container for positioning
      const wrapper = document.createElement('div');
      wrapper.style.position = 'relative';
      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);
      wrapper.appendChild(button);

      // Show/hide on hover
      wrapper.addEventListener('mouseenter', function() {
        button.style.opacity = '1';
      });

      wrapper.addEventListener('mouseleave', function() {
        button.style.opacity = '0';
      });

      // Copy on click
      button.addEventListener('click', function() {
        navigator.clipboard.writeText(codeBlock.textContent).then(function() {
          button.textContent = 'Copied!';
          setTimeout(function() {
            button.textContent = 'Copy';
          }, 2000);
        }).catch(function(err) {
          console.error('Failed to copy:', err);
          button.textContent = 'Failed';
        });
      });
    });
  }

  /**
   * Smooth scroll for anchor links
   */
  function enableSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
      anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href').slice(1);
        const target = document.getElementById(targetId);

        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });

          // Update URL without jumping
          history.pushState(null, null, '#' + targetId);
        }
      });
    });
  }

  /**
   * Expand all foldables
   */
  function expandAllFoldables() {
    document.querySelectorAll('details').forEach(function(details) {
      details.open = true;
    });
  }

  /**
   * Collapse all foldables
   */
  function collapseAllFoldables() {
    document.querySelectorAll('details').forEach(function(details) {
      details.open = false;
    });
  }

  /**
   * Initialize on DOM ready
   */
  function init() {
    addAnchorLinks();
    addCodeCopyButtons();
    enableSmoothScroll();

    // Expose utilities globally for debugging/testing
    window.litepubTheme = {
      expandAllFoldables: expandAllFoldables,
      collapseAllFoldables: collapseAllFoldables
    };
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
