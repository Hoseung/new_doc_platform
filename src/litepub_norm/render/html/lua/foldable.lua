--[[
Lua filter for converting foldable Divs to HTML details/summary elements.

Converts:
  Div with class "foldable" and attributes:
    - data-title: summary text (required)
    - data-collapsed: "true" or "false" (optional, default "true")

To:
  <details open?>
    <summary>data-title</summary>
    ...content...
  </details>
]]

-- Only apply to HTML output
if FORMAT:match 'html' then

  function Div(el)
    -- Check if this is a foldable div
    if el.classes:includes('foldable') or el.classes:includes('foldable-code') then
      -- Get attributes
      local title = el.attributes['data-title'] or 'Details'
      local collapsed = el.attributes['data-collapsed'] or 'true'

      -- Build the open attribute
      local open_attr = ''
      if collapsed == 'false' then
        open_attr = ' open'
      end

      -- Preserve semantic ID if present
      local id_attr = ''
      if el.identifier and el.identifier ~= '' then
        id_attr = ' id="' .. el.identifier .. '"'
      end

      -- Build additional classes
      local classes = {}
      for _, cls in ipairs(el.classes) do
        table.insert(classes, cls)
      end
      local class_attr = ''
      if #classes > 0 then
        class_attr = ' class="' .. table.concat(classes, ' ') .. '"'
      end

      -- Create HTML structure
      local html_start = '<details' .. id_attr .. class_attr .. open_attr .. '>'
      local html_summary = '<summary>' .. title .. '</summary>'
      local html_end = '</details>'

      -- Return the transformed content
      return {
        pandoc.RawBlock('html', html_start .. html_summary),
        pandoc.Div(el.content),
        pandoc.RawBlock('html', html_end)
      }
    end

    -- Pass through non-foldable divs
    return el
  end

end
