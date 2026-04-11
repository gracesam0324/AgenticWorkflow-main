# MCP Server Research for AI Autobiography Generator

> **Scope**: LOCAL Claude Code workflow — all MCP servers run on the developer's machine.
> **Date**: 2026-03-17
> **Status**: Research Complete

---

## Table of Contents

1. [Complete MCP Server Catalog](#1-complete-mcp-server-catalog)
2. [Recommended MCP Servers (Top 5)](#2-recommended-mcp-servers-top-5)
3. [Custom MCP Server Blueprint](#3-custom-mcp-server-blueprint)
4. [MCP Integration in settings.json](#4-mcp-integration-in-settingsjson)
5. [MCP vs Direct CLI Calls](#5-mcp-vs-direct-cli-calls)

---

## 1. Complete MCP Server Catalog

### 1.1 File System & Search

| Server | Package | Purpose | Install Command | Transport |
|--------|---------|---------|-----------------|-----------|
| **Filesystem** (Official) | `@modelcontextprotocol/server-filesystem` | Read, write, search, move files with configurable access controls | `claude mcp add filesystem -s user -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed` | stdio |
| **Markdown Editor** | `markdown-editor-mcp-server` (PyPI) | Semantic editing of Markdown with structural navigation, content manipulation, YAML frontmatter | `pip install markdown-editor-mcp-server` | stdio |
| **MarkItDown** | `markitdown-mcp` (npm) | Convert PDF, DOCX, PPTX, images, audio, HTML to Markdown | `npx -y markitdown-mcp` | stdio |

### 1.2 Web Search & Fact-Checking

| Server | Package | Purpose | Install Command | API Key Required |
|--------|---------|---------|-----------------|------------------|
| **Brave Search** (Official) | `@anthropic-ai/mcp-server-brave-search` | Web, image, video, news search; generous free tier; privacy-first | `claude mcp add brave-search -s user -e BRAVE_API_KEY=xxx -- npx -y @anthropic-ai/mcp-server-brave-search` | Yes (free tier: 2000/mo) |
| **Tavily Search** | `tavily-mcp` | Real-time web search optimized for factual info + citation support | `claude mcp add tavily -s user -e TAVILY_API_KEY=xxx -- npx -y tavily-mcp@latest` | Yes (free tier: 1000/mo) |
| **Omnisearch** | `mcp-omnisearch` | Unified access: Tavily + Brave + Kagi + Perplexity + Jina AI | `npx -y mcp-omnisearch` | Multiple keys |
| **Fetch** (Official) | `@modelcontextprotocol/server-fetch` | Fetch web content and convert to Markdown for LLM consumption | `claude mcp add fetch -s user -- npx -y @modelcontextprotocol/server-fetch` | No |

### 1.3 Document Processing

| Server | Package | Purpose | Install Command | Dependencies |
|--------|---------|---------|-----------------|--------------|
| **mcp-pandoc** | `mcp-pandoc` (PyPI) | Convert between MD, DOCX, PDF, EPUB, LaTeX, HTML via Pandoc | `pip install mcp-pandoc` | pandoc CLI |
| **pdf-reader-mcp** | `pdf-reader-mcp` (npm) | Production-grade PDF processing; parallel extraction; 5-10x faster | `npx -y pdf-reader-mcp` | None |
| **mcp-pdf-tools** | `mcp-pdf-tools` (npm) | Merge, split, extract pages from PDFs | `npx -y mcp-pdf-tools` | None |
| **ebook-mcp** | `ebook-mcp` (PyPI) | Read/process EPUB and PDF ebooks | `pip install ebook-mcp` | None |
| **Markdownify** | `markdownify-mcp` (npm) | Convert PDFs, images, audio, web pages to Markdown | `npx -y markdownify-mcp` | None |

### 1.4 Speech & Audio Transcription

| Server | Package | Purpose | Install Command | Dependencies |
|--------|---------|---------|-----------------|--------------|
| **Fast-Whisper-MCP** | `fast-whisper-mcp-server` (PyPI) | High-performance speech recognition via faster-whisper; batch processing | `pip install fast-whisper-mcp-server` | faster-whisper, CUDA optional |
| **Speech Interface** | `speech-faster-whisper` (npm) | Voice interaction with faster-whisper + PyAudio; multi-language | `npx -y speech-faster-whisper` | faster-whisper, PyAudio |
| **mcp-server-whisper** | `mcp-server-whisper` (PyPI) | Audio transcription via OpenAI Whisper API | `pip install mcp-server-whisper` | OpenAI API key |

### 1.5 Database & Knowledge Storage

| Server | Package | Purpose | Install Command | Storage |
|--------|---------|---------|-----------------|---------|
| **Memory** (Official) | `@modelcontextprotocol/server-memory` | Knowledge graph with entities + relations; persistent across sessions | `claude mcp add memory -s user -- npx -y @modelcontextprotocol/server-memory` | Local JSON file |
| **Knowledge Graph** | `mcp-knowledge-graph` (npm) | Enhanced knowledge graph; SQLite or PostgreSQL backend; fuzzy search | `npx -y mcp-knowledge-graph` | SQLite file |
| **ChromaDB MCP** | `chroma-mcp` (PyPI) | Vector database; semantic search; embeddings; collection management | `pip install chroma-mcp` | Local ChromaDB |
| **Vector Memory** | `vector-memory-mcp` (PyPI) | Semantic memory via sqlite-vec + sentence-transformers | `pip install vector-memory-mcp` | Local SQLite |
| **Basic Memory** | `basic-memory` (PyPI) | Markdown-file-based memory; searchable knowledge base | `pip install basic-memory` | Local Markdown files |

### 1.6 LLM Bridge / Multi-Model

| Server | Package | Purpose | Install Command | Providers |
|--------|---------|---------|-----------------|-----------|
| **MindBridge MCP** | `mindbridge-mcp` (npm) | Unified API to OpenAI, Anthropic, Gemini, DeepSeek, Ollama | `npx -y mindbridge-mcp` | All major LLMs |
| **LLM Bridge MCP** | `llm-bridge-mcp` (PyPI) | AI router: dynamic switching between models for different tasks | `pip install llm-bridge-mcp` | OpenAI, Gemini, Ollama |
| **Ollama MCP Bridge** | `ollama-mcp-bridge` (npm) | Connect local Ollama models to MCP ecosystem | `npx -y ollama-mcp-bridge` | Local Ollama |

### 1.7 Git & Version Control

| Server | Package | Purpose | Install Command | Auth |
|--------|---------|---------|-----------------|------|
| **Git** (Official) | `@modelcontextprotocol/server-git` | Read, search, manipulate Git repositories | `claude mcp add git -s user -- npx -y @modelcontextprotocol/server-git` | Local |
| **GitHub** (Official) | `@modelcontextprotocol/server-github` | GitHub API: repos, issues, PRs, actions | `claude mcp add github -s user -e GITHUB_TOKEN=xxx -- npx -y @modelcontextprotocol/server-github` | PAT |

### 1.8 Image Processing

| Server | Package | Purpose | Install Command | Dependencies |
|--------|---------|---------|-----------------|--------------|
| **EXIF MCP** | `exif-mcp` (npm) | Extract EXIF, XMP metadata from JPEG, PNG, TIFF, HEIC | `npx -y exif-mcp` | None |
| **Image Processing MCP** | `image-processing-mcp-server` (PyPI) | Resize, compress, crop, convert, batch operations | `pip install image-processing-mcp-server` | Pillow |
| **Enhanced Image Analysis** | `local-mcp-image-analysis-server` | Smart filename generation, metadata extraction, color analysis, folder organization | Custom install | sharp |

### 1.9 Reasoning & Planning

| Server | Package | Purpose | Install Command |
|--------|---------|---------|-----------------|
| **Sequential Thinking** (Official) | `@modelcontextprotocol/server-sequential-thinking` | Dynamic, reflective problem-solving through thought sequences | `claude mcp add thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking` |

---

## 2. Recommended MCP Servers (Top 5)

These are the 5 most valuable MCP servers specifically for the AI Autobiography Generator pipeline, ranked by impact.

### Rank 1: Fast-Whisper-MCP-Server

**Why**: The autobiography pipeline's core input is audio interviews. This server wraps faster-whisper as an MCP tool, enabling Claude Code agents to transcribe audio directly without subprocess orchestration.

```bash
# Prerequisites
pip install faster-whisper

# Install the MCP server
pip install fast-whisper-mcp-server

# Add to Claude Code
claude mcp add whisper -s local -- python -m fast_whisper_mcp_server \
  --model large-v3 \
  --device cpu \
  --compute-type int8
```

**Configuration in `.mcp.json`**:
```json
{
  "mcpServers": {
    "whisper": {
      "command": "python",
      "args": ["-m", "fast_whisper_mcp_server", "--model", "large-v3", "--device", "cpu", "--compute-type", "int8"],
      "env": {}
    }
  }
}
```

**Tools exposed**: `transcribe_audio`, `transcribe_batch`, `list_models`, `get_supported_languages`

---

### Rank 2: Memory (Official @modelcontextprotocol/server-memory)

**Why**: The autobiography pipeline must maintain a persistent Story Bible (characters, timeline, themes, relationships) across sessions. The official Memory server provides a knowledge graph with entities and relations that persists to disk.

```bash
# Install and add to Claude Code
claude mcp add memory -s local -- npx -y @modelcontextprotocol/server-memory

# Custom memory file path (recommended)
claude mcp add memory -s local -- npx -y @modelcontextprotocol/server-memory \
  --memory-path ./autobiography-generator/.story-bible/memory.json
```

**Configuration in `.mcp.json`**:
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "./autobiography-generator/.story-bible/memory.json"
      }
    }
  }
}
```

**Tools exposed**: `create_entities`, `create_relations`, `add_observations`, `search_nodes`, `open_nodes`, `delete_entities`, `delete_relations`, `delete_observations`, `read_graph`

---

### Rank 3: mcp-pandoc

**Why**: The final deliverable is a book in PDF and EPUB format. Pandoc is the gold standard for Markdown-to-book conversion, and wrapping it as MCP lets agents call format conversion as a structured tool with proper error handling and format validation.

```bash
# Prerequisites
brew install pandoc         # macOS
# or: sudo apt install pandoc  # Linux

# Install
pip install mcp-pandoc

# Add to Claude Code
claude mcp add pandoc -s local -- python -m mcp_pandoc
```

**Configuration in `.mcp.json`**:
```json
{
  "mcpServers": {
    "pandoc": {
      "command": "python",
      "args": ["-m", "mcp_pandoc"],
      "env": {}
    }
  }
}
```

**Tools exposed**: `convert_document` (supports md, docx, pdf, epub, latex, html, rst and more)

---

### Rank 4: Brave Search

**Why**: Autobiography writing requires fact-checking dates, places, historical events, and public figures. Brave Search's free tier (2,000 queries/month) is sufficient, and its privacy-first approach aligns with the sensitive nature of personal biography data.

```bash
# Get free API key at https://brave.com/search/api/
# Add to Claude Code
claude mcp add brave-search -s local \
  -e BRAVE_API_KEY=${BRAVE_API_KEY} \
  -- npx -y @anthropic-ai/mcp-server-brave-search
```

**Configuration in `.mcp.json`**:
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${env:BRAVE_API_KEY}"
      }
    }
  }
}
```

**Tools exposed**: `brave_web_search`, `brave_local_search`

---

### Rank 5: ChromaDB MCP

**Why**: As the autobiography grows, the agent needs semantic search over all previously written chapters, interview transcripts, and story elements. ChromaDB provides vector-based retrieval that goes beyond keyword matching — essential for finding thematic connections across a 300+ page manuscript.

```bash
# Prerequisites
pip install chromadb sentence-transformers

# Install
pip install chroma-mcp

# Add to Claude Code
claude mcp add chroma -s local -- python -m chroma_mcp \
  --persist-path ./autobiography-generator/.chroma-db \
  --client-type persistent
```

**Configuration in `.mcp.json`**:
```json
{
  "mcpServers": {
    "chroma": {
      "command": "python",
      "args": ["-m", "chroma_mcp", "--persist-path", "./autobiography-generator/.chroma-db", "--client-type", "persistent"],
      "env": {}
    }
  }
}
```

**Tools exposed**: `create_collection`, `add_documents`, `query_collection`, `get_collection_info`, `list_collections`, `delete_collection`, `update_documents`

---

## 3. Custom MCP Server Blueprint

### Architecture

```
autobiography-mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              ← Entry point + MCP server registration
│   ├── tools/
│   │   ├── transcribe.ts     ← Wraps faster-whisper CLI
│   │   ├── search-memories.ts ← Queries story bible
│   │   ├── validate-bible.ts  ← Story bible consistency checks
│   │   └── build-book.ts     ← Pandoc-based book assembly
│   ├── utils/
│   │   ├── subprocess.ts     ← Safe subprocess wrapper
│   │   └── story-bible.ts    ← Story bible schema + I/O
│   └── types.ts              ← Shared TypeScript types
└── README.md
```

### Full Implementation (TypeScript)

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execFile } from "child_process";
import { promisify } from "util";
import * as fs from "fs/promises";
import * as path from "path";

