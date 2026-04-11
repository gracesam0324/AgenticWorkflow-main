-- epigraphs.lua — Pandoc Lua filter for chapter epigraphs
--
-- Converts specially-classed blockquotes into formatted epigraphs.
--
-- Markdown syntax:
--   ::: {.epigraph}
--   The past is never dead. It's not even past.
--
--   --- William Faulkner
--   :::
--
-- Or using a Div with class:
--   <div class="epigraph">
--   Quote text here.
--
--   --- Attribution
--   </div>
--
-- Output:
--   LaTeX:     \epigraph{Quote text}{--- Attribution}
--   HTML/EPUB: <div class="epigraph"><p>...</p><p class="attribution">...</p></div>
--
-- Usage: pandoc --lua-filter=templates/lua/epigraphs.lua

function Div(el)
  -- Check if this div has the "epigraph" class
  if not el.classes:includes('epigraph') then
    return el
  end

  local quote_parts = {}
  local attribution = nil

  for _, block in ipairs(el.content) do
    if block.t == "Para" then
      local text = pandoc.utils.stringify(block)
      -- Check if this paragraph starts with an em-dash (attribution)
      if text:match('^[%—–%-]') then
        attribution = text:gsub('^[%—–%-]+%s*', '')
      else
        table.insert(quote_parts, text)
      end
    end
  end

  local quote_text = table.concat(quote_parts, '\n\n')

  if FORMAT:match('latex') then
    local attr = attribution and ('--- ' .. attribution) or ''
    return pandoc.RawBlock('latex',
      string.format('\\epigraph{%s}{%s}', quote_text, attr))
  elseif FORMAT:match('html') or FORMAT:match('epub') then
    local html = '<div class="epigraph">\n'
    html = html .. '  <p>' .. quote_text .. '</p>\n'
    if attribution then
      html = html .. '  <p class="attribution">&mdash; ' .. attribution .. '</p>\n'
    end
    html = html .. '</div>'
    return pandoc.RawBlock('html', html)
  end

  -- For other formats, return unchanged
  return el
end
