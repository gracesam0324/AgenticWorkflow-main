/**
 * Data loading utilities — reads Python pipeline data files from disk.
 *
 * All paths are relative to the autobiography-generator project root
 * (one directory up from webapp/).
 */

import fs from "fs";
import path from "path";
import { type ReactNode } from "react";

const PROJECT_ROOT = path.resolve(process.cwd(), "..");

function readJson<T = Record<string, unknown>>(
  relativePath: string
): T | null {
  const fullPath = path.join(PROJECT_ROOT, relativePath);
  try {
    const raw = fs.readFileSync(fullPath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function readYaml(relativePath: string): Record<string, unknown> | null {
  const fullPath = path.join(PROJECT_ROOT, relativePath);
  try {
    const raw = fs.readFileSync(fullPath, "utf-8");
    // Simple YAML parser for flat/nested structures
    return parseSimpleYaml(raw);
  } catch {
    return null;
  }
}

function parseSimpleYaml(text: string): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  let currentKey = "";
  let currentObj: Record<string, unknown> = result;
  const stack: { key: string; obj: Record<string, unknown>; indent: number }[] =
    [];

  for (const line of text.split("\n")) {
    if (line.trim() === "" || line.trim().startsWith("#")) continue;

    const indent = line.search(/\S/);
    const trimmed = line.trim();

    // Handle list items
    if (trimmed.startsWith("- ")) {
      const listValue = trimmed.slice(2).trim();
      if (currentKey && Array.isArray(currentObj[currentKey])) {
        (currentObj[currentKey] as unknown[]).push(parseYamlValue(listValue));
      }
      continue;
    }

    const colonIdx = trimmed.indexOf(":");
    if (colonIdx === -1) continue;

    const key = trimmed.slice(0, colonIdx).trim();
    const rawValue = trimmed.slice(colonIdx + 1).trim();

    // Pop stack for dedented lines
    while (stack.length > 0 && indent <= stack[stack.length - 1].indent) {
      stack.pop();
      currentObj =
        stack.length > 0 ? stack[stack.length - 1].obj : result;
    }

    if (rawValue === "" || rawValue === "|") {
      // Nested object or block scalar
      const newObj: Record<string, unknown> = {};
      currentObj[key] = newObj;
      stack.push({ key, obj: currentObj, indent });
      currentObj = newObj;
      currentKey = key;
    } else if (rawValue === "[]") {
      currentObj[key] = [];
      currentKey = key;
    } else {
      currentObj[key] = parseYamlValue(rawValue);
      currentKey = key;
    }
  }

  return result;
}

function parseYamlValue(
  v: string
): string | number | boolean | null {
  if (v === "null" || v === "~" || v === "") return null;
  if (v === "true") return true;
  if (v === "false") return false;
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v);
  // Strip quotes
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))
    return v.slice(1, -1);
  return v;
}

function readText(relativePath: string): string | null {
  const fullPath = path.join(PROJECT_ROOT, relativePath);
  try {
    return fs.readFileSync(fullPath, "utf-8");
  } catch {
    return null;
  }
}

function listFiles(relativePath: string, ext?: string): string[] {
  const fullPath = path.join(PROJECT_ROOT, relativePath);
  try {
    const files = fs.readdirSync(fullPath);
    return ext ? files.filter((f) => f.endsWith(ext)) : files;
  } catch {
    return [];
  }
}

// ──────────────────────────────────────────────
// Public API
// ──────────────────────────────────────────────

export interface PipelineState {
  meta: {
    subject_name: string;
    project_start_date: string;
    target_word_count: number;
    target_chapters: number;
    current_phase: string;
  };
  interviews: {
    total_collected: number;
    sessions: Array<{
      session_id: string;
      file: string;
      status: string;
      themes: string[];
    }>;
  };
  structure: {
    outline_version: number;
    chapters: Array<{
      number: number;
      title: string;
      life_period: string;
      source_sessions: string[];
      status: string;
    }>;
  };
  drafts: {
    current_round: number;
    chapters_drafted: number;
    chapters_revised: number;
  };
  quality: {
    voice_consistency_score: number | null;
    factual_accuracy_score: number | null;
    readability_avg: number | null;
    last_eval_date: string | null;
  };
  pipeline: {
    last_agent_run: string | null;
    last_agent_name: string | null;
    errors: string[];
  };
}

export function loadPipelineState(): PipelineState | null {
  return readYaml("state.yaml") as PipelineState | null;
}