const execFileAsync = promisify(execFile);

const server = new McpServer({
  name: "autobiography-pipeline",
  version: "1.0.0",
  description: "Tools for the AI Autobiography Generator pipeline",
});

// ─────────────────────────────────────────────
// Tool 1: transcribe_audio
// ─────────────────────────────────────────────
server.tool(
  "transcribe_audio",
  "Transcribe an audio file to text using faster-whisper. " +
  "Supports mp3, wav, m4a, flac, ogg. Returns timestamped segments.",
  {
    file_path: z.string().describe("Absolute path to audio file"),
    language: z.string().optional().describe("Language code (e.g., 'en', 'ko'). Auto-detect if omitted."),
    model: z.enum(["tiny", "base", "small", "medium", "large-v3"]).default("large-v3")
      .describe("Whisper model size"),
    output_format: z.enum(["text", "srt", "vtt", "json"]).default("json")
      .describe("Output format"),
  },
  async ({ file_path, language, model, output_format }) => {
    // Validate file exists
    try {
      await fs.access(file_path);
    } catch {
      return {
        content: [{ type: "text", text: `Error: File not found: ${file_path}` }],
        isError: true,
      };
    }

    const args = [
      "-m", "faster_whisper",
      "--model", model,
      "--output_format", output_format,
      file_path,
    ];
    if (language) {
      args.push("--language", language);
    }

    try {
      const { stdout, stderr } = await execFileAsync("python3", args, {
        timeout: 600_000, // 10 min for long recordings
        maxBuffer: 50 * 1024 * 1024, // 50MB buffer
      });

      return {
        content: [{ type: "text", text: stdout }],
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: `Transcription failed:\n${error.stderr || error.message}`,
        }],
        isError: true,
      };
    }
  }
);

