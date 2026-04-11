#!/usr/bin/env bash
# ============================================================================
# setup.sh — AI Autobiography Generator: Full Project Scaffold
# Usage: cd autobiography-generator && bash scripts/setup.sh
# Creates everything needed to start developing in <30 seconds.
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== AI Autobiography Generator — Project Scaffold ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# ── 1. Directory Structure ──────────────────────────────────────────────────
echo "[1/8] Creating directory structure..."
dirs=(
  "agents/prompts"
  "agents/prompts/versions"
  "test-data"
  "test-data/micro-interviews"
  "test-data/golden-outputs"
  "outputs/drafts"
  "outputs/chapters"
  "outputs/comparisons"
  "outputs/eval-reports"
  "schemas"
  "scripts"
  "templates"
  "review-logs"
  "autopilot-logs"
  "eval"
  "eval/promptfoo"
  ".prompt-versions"
)

for d in "${dirs[@]}"; do
  mkdir -p "$d"
done
echo "  -> Created ${#dirs[@]} directories"

# ── 2. State File (SOT) ────────────────────────────────────────────────────
echo "[2/8] Creating state.yaml..."
cat > state.yaml << 'STATEEOF'
# ============================================================================
# state.yaml — Single Source of Truth for autobiography generation pipeline
# Only the Orchestrator writes to this file.
# ============================================================================
meta:
  subject_name: ""
  project_start_date: ""
  target_word_count: 50000
  target_chapters: 12
  current_phase: "interview-collection"  # interview-collection | structuring | drafting | revision | final

interviews:
  total_collected: 0
  sessions: []
  # Each entry: { session_id: "INT-001", file: "test-data/...", status: "raw|processed", themes: [] }

structure:
  outline_version: 0
  chapters: []
  # Each entry: { number: 1, title: "", life_period: "", source_sessions: [], status: "planned|drafted|revised|final" }

drafts:
  current_round: 0
  chapters_drafted: 0
  chapters_revised: 0

quality:
  voice_consistency_score: null    # 0.0-1.0 from eval
  factual_accuracy_score: null     # 0.0-1.0 from check.py
  readability_avg: null            # Flesch-Kincaid grade level
  last_eval_date: null

pipeline:
  last_agent_run: null
  last_agent_name: null
  errors: []
STATEEOF

# ── 3. Agent Prompt Files ──────────────────────────────────────────────────
echo "[3/8] Creating agent prompt files..."

cat > agents/prompts/interviewer.md << 'EOF'
---
name: interviewer
version: 1.0.0
temperature: 0.7
max_tokens: 4000
---

# Role
You are a skilled biographical interviewer. Your job is to extract rich, detailed life stories from the subject through thoughtful, empathetic questioning.

# Instructions
Given the subject's basic profile and the target life period, generate a structured interview transcript.

## Input Variables
- `{{subject_profile}}`: Name, age, background summary
- `{{life_period}}`: The period to explore (e.g., "Childhood 1985-1997")
- `{{previous_sessions_summary}}`: Brief summary of what's already been covered
- `{{themes_to_explore}}`: Specific themes to dig into

## Output Format
Return a JSON object matching the interview_transcript.schema.json schema.

## Rules
1. Ask open-ended questions that invite storytelling, not yes/no answers
2. Follow emotional cues — when the subject mentions something meaningful, dig deeper
3. Always capture specific names, places, dates, and sensory details
4. Generate 3-5 segments per session, each covering a distinct subtopic
5. Mark key quotes that are vivid enough to use verbatim in the autobiography
6. Note emotional markers with intensity ratings
7. Cross-reference people and places mentioned in previous sessions
EOF

cat > agents/prompts/chapter-writer.md << 'EOF'
---
name: chapter-writer
version: 1.0.0
temperature: 0.8
max_tokens: 8000
---

# Role
You are a literary ghostwriter creating a first-person autobiography. You write in the subject's authentic voice, transforming interview transcripts into compelling narrative prose.

# Instructions
Given interview transcripts and a chapter outline, write one chapter of the autobiography.

## Input Variables
- `{{chapter_number}}`: Chapter number (1-12)
- `{{chapter_title}}`: Title of this chapter
- `{{chapter_outline}}`: 3-5 bullet points describing what this chapter covers
- `{{source_transcripts}}`: The interview transcript segments relevant to this chapter
- `{{voice_profile}}`: Description of the subject's speaking style and personality
- `{{previous_chapter_ending}}`: Last 2 paragraphs of the previous chapter (for continuity)

