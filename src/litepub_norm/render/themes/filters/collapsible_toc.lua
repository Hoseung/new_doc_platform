-- collapsible_toc.lua
-- Lua filter for Pandoc: Transforms nested TOC lists into collapsible
-- <details>/<summary> elements for CSS-only expand/collapse behavior.
--
-- This filter processes the table-of-contents variable and wraps
-- nested <ul> elements in <details>/<summary> elements.
--
-- Usage: pandoc --lua-filter=collapsible_toc.lua --toc ...

-- Track if we're processing the TOC
local in_toc = false

-- Process the table of contents specifically
-- The TOC is passed via the $table-of-contents$ template variable
-- We need to process it as raw HTML since Pandoc generates it directly

function RawBlock(el)
  -- Only process HTML blocks that might be TOC content
  if el.format ~= "html" then
    return nil
  end

  -- Check if this looks like TOC content (contains toc- prefixed IDs)
  if el.text:match('id="toc%-') then
    -- Transform nested lists to use details/summary
    local html = el.text

    -- Pattern: Find <li> elements that have nested <ul>
    -- We want to wrap the nested <ul> in <details> and the <a> in <summary>
    html = html:gsub(
      '(<li>)(<a[^>]*>[^<]*</a>)(%s*<ul)',
      '%1<details class="toc-section" open>%2<summary></summary>%3'
    )

    -- Close the details tag before closing </li> for items with nested lists
    html = html:gsub('(</ul>)(</li>)', '%1</details>%2')

    return pandoc.RawBlock("html", html)
  end

  return nil
end

-- Note: Since Pandoc's TOC is generated at template time (not in the AST),
-- this filter may not be able to transform it directly.
-- A post-processing step or custom template may be needed instead.