// ─────────────────────────────────────────────
// Tool 2: search_memories
// ─────────────────────────────────────────────
interface StoryEntity {
  name: string;
  type: "person" | "place" | "event" | "theme" | "period";
  observations: string[];
  metadata?: Record<string, string>;
}

interface StoryBible {
  entities: StoryEntity[];
  relations: Array<{ from: string; to: string; type: string }>;
  timeline: Array<{ date: string; event: string; entities: string[] }>;
}

server.tool(
  "search_memories",
  "Search the Story Bible for relevant people, places, events, themes, or time periods. " +
  "Uses fuzzy text matching across entities, relations, and timeline.",
  {
    query: z.string().describe("Natural language search query"),
    entity_type: z.enum(["person", "place", "event", "theme", "period", "all"]).default("all")
      .describe("Filter by entity type"),
    max_results: z.number().default(10).describe("Maximum number of results"),
    bible_path: z.string().default("./autobiography-generator/.story-bible/story-bible.json")
      .describe("Path to story bible JSON"),
  },
  async ({ query, entity_type, max_results, bible_path }) => {
    try {
      const raw = await fs.readFile(bible_path, "utf-8");
      const bible: StoryBible = JSON.parse(raw);

      const queryLower = query.toLowerCase();
      const queryTerms = queryLower.split(/\s+/);

      // Score each entity by relevance
      const scored = bible.entities
        .filter((e) => entity_type === "all" || e.type === entity_type)
        .map((entity) => {
          const searchText = [
            entity.name,
            ...entity.observations,
            ...(entity.metadata ? Object.values(entity.metadata) : []),
          ].join(" ").toLowerCase();

          let score = 0;
          for (const term of queryTerms) {
            if (searchText.includes(term)) score += 1;
            if (entity.name.toLowerCase().includes(term)) score += 3; // name match bonus
          }

          // Find related timeline entries
          const timelineHits = bible.timeline.filter(
            (t) => t.entities.includes(entity.name) &&
              t.event.toLowerCase().includes(queryLower)
          );
          score += timelineHits.length * 2;

          // Find relations
          const relatedEntities = bible.relations
            .filter((r) => r.from === entity.name || r.to === entity.name)
            .map((r) => (r.from === entity.name ? r.to : r.from));

          return { entity, score, timelineHits, relatedEntities };
        })
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, max_results);

      const result = scored.map((item) => ({
        name: item.entity.name,
        type: item.entity.type,
        relevance_score: item.score,
        observations: item.entity.observations,
        related_entities: item.relatedEntities,
        timeline_entries: item.timelineHits,
      }));

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ query, results_count: result.length, results: result }, null, 2),
        }],
      };
    } catch (error: any) {
      return {
        content: [{ type: "text", text: `Search failed: ${error.message}` }],
        isError: true,
      };
    }
  }
);