export interface InterviewTranscript {
  meta: {
    session_id: string;
    subject_name: string;
    interviewer: string;
    date: string;
    duration_minutes: number;
    life_period: {
      label: string;
      start_year: number;
      end_year: number;
    };
    themes: string[];
    emotional_tone: string;
  };
  segments: Array<{
    segment_id: string;
    topic: string;
    content: string;
    key_quotes: Array<{
      text: string;
      context: string;
      usable_in_chapter: boolean;
    }>;
    people_mentioned: Array<{ name: string; relationship: string }>;
    places_mentioned: Array<{
      name: string;
      city: string;
      country: string;
    }>;
    events: Array<{
      description: string;
      date_approximate: string;
      significance: string;
    }>;
    emotional_markers: Array<{
      emotion: string;
      trigger: string;
      intensity: number;
    }>;
  }>;
}

export function loadInterviews(): InterviewTranscript[] {
  const files = listFiles("test-data/micro-interviews", ".json");
  return files
    .map((f) =>
      readJson<InterviewTranscript>(
        path.join("test-data/micro-interviews", f)
      )
    )
    .filter((t): t is InterviewTranscript => t !== null);
}

export function loadInterviewById(
  sessionId: string
): InterviewTranscript | null {
  const files = listFiles("test-data/micro-interviews", ".json");
  for (const f of files) {
    const transcript = readJson<InterviewTranscript>(
      path.join("test-data/micro-interviews", f)
    );
    if (transcript?.meta?.session_id === sessionId) return transcript;
  }
  return null;
}

export interface StoryBible {
  subject: Record<string, unknown>;
  characters: Array<Record<string, unknown>>;
  locations: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  timeline: Array<Record<string, unknown>>;
  places: Array<Record<string, unknown>>;
  themes: Array<Record<string, unknown>>;
  chapter_plan: Array<Record<string, unknown>>;
  voice_guide: Record<string, unknown>;
  [key: string]: unknown;
}

export function loadStoryBible(): StoryBible | null {
  return readJson<StoryBible>("outputs/story-bible/story_bible.json");
}

export interface GoldenChapter {
  filename: string;
  content: string;
}

export function loadChapters(): GoldenChapter[] {
  const goldenFiles = listFiles("test-data/golden-outputs", ".md");
  const chapterFiles = listFiles("outputs/chapters", ".md");
  const allFiles = [
    ...goldenFiles.map((f) => ({
      filename: f,
      dir: "test-data/golden-outputs",
    })),
    ...chapterFiles.map((f) => ({ filename: f, dir: "outputs/chapters" })),
  ];

  return allFiles
    .map(({ filename, dir }) => {
      const content = readText(path.join(dir, filename));
      return content ? { filename, content } : null;
    })
    .filter((c): c is GoldenChapter => c !== null);
}

export interface QualityMetrics {
  dimensions: Record<
    string,
    {
      latest: number;
      mean: number;
      trend: string;
      trend_delta: number;
      count: number;
    }
  >;
  total_evaluations: number;
}

export function loadQualityData(): QualityMetrics | null {
  // Try to load evaluation logs
  const evalFiles = listFiles("scripts/.eval-logs", ".json");
  if (evalFiles.length === 0) return null;

  const entries = evalFiles
    .sort()
    .map((f) => readJson(path.join("scripts/.eval-logs", f)))
    .filter((e): e is Record<string, unknown> => e !== null);

  if (entries.length === 0) return null;

  const dimensions = [
    "emotional_authenticity",
    "sensory_detail_preservation",
    "narrative_flow",
    "voice_consistency",
    "factual_grounding",
  ];

  const dimData: QualityMetrics["dimensions"] = {};
  for (const dim of dimensions) {
    const scores: number[] = [];
    for (const entry of entries) {
      const results = (entry.results ?? {}) as Record<string, Record<string, unknown>>;
      for (const result of Object.values(results)) {
        const llmScores = (result.llm_scores ?? {}) as Record<string, number>;
        if (dim in llmScores) scores.push(llmScores[dim]);
      }
    }
    if (scores.length > 0) {
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
      dimData[dim] = {
        latest: scores[scores.length - 1],
        mean: Math.round(mean * 1000) / 1000,
        trend: "stable",
        trend_delta: 0,
        count: scores.length,
      };
    }
  }

  return { dimensions: dimData, total_evaluations: entries.length };
}

export function loadSchemas(): Array<{ name: string; content: string }> {
  const files = listFiles("schemas", ".json");
  return files
    .map((f) => {
      const content = readText(path.join("schemas", f));
      return content ? { name: f, content } : null;
    })
    .filter((s): s is { name: string; content: string } => s !== null);
}
