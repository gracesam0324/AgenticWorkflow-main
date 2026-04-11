-- scene-breaks.lua — Pandoc Lua filter for styled scene breaks
--
-- Converts horizontal rules (---) to styled scene break markers
-- appropriate for each output format.
--
-- In Markdown:  ---  (between paragraphs)
-- In LaTeX:     \scenebreak
-- In HTML/EPUB: <div class="scene-break">...</div>
--
-- Usage: pandoc --lua-filter=templates/lua/scene-breaks.lua

function HorizontalRule()
  if FORMAT:match 'latex' then
    return pandoc.RawBlock('latex', '\\scenebreak')
  elseif FORMAT:match 'epub' or FORMAT:match 'html' then
    return pandoc.RawBlock('html',
      '<div class="scene-break">\226\128\162\226\128\131\226\128\162\226\128\131\226\128\162</div>')
  end
  -- For other formats, keep the default horizontal rule
end