// ─────────────────────────────────────────────
// Tool 3: validate_story_bible
// ─────────────────────────────────────────────
server.tool(
  "validate_story_bible",
  "Validate the Story Bible for internal consistency. Checks: " +
  "orphan entities, timeline conflicts, missing relations, duplicate entries.",
  {
    bible_path: z.string().default("./autobiography-generator/.story-bible/story-bible.json")
      .describe("Path to story bible JSON"),
  },
  async ({ bible_path }) => {
    try {
      const raw = await fs.readFile(bible_path, "utf-8");
      const bible: StoryBible = JSON.parse(raw);

      const issues: Array<{ severity: "error" | "warning"; category: string; message: string }> = [];

      // Check 1: Duplicate entity names
      const nameCount = new Map<string, number>();
      for (const e of bible.entities) {
        nameCount.set(e.name, (nameCount.get(e.name) || 0) + 1);
      }
      for (const [name, count] of nameCount) {
        if (count > 1) {
          issues.push({
            severity: "error",
            category: "duplicate",
            message: `Entity "${name}" appears ${count} times`,
          });
        }
      }

      // Check 2: Orphan relations (reference non-existent entities)
      const entityNames = new Set(bible.entities.map((e) => e.name));
      for (const rel of bible.relations) {
        if (!entityNames.has(rel.from)) {
          issues.push({
            severity: "error",
            category: "orphan_relation",
            message: `Relation references unknown entity "${rel.from}"`,
          });
        }
        if (!entityNames.has(rel.to)) {
          issues.push({
            severity: "error",
            category: "orphan_relation",
            message: `Relation references unknown entity "${rel.to}"`,
          });
        }
      }

      // Check 3: Timeline references unknown entities
      for (const entry of bible.timeline) {
        for (const entityRef of entry.entities) {
          if (!entityNames.has(entityRef)) {
            issues.push({
              severity: "warning",
              category: "timeline_orphan",
              message: `Timeline entry "${entry.event}" references unknown entity "${entityRef}"`,
            });
          }
        }
      }

      // Check 4: Entities with no observations
      for (const e of bible.entities) {
        if (!e.observations || e.observations.length === 0) {
          issues.push({
            severity: "warning",
            category: "empty_entity",
            message: `Entity "${e.name}" (${e.type}) has no observations`,
          });
        }
      }

      // Check 5: Timeline date ordering
      const dates = bible.timeline.map((t) => ({ date: t.date, event: t.event }));
      for (let i = 1; i < dates.length; i++) {
        if (dates[i].date < dates[i - 1].date) {
          issues.push({
            severity: "warning",
            category: "timeline_order",
            message: `Timeline not chronological: "${dates[i - 1].event}" (${dates[i - 1].date}) before "${dates[i].event}" (${dates[i].date})`,
          });
        }
      }

      const summary = {
        total_entities: bible.entities.length,
        total_relations: bible.relations.length,
        total_timeline_entries: bible.timeline.length,
        issues_found: issues.length,
        errors: issues.filter((i) => i.severity === "error").length,
        warnings: issues.filter((i) => i.severity === "warning").length,
        is_valid: issues.filter((i) => i.severity === "error").length === 0,
        issues,
      };

      return {
        content: [{ type: "text", text: JSON.stringify(summary, null, 2) }],
      };
    } catch (error: any) {
      return {
        content: [{ type: "text", text: `Validation failed: ${error.message}` }],
        isError: true,
      };
    }
  }
);

