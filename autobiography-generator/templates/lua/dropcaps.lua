-- dropcaps.lua — Pandoc Lua filter for chapter-opening drop caps
--
-- Applies \lettrine{F}{irst word} to the first paragraph after each
-- H1 (chapter) heading. Only active for LaTeX output.
-- EPUB drop caps are handled via CSS ::first-letter.
--
-- Usage: pandoc --lua-filter=templates/lua/dropcaps.lua
--
-- Requires: \usepackage{lettrine} in the LaTeX template

local chapter_start = false

function Header(el)
  if el.level == 1 then
    chapter_start = true
  end
  return el
end

function Para(el)
  if not chapter_start then
    return el
  end

  -- Only apply to LaTeX output
  if not FORMAT:match('latex') then
    chapter_start = false
    return el
  end

  chapter_start = false

  -- Extract the full text of the paragraph
  local text = pandoc.utils.stringify(el)

  -- Skip if paragraph is too short or starts with non-letter
  if #text < 2 then
    return el
  end

  local first_char = text:sub(1, 1)
  if not first_char:match('[A-Za-z]') then
    -- Non-letter start (number, quote mark, etc.) — skip drop cap
    return el
  end

  -- Find the end of the first word for small caps treatment
  local rest = text:sub(2)
  local sc_end = rest:find('%s')
  if sc_end then
    local sc_part = rest:sub(1, sc_end - 1)
    local remainder = rest:sub(sc_end)
    return pandoc.RawBlock('latex',
      string.format('\\lettrine{%s}{%s}%s', first_char, sc_part, remainder))
  else
    -- Single-word paragraph (unlikely but safe)
    return pandoc.RawBlock('latex',
      string.format('\\lettrine{%s}{%s}', first_char, rest))
  end
end