## Output Format
Return the chapter as narrative prose in markdown format.

## Rules
1. Write in FIRST PERSON — this is the subject telling their own story
2. Weave in direct quotes from the transcripts naturally (use them, don't invent new ones)
3. Maintain chronological order within the chapter unless a flashback serves the narrative
4. Target 3500-5000 words per chapter
5. Begin each chapter with a vivid scene, not exposition
6. End each chapter with a hook or reflection that bridges to the next period
7. Preserve the subject's vocabulary and speech patterns from the transcripts
8. Every factual claim must trace back to a specific transcript segment
9. Use sensory details from the transcripts — do not invent sensory details
10. Name consistency: use exactly the names as they appear in transcripts
EOF

cat > agents/prompts/chapter-reviewer.md << 'EOF'
---
name: chapter-reviewer
version: 1.0.0
temperature: 0.3
max_tokens: 3000
---

# Role
You are a critical editor reviewing autobiography chapters for quality, accuracy, and voice consistency.

# Instructions
Given a chapter draft and its source transcripts, produce a structured review.

## Input Variables
- `{{chapter_draft}}`: The chapter text to review
- `{{source_transcripts}}`: Original interview transcripts this chapter is based on
- `{{voice_profile}}`: The established voice profile
- `{{previous_chapters_summary}}`: Summary of chapters written so far

## Output Format
Return a JSON review object:
```json
{
  "chapter": 1,
  "overall_score": 7.5,
  "voice_consistency": { "score": 8, "issues": [] },
  "factual_accuracy": { "score": 9, "ungrounded_claims": [] },
  "narrative_quality": { "score": 7, "issues": [] },
  "continuity": { "score": 8, "issues": [] },
  "line_edits": [
    { "line": "original text...", "suggestion": "improved text...", "reason": "..." }
  ],
  "must_fix": [],
  "nice_to_have": []
}
```

## Rules
1. Every factual claim in the chapter MUST have a source in the transcripts
2. Flag any invented quotes, details, or events not in the source material
3. Check name spelling consistency across all chapters
4. Verify chronological accuracy against transcript dates
5. Score voice consistency by comparing vocabulary and sentence patterns to the voice profile
EOF

cat > agents/prompts/voice-profiler.md << 'EOF'
---
name: voice-profiler
version: 1.0.0
temperature: 0.4
max_tokens: 2000
---

# Role
You analyze interview transcripts to build a voice profile that ghostwriters can use to write in the subject's authentic voice.

# Instructions
Given 2-3 interview transcripts, extract the subject's distinctive voice characteristics.

## Input Variables
- `{{transcripts}}`: 2-3 interview transcript texts
- `{{subject_name}}`: The subject's name

## Output Format
Return a YAML voice profile:
```yaml
subject: "Name"
vocabulary:
  favorite_words: []        # Words they use frequently
  avoided_words: []          # Words they never use
  filler_phrases: []         # "you know", "the thing is", etc.
  technical_jargon: []       # Domain-specific terms they use naturally
sentence_patterns:
  avg_length: short|medium|long
  style: simple|compound|complex
  rhetorical_devices: []     # e.g., "rhetorical questions", "lists of three"
storytelling:
  structure: chronological|thematic|associative
  detail_level: sparse|moderate|rich
  humor_frequency: rare|occasional|frequent
  emotional_expression: reserved|moderate|expressive
personality_markers:
  optimism: low|medium|high
  formality: casual|mixed|formal
  self_reference: rare|normal|frequent  # How often they say "I think", "I feel"
sample_phrases: []           # 5-10 phrases that capture their voice
```
EOF

# ── 4. Test Data ────────────────────────────────────────────────────────────
echo "[4/8] Creating test data..."

cat > test-data/micro-interviews/INT-001-childhood.json << 'TESTEOF'
{
  "meta": {
    "session_id": "INT-001",
    "subject_name": "Park Jimin",
    "interviewer": "ai-guided",
    "date": "2026-03-10",
    "duration_minutes": 45,
    "life_period": {
      "label": "Childhood in Busan",
      "start_year": 1990,
      "end_year": 2002
    },
    "themes": ["family", "education", "early-interests"],
    "emotional_tone": "reflective"
  },
  "segments": [
    {
      "segment_id": "SEG-001",
      "topic": "Family home and neighborhood",
      "content": "We lived in a small apartment in Haeundae, you know, before it became all fancy with the high-rises. My father was a fisherman — well, he ran a small fishing supply shop, but he always said he was a fisherman at heart. My mother taught piano at the local community center. Every morning I woke up to the sound of her practicing Chopin. The apartment smelled like salt air and sesame oil. I shared a room with my older brother Jihoon, and we had this rule — his side was Korea, my side was Japan, and the middle was the DMZ. Nobody crossed the DMZ without permission.",
      "key_quotes": [
        {
          "text": "My father was a fisherman — well, he ran a small fishing supply shop, but he always said he was a fisherman at heart.",
          "context": "Describing father's identity and self-image",
          "usable_in_chapter": true
        },
        {
          "text": "His side was Korea, my side was Japan, and the middle was the DMZ. Nobody crossed the DMZ without permission.",
          "context": "Childhood game with brother about room territory",
          "usable_in_chapter": true
        }
      ],
      "people_mentioned": [
        {"name": "Park Jihoon", "relationship": "older brother"},
        {"name": "Father (Park Sangwoo)", "relationship": "father"},
        {"name": "Mother (Lee Eunji)", "relationship": "mother"}
      ],
      "places_mentioned": [
        {"name": "Haeundae apartment", "city": "Busan", "country": "South Korea", "years_relevant": [1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002]}
      ],
      "events": [
        {
          "description": "Family moved into Haeundae apartment",
          "date_approximate": "1990",
          "significance": "background"
        }
      ],
      "emotional_markers": [
        {"emotion": "nostalgia", "trigger": "describing childhood apartment", "intensity": 6},
        {"emotion": "warmth", "trigger": "mother's piano practice", "intensity": 7}
      ]
    },
    {
      "segment_id": "SEG-002",
      "topic": "School experiences and friendships",
      "content": "I was terrible at math. I mean genuinely terrible. My teacher, Mrs. Kim — she was ancient, probably 60 but seemed 100 to me — she once held up my test paper and said 'Park Jimin, even my cat could score higher.' The whole class laughed. I wanted to disappear. But you know what saved me? The school library. I discovered science fiction books there. I read everything — Korean translations of Asimov, Clarke, and later Korean sci-fi authors. My best friend Taehyung and I would spend lunch breaks in the library making up our own stories about space travel. We filled three notebooks with our space adventures. I still have them somewhere.",
      "key_quotes": [
        {
          "text": "Park Jimin, even my cat could score higher.",
          "context": "Math teacher publicly humiliating him",
          "usable_in_chapter": true
        },
        {
          "text": "We filled three notebooks with our space adventures. I still have them somewhere.",
          "context": "Creative friendship with Taehyung",
          "usable_in_chapter": true
        }
      ],
      "people_mentioned": [
        {"name": "Mrs. Kim", "relationship": "math teacher"},
        {"name": "Kim Taehyung", "relationship": "best friend"}
      ],
      "places_mentioned": [
        {"name": "Elementary school library", "city": "Busan", "country": "South Korea", "years_relevant": [1997, 1998, 1999]}
      ],
      "events": [
        {
          "description": "Discovery of science fiction in school library",
          "date_approximate": "1997",
          "significance": "turning-point"
        }
      ],
      "emotional_markers": [
        {"emotion": "shame", "trigger": "math test humiliation", "intensity": 8},
        {"emotion": "joy", "trigger": "discovering sci-fi books", "intensity": 9}
      ]
    },
    {
      "segment_id": "SEG-003",
      "topic": "Father's shop and life lessons",
      "content": "After school I would go to my father's shop. It was this tiny place near the harbor, crammed with fishing lines and hooks and nets. The regulars were all old fishermen with these incredible weathered faces. My father would let me sit behind the counter and do homework while he served customers. The thing is, I learned more there than in any classroom. Those fishermen told stories — about storms, about the sea, about the Japanese occupation, about losing friends to the ocean. My father always said the same thing: 'Listen first, talk later.' I think that's why I became a writer. I learned to listen before I could even read properly.",
      "key_quotes": [
        {
          "text": "Listen first, talk later.",
          "context": "Father's core life philosophy",
          "usable_in_chapter": true
        },
        {
          "text": "I think that's why I became a writer. I learned to listen before I could even read properly.",
          "context": "Subject connecting childhood experience to career",
          "usable_in_chapter": true
        }
      ],
      "people_mentioned": [
        {"name": "Father (Park Sangwoo)", "relationship": "father"}
      ],
      "places_mentioned": [
        {"name": "Father's fishing supply shop", "city": "Busan", "country": "South Korea", "years_relevant": [1996, 1997, 1998, 1999, 2000, 2001, 2002]}
      ],
      "events": [
        {
          "description": "Regularly spending afternoons at father's shop after school",
          "date_approximate": "1996-2002",
          "significance": "milestone"
        }
      ],
      "emotional_markers": [
        {"emotion": "admiration", "trigger": "father's wisdom", "intensity": 8},
        {"emotion": "wonder", "trigger": "fishermen's stories", "intensity": 7}
      ]
    }
  ],
  "cross_references": []
}
TESTEOF

cat > test-data/micro-interviews/INT-002-university.json << 'TESTEOF'
{
  "meta": {
    "session_id": "INT-002",
    "subject_name": "Park Jimin",
    "interviewer": "ai-guided",
    "date": "2026-03-11",
    "duration_minutes": 50,
    "life_period": {
      "label": "University years in Seoul",
      "start_year": 2008,
      "end_year": 2012
    },
    "themes": ["education", "independence", "career-discovery"],
    "emotional_tone": "bittersweet"
  },
  "segments": [
    {
      "segment_id": "SEG-001",
      "topic": "Arriving in Seoul",
      "content": "Seoul hit me like a wall. I came from Busan where everything moves at ocean speed — slow, rhythmic. Seoul was a machine. I remember standing in Gangnam station for the first time, people rushing past me in every direction, and thinking I had made a terrible mistake. My dorm room at Yonsei was smaller than the DMZ between my brother's side and mine. But I had a window that looked out at the mountains, and every morning those mountains reminded me that nature doesn't care about your anxiety.",
      "key_quotes": [
        {
          "text": "Seoul hit me like a wall.",
          "context": "First impression of moving to Seoul from Busan",
          "usable_in_chapter": true
        },
        {
          "text": "Nature doesn't care about your anxiety.",
          "context": "Finding comfort in mountain view from dorm",
          "usable_in_chapter": true
        }
      ],
      "people_mentioned": [
        {"name": "Park Jihoon", "relationship": "older brother", "first_appearance_session": "INT-001"}
      ],
      "places_mentioned": [
        {"name": "Gangnam station", "city": "Seoul", "country": "South Korea", "years_relevant": [2008]},
        {"name": "Yonsei University dorm", "city": "Seoul", "country": "South Korea", "years_relevant": [2008, 2009]}
      ],
      "events": [
        {
          "description": "Moved to Seoul for university",
          "date_approximate": "2008-03",
          "significance": "turning-point"
        }
      ],
      "emotional_markers": [
        {"emotion": "overwhelm", "trigger": "arriving in Seoul", "intensity": 8},
        {"emotion": "comfort", "trigger": "mountain view from dorm", "intensity": 5}
      ]
    },
    {
      "segment_id": "SEG-002",
      "topic": "Discovering creative writing",
      "content": "I was supposed to study business. My father had this whole plan — I would get a business degree, come back to Busan, and eventually take over the shop. Expand it, modernize it, make it a chain. He never said it out loud, but I could see the blueprint in his eyes every time we video-called. Then in my second semester I took a creative writing elective. Professor Choi — she was this fierce woman who had published six novels and smoked on the rooftop between classes — she read my first short story aloud to the class. Not to embarrass me like Mrs. Kim. She read it because she said it was the most honest piece of writing she had seen from a student in years. That moment changed everything. I changed my major the next week. I didn't tell my father for three months.",
      "key_quotes": [
        {
          "text": "She read it because she said it was the most honest piece of writing she had seen from a student in years.",
          "context": "Professor Choi recognizing his writing talent",
          "usable_in_chapter": true
        },
        {
          "text": "I changed my major the next week. I didn't tell my father for three months.",
          "context": "Pivotal career decision and family tension",
          "usable_in_chapter": true
        }
      ],
      "people_mentioned": [
        {"name": "Professor Choi", "relationship": "creative writing professor"},
        {"name": "Father (Park Sangwoo)", "relationship": "father", "first_appearance_session": "INT-001"},
        {"name": "Mrs. Kim", "relationship": "math teacher", "first_appearance_session": "INT-001"}
      ],
      "places_mentioned": [
        {"name": "Yonsei University", "city": "Seoul", "country": "South Korea", "years_relevant": [2008, 2009, 2010, 2011, 2012]}
      ],
      "events": [
        {
          "description": "Changed major from business to creative writing",
          "date_approximate": "2008-10",
          "significance": "turning-point"
        },
        {
          "description": "Professor Choi reads his story to the class",
          "date_approximate": "2008-09",
          "significance": "turning-point"
        }
      ],
      "emotional_markers": [
        {"emotion": "guilt", "trigger": "hiding major change from father", "intensity": 7},
        {"emotion": "validation", "trigger": "professor praising his writing", "intensity": 9}
      ]
    }
  ],
  "cross_references": [
    {
      "from_segment": "SEG-002",
      "to_session": "INT-001",
      "to_segment": "SEG-002",
      "relationship": "contextualizes",
      "note": "Mrs. Kim's humiliation contrasted with Professor Choi's encouragement — both read his work aloud but with opposite intentions"
    }
  ]
}
TESTEOF

# ── 5. Golden Output (for comparison baseline) ─────────────────────────────
echo "[5/8] Creating golden output sample..."

cat > test-data/golden-outputs/chapter-1-golden.md << 'GOLDEN'
# Chapter 1: Salt Air and Sesame Oil

The apartment smelled like salt air and sesame oil. Every morning, before I opened my eyes, I could hear my mother playing Chopin — the same nocturne, over and over, until the notes became as natural as breathing. We lived in Haeundae then, before the high-rises swallowed the skyline, when you could still hear the fishing boats from our window.

My father was a fisherman — well, he ran a small fishing supply shop near the harbor, but he always said he was a fisherman at heart. I believed him. He had the hands for it, rough and sun-darkened, and he smelled like rope and diesel even on Sundays. His shop was a tiny place crammed with fishing lines and hooks and nets, and it was more of a gathering place than a business. The regulars were old men with incredible weathered faces who came as much for conversation as for supplies.

I shared a room with my older brother Jihoon. We had a system: his side was Korea, my side was Japan, and the narrow strip of floor between our beds was the DMZ. Nobody crossed the DMZ without permission. This was serious business. Violations resulted in immediate retaliation — usually a thrown pillow, sometimes worse. Looking back, it was our way of claiming something private in a space that gave us none.

After school, I would walk to my father's shop. He would let me sit behind the counter and do homework while he served customers, and I would listen to the fishermen tell their stories — about storms, about the sea, about the Japanese occupation, about friends they had lost to the ocean. My father always said the same thing when I asked him questions: "Listen first, talk later."

I was terrible at math. Genuinely terrible. My teacher, Mrs. Kim — she was probably 60 but seemed 100 to me — once held up my test paper in front of the entire class and said, "Park Jimin, even my cat could score higher." The whole class laughed, and I wanted to disappear into the floor. For weeks after that, I dreaded walking into her classroom.

But what Mrs. Kim took from me, the school library gave back. That was where I discovered science fiction — Korean translations of Asimov and Clarke at first, then Korean sci-fi authors whose names I can no longer remember but whose worlds I can still see. My best friend Taehyung and I would spend every lunch break in the library, hunched over notebooks, making up our own stories about space travel. We filled three notebooks with our space adventures. I still have them somewhere.

I think that's why I became a writer. Not because of any single moment or teacher or book. Because I learned to listen before I could even read properly, sitting behind that counter in my father's shop, absorbing the rhythms of other people's lives. The fishermen gave me stories. My father gave me patience. And Taehyung gave me someone to tell those stories to.
GOLDEN

# ── 6. Voice Profile Template ──────────────────────────────────────────────
echo "[6/8] Creating voice profile..."

cat > agents/voice-profile.yaml << 'VPEOF'
# Voice Profile: Park Jimin
# Generated from INT-001, INT-002 analysis
subject: "Park Jimin"
vocabulary:
  favorite_words: ["you know", "the thing is", "genuinely", "incredible", "this"]
  avoided_words: ["utilize", "leverage", "synergy", "basically"]
  filler_phrases: ["you know", "the thing is", "I mean", "well"]
  technical_jargon: []
sentence_patterns:
  avg_length: medium
  style: compound
  rhetorical_devices: ["self-correction", "em-dash asides", "lists of three", "concrete-then-abstract"]
storytelling:
  structure: chronological
  detail_level: rich
  humor_frequency: occasional
  emotional_expression: moderate
personality_markers:
  optimism: medium
  formality: casual
  self_reference: frequent
sample_phrases:
  - "My father was a fisherman — well, he ran a small fishing supply shop"
  - "I mean genuinely terrible"
  - "you know, before it became all fancy"
  - "The thing is, I learned more there than in any classroom"
  - "I think that's why I became a writer"
VPEOF

# ── 7. .gitignore ──────────────────────────────────────────────────────────
echo "[7/8] Creating .gitignore..."

cat > .gitignore << 'GIEOF'
# Generated outputs (large, should not be versioned)
outputs/drafts/*.md
outputs/chapters/*.md
outputs/comparisons/*.md
outputs/eval-reports/*.html

# Runtime state
autopilot-logs/
review-logs/

# promptfoo artifacts
eval/promptfoo/.promptfoo/
eval/promptfoo/output/
node_modules/

# Python
__pycache__/
*.pyc
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# Do NOT ignore these (they are versioned assets):
# !test-data/
# !schemas/
# !agents/prompts/
# !agents/prompts/versions/
# !.prompt-versions/
# !test-data/golden-outputs/
GIEOF

# ── 8. Git Hooks for Prompt Versioning ──────────────────────────────────────
echo "[8/8] Creating prompt versioning hook..."

mkdir -p .git-hooks

cat > .git-hooks/pre-commit-prompt-version << 'HOOKEOF'
#!/usr/bin/env bash
# Pre-commit hook: auto-version prompt files on change
# Install: ln -sf ../../autobiography-generator/.git-hooks/pre-commit-prompt-version .git/hooks/pre-commit

PROMPT_DIR="autobiography-generator/agents/prompts"
VERSION_LOG="autobiography-generator/.prompt-versions/changelog.md"

changed_prompts=$(git diff --cached --name-only -- "$PROMPT_DIR/*.md" 2>/dev/null)

if [ -z "$changed_prompts" ]; then
    exit 0
fi

echo "[prompt-version] Detected prompt changes:"

for f in $changed_prompts; do
    basename_f=$(basename "$f" .md)
    timestamp=$(date +"%Y%m%d-%H%M%S")

    # Extract current version from frontmatter
    current_version=$(grep -m1 'version:' "$f" | awk '{print $2}' || echo "0.0.0")

    # Auto-bump patch version
    IFS='.' read -r major minor patch <<< "$current_version"
    new_patch=$((patch + 1))
    new_version="${major}.${minor}.${new_patch}"

    # Save snapshot
    snapshot_dir="autobiography-generator/agents/prompts/versions"
    cp "$f" "${snapshot_dir}/${basename_f}-v${new_version}-${timestamp}.md"
    git add "${snapshot_dir}/${basename_f}-v${new_version}-${timestamp}.md"

    # Update version in file
    sed -i.bak "s/version: ${current_version}/version: ${new_version}/" "$f"
    rm -f "${f}.bak"
    git add "$f"

    # Append to changelog
    mkdir -p "$(dirname "$VERSION_LOG")"
    echo "- **${basename_f}**: v${current_version} -> v${new_version} (${timestamp})" >> "$VERSION_LOG"
    git add "$VERSION_LOG"

    echo "  $basename_f: v${current_version} -> v${new_version}"
done
HOOKEOF
chmod +x .git-hooks/pre-commit-prompt-version

# Create initial changelog
mkdir -p .prompt-versions
echo "# Prompt Version Changelog" > .prompt-versions/changelog.md
echo "" >> .prompt-versions/changelog.md
echo "Auto-generated by pre-commit hook." >> .prompt-versions/changelog.md
echo "" >> .prompt-versions/changelog.md

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Project structure:"
find . -type f -not -path './.git/*' -not -path './.git-hooks/*' -not -name '.DS_Store' | sort | head -40
echo ""
echo "Next steps:"
echo "  1. Install prompt versioning hook:"
echo "     ln -sf ../../autobiography-generator/.git-hooks/pre-commit-prompt-version .git/hooks/pre-commit"
echo "  2. Install Python deps:  pip install textstat pyyaml"
echo "  3. Install promptfoo:    npm install -g promptfoo"
echo "  4. Run dev loop:         bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json"
echo "  5. Run quality check:    python scripts/check.py outputs/chapters/"
echo ""
echo "Total setup time: ${SECONDS}s"