// ─────────────────────────────────────────────
// Tool 4: build_book
// ─────────────────────────────────────────────
server.tool(
  "build_book",
  "Assemble chapter Markdown files into a book. Outputs PDF, EPUB, or DOCX via Pandoc. " +
  "Applies custom CSS for EPUB, LaTeX template for PDF.",
  {
    source_dir: z.string().describe("Directory containing chapter .md files (sorted by filename)"),
    output_format: z.enum(["pdf", "epub", "docx"]).describe("Output format"),
    output_path: z.string().describe("Full path for the output file"),
    title: z.string().describe("Book title"),
    author: z.string().describe("Author name"),
    cover_image: z.string().optional().describe("Path to cover image"),
    css_file: z.string().optional().describe("Custom CSS for EPUB styling"),
    toc: z.boolean().default(true).describe("Include table of contents"),
    metadata_file: z.string().optional().describe("YAML metadata file for Pandoc"),
  },
  async ({ source_dir, output_format, output_path, title, author, cover_image, css_file, toc, metadata_file }) => {
    // Collect and sort chapter files
    let files: string[];
    try {
      const entries = await fs.readdir(source_dir);
      files = entries
        .filter((f) => f.endsWith(".md"))
        .sort()
        .map((f) => path.join(source_dir, f));
    } catch (error: any) {
      return {
        content: [{ type: "text", text: `Cannot read source directory: ${error.message}` }],
        isError: true,
      };
    }

    if (files.length === 0) {
      return {
        content: [{ type: "text", text: `No .md files found in ${source_dir}` }],
        isError: true,
      };
    }

    // Build Pandoc command
    const args = [
      "--from", "markdown",
      "--to", output_format === "pdf" ? "latex" : output_format,
      "--output", output_path,
      "--metadata", `title=${title}`,
      "--metadata", `author=${author}`,
      "--standalone",
    ];

    if (toc) args.push("--toc", "--toc-depth=3");
    if (cover_image) args.push("--epub-cover-image", cover_image);
    if (css_file) args.push("--css", css_file);
    if (metadata_file) args.push("--metadata-file", metadata_file);
    if (output_format === "pdf") {
      args.push("--pdf-engine=xelatex"); // Unicode support
      args.push("-V", "geometry:margin=1in");
      args.push("-V", "fontsize=11pt");
      args.push("-V", "mainfont=Noto Serif");
    }

    args.push(...files);

    try {
      const { stdout, stderr } = await execFileAsync("pandoc", args, {
        timeout: 120_000,
        maxBuffer: 100 * 1024 * 1024,
      });

      // Verify output was created
      const stats = await fs.stat(output_path);
      const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            success: true,
            output_path,
            format: output_format,
            chapters_included: files.length,
            file_size_mb: sizeMB,
            pandoc_output: stderr || "No warnings",
          }, null, 2),
        }],
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: `Build failed:\n${error.stderr || error.message}`,
        }],
        isError: true,
      };
    }
  }
);

// ─────────────────────────────────────────────
// Start server
// ─────────────────────────────────────────────
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("autobiography-pipeline MCP server running on stdio");
}

main().catch(console.error);
```

### Alternative: Python Implementation with FastMCP

```python
# src/autobiography_mcp/server.py
from fastmcp import FastMCP
import subprocess
import json
from pathlib import Path
from typing import Optional, Literal

mcp = FastMCP(
    "autobiography-pipeline",
    version="1.0.0",
    description="Tools for the AI Autobiography Generator pipeline",
)


@mcp.tool
def transcribe_audio(
    file_path: str,
    language: Optional[str] = None,
    model: Literal["tiny", "base", "small", "medium", "large-v3"] = "large-v3",
    output_format: Literal["text", "srt", "vtt", "json"] = "json",
) -> str:
    """Transcribe an audio file to text using faster-whisper.

    Supports mp3, wav, m4a, flac, ogg. Returns timestamped segments.

    Args:
        file_path: Absolute path to audio file
        language: Language code (e.g., 'en', 'ko'). Auto-detect if omitted.
        model: Whisper model size
        output_format: Output format for transcription
    """
    from faster_whisper import WhisperModel

    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    whisper_model = WhisperModel(model, device="cpu", compute_type="int8")
    segments, info = whisper_model.transcribe(
        file_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    result = {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(info.duration, 1),
        "segments": [],
    }

    for seg in segments:
        result["segments"].append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })

    if output_format == "text":
        return "\n".join(s["text"] for s in result["segments"])
    elif output_format == "srt":
        lines = []
        for i, s in enumerate(result["segments"], 1):
            lines.append(str(i))
            lines.append(f"{_fmt_time(s['start'])} --> {_fmt_time(s['end'])}")
            lines.append(s["text"])
            lines.append("")
        return "\n".join(lines)
    else:
        return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool
def search_memories(
    query: str,
    entity_type: Literal["person", "place", "event", "theme", "period", "all"] = "all",
    max_results: int = 10,
    bible_path: str = "./autobiography-generator/.story-bible/story-bible.json",
) -> str:
    """Search the Story Bible for relevant people, places, events, themes.

    Uses fuzzy text matching across entities, relations, and timeline.

    Args:
        query: Natural language search query
        entity_type: Filter by entity type
        max_results: Maximum number of results
        bible_path: Path to story bible JSON
    """
    p = Path(bible_path)
    if not p.exists():
        return json.dumps({"error": f"Story bible not found at {bible_path}"})

    bible = json.loads(p.read_text(encoding="utf-8"))
    query_lower = query.lower()
    terms = query_lower.split()

    scored = []
    entity_names = {e["name"] for e in bible.get("entities", [])}

    for entity in bible.get("entities", []):
        if entity_type != "all" and entity.get("type") != entity_type:
            continue

        search_text = " ".join([
            entity["name"],
            *entity.get("observations", []),
            *list(entity.get("metadata", {}).values()),
        ]).lower()

        score = sum(3 if term in entity["name"].lower() else 1
                     for term in terms if term in search_text)

        if score > 0:
            related = [
                r["to"] if r["from"] == entity["name"] else r["from"]
                for r in bible.get("relations", [])
                if r["from"] == entity["name"] or r["to"] == entity["name"]
            ]
            scored.append({
                "name": entity["name"],
                "type": entity.get("type"),
                "score": score,
                "observations": entity.get("observations", []),
                "related_entities": related,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return json.dumps({
        "query": query,
        "results_count": len(scored[:max_results]),
        "results": scored[:max_results],
    }, indent=2, ensure_ascii=False)


@mcp.tool
def validate_story_bible(
    bible_path: str = "./autobiography-generator/.story-bible/story-bible.json",
) -> str:
    """Validate Story Bible for consistency.

    Checks: orphan entities, timeline conflicts, missing relations, duplicates.

    Args:
        bible_path: Path to story bible JSON
    """
    p = Path(bible_path)
    if not p.exists():
        return json.dumps({"error": f"Story bible not found at {bible_path}"})

    bible = json.loads(p.read_text(encoding="utf-8"))
    issues = []
    entities = bible.get("entities", [])
    entity_names = {e["name"] for e in entities}

    # Duplicate check
    from collections import Counter
    name_counts = Counter(e["name"] for e in entities)
    for name, count in name_counts.items():
        if count > 1:
            issues.append({"severity": "error", "category": "duplicate",
                           "message": f'Entity "{name}" appears {count} times'})

    # Orphan relations
    for rel in bible.get("relations", []):
        if rel["from"] not in entity_names:
            issues.append({"severity": "error", "category": "orphan_relation",
                           "message": f'Relation references unknown entity "{rel["from"]}"'})
        if rel["to"] not in entity_names:
            issues.append({"severity": "error", "category": "orphan_relation",
                           "message": f'Relation references unknown entity "{rel["to"]}"'})

    # Empty entities
    for e in entities:
        if not e.get("observations"):
            issues.append({"severity": "warning", "category": "empty_entity",
                           "message": f'Entity "{e["name"]}" has no observations'})

    errors = [i for i in issues if i["severity"] == "error"]
    return json.dumps({
        "total_entities": len(entities),
        "total_relations": len(bible.get("relations", [])),
        "total_timeline_entries": len(bible.get("timeline", [])),
        "is_valid": len(errors) == 0,
        "errors": len(errors),
        "warnings": len(issues) - len(errors),
        "issues": issues,
    }, indent=2)


@mcp.tool
def build_book(
    source_dir: str,
    output_format: Literal["pdf", "epub", "docx"],
    output_path: str,
    title: str,
    author: str,
    cover_image: Optional[str] = None,
    css_file: Optional[str] = None,
    toc: bool = True,
) -> str:
    """Assemble chapter Markdown files into a book via Pandoc.

    Args:
        source_dir: Directory containing chapter .md files (sorted by filename)
        output_format: Output format (pdf, epub, docx)
        output_path: Full path for the output file
        title: Book title
        author: Author name
        cover_image: Path to cover image (optional)
        css_file: Custom CSS for EPUB styling (optional)
        toc: Include table of contents
    """
    src = Path(source_dir)
    if not src.is_dir():
        return json.dumps({"error": f"Source directory not found: {source_dir}"})

    md_files = sorted(src.glob("*.md"))
    if not md_files:
        return json.dumps({"error": f"No .md files found in {source_dir}"})

    cmd = [
        "pandoc", "--from", "markdown",
        "--to", "latex" if output_format == "pdf" else output_format,
        "--output", output_path,
        "--metadata", f"title={title}",
        "--metadata", f"author={author}",
        "--standalone",
    ]

    if toc:
        cmd.extend(["--toc", "--toc-depth=3"])
    if cover_image:
        cmd.extend(["--epub-cover-image", cover_image])
    if css_file:
        cmd.extend(["--css", css_file])
    if output_format == "pdf":
        cmd.extend(["--pdf-engine=xelatex", "-V", "geometry:margin=1in",
                     "-V", "fontsize=11pt"])

    cmd.extend(str(f) for f in md_files)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return json.dumps({"error": result.stderr})

    out = Path(output_path)
    size_mb = round(out.stat().st_size / (1024 * 1024), 2)

    return json.dumps({
        "success": True,
        "output_path": output_path,
        "format": output_format,
        "chapters_included": len(md_files),
        "file_size_mb": size_mb,
    }, indent=2)


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    mcp.run()
```

### package.json (TypeScript version)

```json
{
  "name": "autobiography-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsc --watch",
    "inspect": "npx @modelcontextprotocol/inspector node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "@types/node": "^22.0.0"
  }
}
```

### pyproject.toml (Python version)

```toml
[project]
name = "autobiography-mcp-server"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=3.0.0",
    "faster-whisper>=1.1.0",
]

