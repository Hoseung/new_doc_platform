-- pdf_callouts.lua
-- Lua filter for Pandoc: Maps AST Div classes to LaTeX environments
-- This bridges semantic Divs (info, warning, note, danger) to tcolorbox
-- environments defined in theme.sty (infobox, warningbox, dangerbox)

-- Class to LaTeX environment mapping
local class_to_env = {
  info = "infobox",
  note = "infobox",      -- note is an alias for info
  warning = "warningbox",
  caution = "warningbox", -- caution is an alias for warning
  danger = "dangerbox",
  error = "dangerbox",   -- error is an alias for danger
}

-- Process Div elements
function Div(el)
  -- Check if any class matches our callout types
  for _, class in ipairs(el.classes) do
    local env_name = class_to_env[class]
    if env_name then
      -- Wrap the Div content in the appropriate LaTeX environment
      -- We return a list: opening RawBlock, content blocks, closing RawBlock
      local result = {}

      -- Add opening environment
      table.insert(result, pandoc.RawBlock('latex', '\\begin{' .. env_name .. '}'))

      -- Add all content blocks from the Div
      for _, block in ipairs(el.content) do
        table.insert(result, block)
      end

      -- Add closing environment
      table.insert(result, pandoc.RawBlock('latex', '\\end{' .. env_name .. '}'))

      return result
    end
  end

  -- No matching class - pass through unchanged
  return nil
end