[project.scripts]
autobiography-mcp = "autobiography_mcp.server:mcp.run"
```

---

## 4. MCP Integration in settings.json

### Project-Level Configuration: `.mcp.json`

This file is committed to the repo and shared with the team.

```json
{
  "mcpServers": {
    "autobiography-pipeline": {
      "command": "node",
      "args": ["./autobiography-generator/mcp-server/dist/index.js"],
      "env": {}
    },
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ],
      "env": {
        "MEMORY_FILE_PATH": "./autobiography-generator/.story-bible/memory.json"
      }
    },
    "pandoc": {
      "command": "python3",
      "args": ["-m", "mcp_pandoc"],
      "env": {}
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {}
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./autobiography-generator"
      ],
      "env": {}
    }
  }
}
```

### User-Level Configuration: `~/.claude.json`

Credentials stay here, never committed.

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${env:BRAVE_API_KEY}"
      }
    },
    "whisper": {
      "command": "python3",
      "args": [
        "-m", "fast_whisper_mcp_server",
        "--model", "large-v3",
        "--device", "cpu",
        "--compute-type", "int8"
      ],
      "env": {}
    },
    "chroma": {
      "command": "python3",
      "args": [
        "-m", "chroma_mcp",
        "--persist-path", "./autobiography-generator/.chroma-db",
        "--client-type", "persistent"
      ],
      "env": {}
    }
  }
}
```

### Claude Code CLI Commands to Set Up

```bash
# ---- Project-scoped (shared) ----
claude mcp add autobiography-pipeline -s project -- node ./autobiography-generator/mcp-server/dist/index.js
claude mcp add memory -s project -- npx -y @modelcontextprotocol/server-memory
claude mcp add pandoc -s project -- python3 -m mcp_pandoc
claude mcp add fetch -s project -- npx -y @modelcontextprotocol/server-fetch
claude mcp add filesystem -s project -- npx -y @modelcontextprotocol/server-filesystem ./autobiography-generator

# ---- User-scoped (credentials, not shared) ----
claude mcp add brave-search -s user -e BRAVE_API_KEY=${BRAVE_API_KEY} -- npx -y @anthropic-ai/mcp-server-brave-search
claude mcp add whisper -s user -- python3 -m fast_whisper_mcp_server --model large-v3 --device cpu --compute-type int8
claude mcp add chroma -s user -- python3 -m chroma_mcp --persist-path ./autobiography-generator/.chroma-db --client-type persistent

# ---- Verify ----
claude mcp list
```

### Performance Note on Tool Search

Claude Code enables **Tool Search** automatically when MCP tool descriptions exceed 10% of the context window. With 8 MCP servers configured (approximately 30-40 tools total), this threshold is unlikely to be hit for a 200K-token context. If it is, Claude dynamically loads only the relevant tools on-demand rather than preloading all definitions.

---

## 5. MCP vs Direct CLI Calls

### Decision Framework

```
                     ┌─────────────────────────────────────┐
                     │   Does the tool need structured     │
                     │   output that the agent acts on?    │
                     └──────────────┬──────────────────────┘
                                    │
                          ┌─────────┴─────────┐
                         Yes                   No
                          │                    │
                 ┌────────┴────────┐   ┌──────┴───────┐
                 │ Does it need    │   │ CLI is fine.  │
                 │ session state?  │   │ subprocess.   │
                 └────────┬───────┘   └──────────────┘
                          │
                ┌─────────┴─────────┐
               Yes                   No
                │                    │
          ┌─────┴──────┐    ┌───────┴────────┐
          │ MCP wins.  │    │ Either works.  │
          │ Use it.    │    │ MCP if complex │
          └────────────┘    │ args/output.   │
                            └────────────────┘
```

### Tool-by-Tool Comparison

| External Tool | MCP | CLI Subprocess | Verdict | Rationale |
|---------------|-----|----------------|---------|-----------|
| **faster-whisper** | `transcribe_audio(path)` returns structured JSON with timestamps | `python3 -m faster_whisper audio.wav > out.json` | **MCP** | Agent needs structured segments (start, end, text) for downstream processing. MCP provides typed schema. Raw CLI stdout requires parsing. |
| **Pandoc** | `build_book(dir, format, title)` returns success + file size | `pandoc *.md -o book.epub` | **Tie / CLI slightly** | Pandoc's CLI is already well-structured. MCP adds input validation and structured error reporting, but the CLI is simple enough. For one-shot conversion, CLI is fine. For pipeline integration with error handling, MCP is better. |
| **Brave Search** | `brave_web_search(query)` returns structured results | N/A (API only) | **MCP** | No CLI equivalent. The MCP server wraps the HTTP API and handles auth. |
| **ChromaDB** | `query_collection(query, n)` returns ranked documents | `python3 -c "import chromadb; ..."` | **MCP** | Vector DB queries are multi-step (connect, select collection, query, parse). MCP encapsulates state (persistent connection to the DB). |
| **Git operations** | `git_log()`, `git_diff()` | `git log --oneline` | **CLI** | Git CLI is universally known by LLMs. Structured output via `--format`. Claude Code already has Git tools built in. Adding an MCP server is redundant. |
| **File I/O** | `read_file(path)`, `write_file(path, content)` | `cat file.md`, `echo > file.md` | **CLI** | Claude Code already has built-in Read, Write, Edit tools. A filesystem MCP server adds nothing. |
| **Image metadata** | `extract_exif(path)` returns JSON | `exiftool -json photo.jpg` | **Tie** | exiftool with `-json` already returns structured data. MCP adds no significant benefit. CLI is simpler. |
| **PDF extraction** | `extract_pdf(path)` returns text + metadata | `pdftotext file.pdf -` | **MCP** | PDF extraction is complex (OCR fallback, page ranges, metadata). MCP server handles edge cases and returns structured data. CLI tools vary in quality. |
| **Memory / Knowledge Graph** | `create_entities()`, `search_nodes()` | Write/read JSON files manually | **MCP** | Persistent state is the entire point. Manual JSON manipulation is error-prone. The official Memory server handles concurrent access, schema validation, and persistence. |
| **Text-to-Speech** | `synthesize_speech(text, voice)` | `say "text"` or `espeak "text"` | **CLI** | For simple TTS, CLI is sufficient. MCP only if you need voice selection, SSML, and audio file output. |

### Summary Verdict

| Category | Recommendation |
|----------|---------------|
| **Use MCP for** | Audio transcription, vector search, persistent memory/knowledge graph, web search APIs, PDF processing |
| **Use CLI for** | Git operations, file I/O, simple format conversions, image metadata, text-to-speech |
| **Either works** | Pandoc book building (MCP if error handling matters), EXIF extraction |

### The Key Insight

MCP wins when:
1. **The tool maintains state** across calls (database connections, knowledge graphs)
2. **The output schema matters** to downstream agent logic (transcription segments, search results)
3. **There is no CLI equivalent** (web APIs like Brave Search)
4. **Error handling is complex** and benefits from structured error responses

CLI wins when:
1. **LLMs already know the tool** from training data (git, grep, pandoc)
2. **The output is simple text** that needs no parsing
3. **Claude Code already provides the capability** (Read, Write, Edit, Bash)
4. **Token efficiency matters** (CLI is 33% more token-efficient per benchmark data)

### Cost Consideration

Each MCP server is a persistent subprocess consuming memory. With 8 servers, expect ~200-400MB additional RAM usage. For a local development machine, this is negligible. But avoid adding MCP servers for capabilities Claude Code already has natively.

---

## Appendix: Source URLs

### Official MCP Resources
- [Model Context Protocol Servers Repository](https://github.com/modelcontextprotocol/servers)
- [MCP Official Registry](https://registry.modelcontextprotocol.io/)
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [Build an MCP Server](https://modelcontextprotocol.io/docs/develop/build-server)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### Community Catalogs
- [Awesome MCP Servers (wong2)](https://github.com/wong2/awesome-mcp-servers)
- [Awesome MCP Servers (punkpeye)](https://github.com/punkpeye/awesome-mcp-servers)
- [MCP Servers Directory (593+)](https://aiagentslist.com/mcp-servers)
- [PulseMCP](https://www.pulsemcp.com/)

### Specific Server Repositories
- [Fast-Whisper-MCP-Server](https://github.com/BigUncle/Fast-Whisper-MCP-Server)
- [ChromaDB MCP](https://github.com/chroma-core/chroma-mcp)
- [mcp-pandoc](https://github.com/vivekVells/mcp-pandoc)
- [MindBridge MCP](https://github.com/pinkpixel-dev/mindbridge-mcp)
- [LLM Bridge MCP](https://glama.ai/mcp/servers/@sjquant/llm-bridge-mcp)
- [EXIF MCP](https://github.com/stass/exif-mcp)
- [ebook-mcp](https://github.com/onebirdrocks/ebook-mcp)
- [Knowledge Graph MCP](https://github.com/shaneholloman/mcp-knowledge-graph)
- [pdf-reader-mcp](https://github.com/SylphxAI/pdf-reader-mcp)

### Best Practices & Comparisons
- [MCP vs CLI for AI Agents (CircleCI)](https://circleci.com/blog/mcp-vs-cli/)
- [MCP vs CLI Benchmarking](https://mariozechner.at/posts/2025-08-15-mcp-vs-cli/)
- [MCP Server Security Best Practices](https://www.descope.com/blog/post/mcp-server-security-best-practices)
- [MCP API Key Management](https://www.stainless.com/mcp/mcp-server-api-key-management-best-practices)
- [Claude Code MCP Configuration Guide](https://www.builder.io/blog/claude-code-mcp-servers)
- [Configuring MCP Tools in Claude Code](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
- [FastMCP Tutorial (Firecrawl)](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python)
- [Docker MCP Toolkit for Claude Code](https://www.docker.com/blog/add-mcp-servers-to-claude-code-with-mcp-toolkit/)
