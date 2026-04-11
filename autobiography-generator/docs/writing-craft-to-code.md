# Writing Craft to Code: Classical Methodology as Executable Infrastructure

> **Perspective**: 40 years of memoir craft, translated into executable prompts, schemas, and validation scripts for the AI Autobiography Generator pipeline.

---

## Table of Contents

1. [McAdams Life Story Interview → Agent Questions](#1-mcadams-life-story-interview--agent-questions)
2. [Kvale's Interview Framework → Conversation Flow Code](#2-kvales-interview-framework--conversation-flow-code)
3. [Narrative Structure → Outline Schema](#3-narrative-structure--outline-schema)
4. [Editorial Standards → Validation Rules](#4-editorial-standards--validation-rules)
5. [Ghostwriter Workflow → Pipeline Design](#5-ghostwriter-workflow--pipeline-design)
6. [Voice Capture Techniques → Prompt Code](#6-voice-capture-techniques--prompt-code)

---

## 1. McAdams Life Story Interview → Agent Questions

### Theoretical Foundation

Dan McAdams' Life Story Interview (LSI-II, 2007) is the most empirically validated protocol for eliciting narrative identity. The subject is asked to think of their life "as if it were a book or novel" and to describe its chapters, key scenes, significant people, future script, and central theme. The method produces structured, analyzable life narratives with consistent components across cultures and age groups.

The protocol maps directly onto the `@interviewer` agent's session design. Each McAdams domain becomes a session type with specific prompt sequences.

### Domain 1: Life Chapters (5 questions)

McAdams asks subjects to divide their entire life into "chapters" as if writing a book. This produces the chronological backbone that the `@story-architect` agent later transforms into the `chapter_plan` array in `story_bible.schema.json`.

```yaml
# Session type: life-chapters
# Maps to: story_bible.chapter_plan[], story_bible.timeline[]
# Output: Interview transcript with life period segments

questions:
  LC-01:
    prompt: >
      I'd like you to think about your life as if it were a book.
      Each part of your life composes a chapter. Think about at least
      two or three chapters and at most about seven or eight. Give
      each chapter a name, and describe the overall contents of each
      chapter. Tell me what each one is about, what the main theme is,
      and how one chapter flows into the next.
    follow_up:
      - "What would you title this chapter of your life?"
      - "When exactly did this chapter begin? Was there a specific moment?"
      - "How did you know this chapter was ending and a new one beginning?"
    maps_to_schema:
      - story_bible.chapter_plan[].title
      - story_bible.chapter_plan[].time_period
      - story_bible.chapter_plan[].summary

  LC-02:
    prompt: >
      Now think about the chapter you are living in right now.
      What is happening in it? What makes it different from the
      previous chapter?
    follow_up:
      - "What is the central challenge or question of this current chapter?"
      - "Who are the most important people in this chapter?"
    maps_to_schema:
      - story_bible.chapter_plan[-1]  # current chapter
      - story_bible.themes[]

  LC-03:
    prompt: >
      If you had to pick the single most important chapter —
      the one that made you who you are — which would it be?
      Why that one?
    maps_to_schema:
      - story_bible.timeline[].significance = "turning-point"

  LC-04:
    prompt: >
      Are there any chapters you would rather not have in the book?
      Chapters you wish you could rewrite or remove entirely?
    maps_to_schema:
      - interview_transcript.emotional_markers[]
      - story_bible.themes[] (regret, resilience)

  LC-05:
    prompt: >
      Looking at all the chapters together, do you see a pattern?
      Is your life story one of progress? Of struggle and redemption?
      Of things coming full circle?
    maps_to_schema:
      - story_bible.meta.tone_profile
      - story_bible.themes[].evolution
```

### Domain 2: Key Scenes (8 questions)

McAdams identifies eight specific scene types. Each produces a segment in the interview transcript with mandatory emotional markers, sensory details, and significance classification.

```yaml
# Session type: key-scenes
# Maps to: story_bible.timeline[], interview_transcript.segments[]
# Critical: These become the SCENES (not summaries) in the final prose

questions:
  KS-01_high_point:
    prompt: >
      Think about a specific moment in your life that stands out
      as a high point — a peak experience, a moment of great joy,
      excitement, or positive feeling. Please describe this scene
      in detail. What happened? When and where did it happen?
      Who was involved? What were you thinking and feeling?
      Why do you think this stands out as a high point?
    extraction_targets:
      - what_happened: narrative content
      - when_where: timeline + places
      - who_involved: characters[]
      - thoughts_feelings: emotional_markers[]
      - why_significant: themes[]
    scene_type: "high-point"
    significance: "turning-point"

  KS-02_low_point:
    prompt: >
      Now the opposite. Think about a moment that stands out as
      a low point — the worst moment, or at least a very negative
      experience. Again: What happened? When and where?
      Who was involved? What were you thinking and feeling?
      Why does this stand out as a low point?
    follow_up:
      - "How did you get through it?"
      - "Who helped you? Who was absent?"
      - "How do you make sense of that experience now?"
    scene_type: "low-point"
    significance: "turning-point"

  KS-03_turning_point:
    prompt: >
      Identify a moment in your life story when you went through
      an important change — a turning point. It might have been
      a gradual realization or a sudden event, but it marked a
      shift in how you understood yourself or your life.
      Describe the scene. What happened? What changed?
    follow_up:
      - "What were you like before this turning point?"
      - "What were you like after?"
      - "Did you recognize it as a turning point at the time, or only later?"
    scene_type: "turning-point"
    significance: "turning-point"

  KS-04_earliest_memory:
    prompt: >
      Think about one of the earliest memories you have — something
      that happened when you were quite young. It doesn't need to be
      verified or accurate. Just tell me the memory as you recall it,
      with as much detail as you can.
    follow_up:
      - "How old do you think you were?"
      - "What colors do you see in this memory?"
      - "Is anyone speaking? What are they saying?"
      - "What does the place smell like?"
    scene_type: "origin"
    significance: "milestone"

  KS-05_important_childhood_scene:
    prompt: >
      Tell me about a specific event from your childhood — something
      that happened before you were a teenager — that you remember
      vividly and that you think says something important about
      who you were becoming.
    scene_type: "formation"
    significance: "milestone"

  KS-06_important_adolescent_scene:
    prompt: >
      Now tell me about a specific event from your adolescence —
      from your teenage years. A moment that felt important at the
      time, or that you now realize was important.
    scene_type: "formation"
    significance: "milestone"

  KS-07_important_adult_scene:
    prompt: >
      Tell me about one specific event from your adult life that
      you consider important or memorable. What happened? Why does
      it matter?
    scene_type: "defining"
    significance: "milestone"

  KS-08_wisdom_event:
    prompt: >
      Can you tell me about a specific event in your life in which
      you learned something important about life — a moment of wisdom?
      Perhaps you were taught a lesson, or perhaps you arrived at
      the wisdom through your own experience. Describe the event
      and what you learned.
    follow_up:
      - "Has that lesson held up over time?"
      - "Have you ever passed that wisdom on to someone else?"
    scene_type: "epiphany"
    significance: "turning-point"
```

### Domain 3: Significant People (6 questions)

McAdams asks about heroes, mentors, and people who shaped the subject's life. This feeds directly into `story_bible.characters[]` and the character registry.

```yaml
# Session type: significant-people
# Maps to: story_bible.characters[], interview_transcript.people_mentioned[]

questions:
  SP-01_hero:
    prompt: >
      Every life story has heroes. Tell me about the person you
      most admire — someone who has been a hero or a role model
      to you. This can be someone you know personally or a
      historical/public figure. What is it about this person
      that makes them your hero?
    maps_to_schema:
      - characters[].relationship = "hero/role-model"
      - characters[].personality_summary

  SP-02_mentor:
    prompt: >
      Who has been the most important teacher or mentor in your
      life? Not necessarily a formal teacher — someone who taught
      you something essential about how to live. Describe a
      specific moment when they taught you something.
    follow_up:
      - "What exactly did they say or do?"
      - "How did you feel in that moment?"
      - "Can you hear their voice when you think about it?"
    maps_to_schema:
      - characters[].relationship = "mentor"
      - characters[].key_interactions[]

  SP-03_closest_person:
    prompt: >
      Who is the person you have been closest to in your life?
      Describe your relationship. How has it evolved over time?
      Tell me about a moment that captures what this relationship
      means to you.
    maps_to_schema:
      - characters[].importance = "primary"
      - characters[].arc

  SP-04_adversary:
    prompt: >
      Has there been anyone in your life who has stood as an
      adversary or opponent? Someone who challenged you, opposed
      you, or made your life more difficult? Tell me about this
      person and a specific encounter.
    follow_up:
      - "Looking back, did they teach you anything despite the conflict?"
      - "Have your feelings about this person changed over time?"
    maps_to_schema:
      - characters[].relationship = "adversary"
      - characters[].key_interactions[]

  SP-05_lost_relationship:
    prompt: >
      Tell me about a person who was once important in your life
      but who is no longer present — whether through death, distance,
      or a falling out. What do you miss most? What would you say
      to them if you could?
    maps_to_schema:
      - characters[].last_appearance
      - emotional_markers[].emotion = "grief" | "nostalgia"

  SP-06_unsung_person:
    prompt: >
      Is there someone in your life who deserves more recognition
      than they've received? Someone whose contribution to your
      story is often overlooked — maybe even by you until now?
    maps_to_schema:
      - characters[].importance  # may upgrade from "mentioned" to "secondary"
```

### Domain 4: Future Script (4 questions)

McAdams explores how subjects envision their future, revealing what they value most. This drives the final chapters of the memoir and its concluding theme.

```yaml
# Session type: future-script
# Maps to: story_bible.chapter_plan[-1] (final chapters), story_bible.themes[]

questions:
  FS-01:
    prompt: >
      What is the next chapter of your life? If you could write
      the next few years as you would want them to unfold, what
      would happen? Be specific — not what you hope in the abstract,
      but what a good Tuesday morning looks like, who is there,
      what you are doing.
    maps_to_schema:
      - chapter_plan[].summary (final chapter)

  FS-02:
    prompt: >
      What is your biggest dream for the future? Something you
      haven't achieved yet but still hope to? What would it take
      to get there?
    maps_to_schema:
      - themes[].name = "aspiration"

  FS-03:
    prompt: >
      What are you most afraid of for the future? What keeps you
      up at night?
    maps_to_schema:
      - emotional_markers[].emotion = "anxiety"
      - themes[].name = "fear/uncertainty"

  FS-04:
    prompt: >
      Imagine you are at the very end of your life, looking back
      on everything. What do you hope people will say about you?
      What legacy do you want to leave?
    maps_to_schema:
      - story_bible.meta.subtitle (often derived from legacy theme)
      - themes[].name = "legacy"
```

### Domain 5: Personal Ideology and Life Theme (7 questions)

McAdams probes the subject's values, beliefs, and their evolution. This produces the `themes[]` array and shapes the narrative's philosophical undercurrent.

```yaml
# Session type: ideology-and-theme
# Maps to: story_bible.themes[], story_bible.meta.tone_profile

questions:
  PI-01:
    prompt: >
      Do you believe in a higher power, a guiding principle,
      or a philosophy that gives your life meaning? How did
      you arrive at this belief? Has it changed over time?
    maps_to_schema:
      - themes[].name = "faith/philosophy"
      - themes[].evolution

  PI-02:
    prompt: >
      What is the most important value in your life? If you had
      to choose one principle that guides your decisions above
      all others, what would it be? Tell me about a time when
      you were tested on this value.
    maps_to_schema:
      - subject.defining_traits[].trait
      - subject.defining_traits[].evidence

  PI-03:
    prompt: >
      Has your political or social outlook changed significantly
      during your lifetime? What caused the change?
    maps_to_schema:
      - themes[].evolution

  PI-04:
    prompt: >
      What is the single most important thing you have learned
      about life? When did you learn it?
    maps_to_schema:
      - themes[].description

  PI-05:
    prompt: >
      If your entire life story had a single theme — one thread
      running through every chapter — what would it be?
    follow_up:
      - "When did you first become aware of this theme?"
      - "Has anyone else ever named this theme for you?"
    maps_to_schema:
      - story_bible.meta.subtitle
      - themes[0] (primary theme)

  PI-06:
    prompt: >
      What is the biggest contradiction in your life? A tension
      between two parts of yourself that has never fully resolved?
    maps_to_schema:
      - themes[].name = "internal-conflict"
      - subject.core_identity

  PI-07:
    prompt: >
      If you could go back and give a message to your younger self,
      not advice exactly, but something you understand now that you
      didn't then — what would it be?
    maps_to_schema:
      - chapter_plan[].closing_bridge (for final chapter)
      - themes[].evolution
```

### Integration with Existing `@interviewer` Agent

The 30 McAdams-derived questions above supplement the existing `@interviewer` agent's question bank. The implementation path:

```
McAdams Domain          →  Session Type           →  Schema Target
─────────────────────────────────────────────────────────────────────
Life Chapters (LC-01~05) →  life-chapters session  →  chapter_plan[]
Key Scenes (KS-01~08)   →  key-scenes sessions    →  timeline[], segments[]
Significant People       →  significant-people     →  characters[]
  (SP-01~06)                session
Future Script (FS-01~04) →  future-script session  →  chapter_plan[-1], themes[]
Personal Ideology        →  ideology-theme session →  themes[], meta.tone_profile
  (PI-01~07)
```

The existing `@interviewer` agent already covers childhood, adolescence, career, relationships, loss, and identity. McAdams adds structured depth: the "chapters" exercise gives chronological scaffolding, the eight key scene types ensure the most narratively potent moments are captured, and the ideology domain surfaces the philosophical substrate the `@story-architect` needs for theme analysis.

---

## 2. Kvale's Interview Framework → Conversation Flow Code

### Theoretical Foundation

Steinar Kvale (1996, *InterViews: An Introduction to Qualitative Research Interviewing*) identified nine types of interview questions. These are not question topics but question *mechanics* — they control the depth, direction, and quality of the subject's responses. For the AI interviewer agent, they become prompt templates that govern how the agent responds to any given subject answer.

### The Nine Types as Prompt Templates

```python
"""
Kvale's 9 question types as executable prompt templates.

Each type is a function that takes the subject's previous response
and returns a follow-up prompt. The @interviewer agent selects
the appropriate type based on response analysis.

Integration point: These templates are called by the @interviewer
agent's conversation loop. The agent's internal state machine
decides which Kvale type to deploy after each subject response.
"""

from dataclasses import dataclass
from enum import Enum


class KvaleType(str, Enum):
    INTRODUCING = "introducing"
    FOLLOW_UP = "follow_up"
    PROBING = "probing"
    SPECIFYING = "specifying"
    DIRECT = "direct"
    INDIRECT = "indirect"
    STRUCTURING = "structuring"
    SILENCE = "silence"
    INTERPRETING = "interpreting"


@dataclass
class KvalePrompt:
    """A Kvale-typed follow-up prompt with rationale."""
    kvale_type: KvaleType
    prompt_text: str
    when_to_use: str
    example_trigger: str
    danger_zone: str  # what NOT to do with this type


# ──────────────────────────────────────────────
# Type 1: INTRODUCING QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Open a new topic. Set the stage. Give the subject
# maximum freedom to choose their entry point.

INTRODUCING_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.INTRODUCING,
        prompt_text=(
            "Can you tell me about {topic}? "
            "Start wherever feels natural to you."
        ),
        when_to_use=(
            "Beginning of a new segment. The subject has not yet "
            "spoken about this topic. Use when transitioning between "
            "life periods or themes."
        ),
        example_trigger="Agent needs to move from childhood to adolescence.",
        danger_zone=(
            "Do NOT use introducing questions mid-story. If the subject "
            "is already deep in a memory, an introducing question breaks "
            "the flow and feels dismissive."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.INTRODUCING,
        prompt_text=(
            "I'd like to hear about {topic}. "
            "What comes to mind first when you think about that?"
        ),
        when_to_use="Alternative opener when the first form feels too clinical.",
        example_trigger="Sensitive topic where freedom of entry matters.",
        danger_zone="Avoid if the subject has already started on this topic.",
    ),
]


# ──────────────────────────────────────────────
# Type 2: FOLLOW-UP QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Pursue the content the subject just introduced.
# Signal active listening. Deepen without redirecting.

FOLLOW_UP_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.FOLLOW_UP,
        prompt_text="You mentioned {specific_detail}. Tell me more about that.",
        when_to_use=(
            "The subject has mentioned something interesting in passing — "
            "a name, a place, an event — but moved on without elaboration. "
            "This pulls them back to the unexplored detail."
        ),
        example_trigger=(
            "Subject says: 'My uncle used to take me fishing, but anyway, "
            "after high school I went to Seoul.' The fishing is unexplored."
        ),
        danger_zone=(
            "Do NOT follow up on every detail. Pick the one with the most "
            "narrative potential — emotional weight, sensory richness, or "
            "thematic relevance."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.FOLLOW_UP,
        prompt_text=(
            "What did you mean when you said '{quoted_phrase}'?"
        ),
        when_to_use=(
            "The subject used a phrase that is ambiguous, metaphorical, "
            "or emotionally charged. Clarification reveals deeper meaning."
        ),
        example_trigger=(
            "Subject says: 'That was when everything fell apart.' "
            "What exactly fell apart?"
        ),
        danger_zone="Do NOT quote back mundane phrases. It feels interrogative.",
    ),
    KvalePrompt(
        kvale_type=KvaleType.FOLLOW_UP,
        prompt_text=(
            "And what happened next?"
        ),
        when_to_use=(
            "The subject is in the middle of a story and paused. "
            "The simplest possible follow-up — keeps momentum."
        ),
        example_trigger="Subject is narrating a sequence and stops mid-event.",
        danger_zone=(
            "Do NOT use if the subject paused because of emotion. "
            "Use SILENCE instead."
        ),
    ),
]


# ──────────────────────────────────────────────
# Type 3: PROBING QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Push for depth and specificity. The subject gave
# a general answer; the probe demands the concrete.

PROBING_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.PROBING,
        prompt_text="Can you give me a specific example of that?",
        when_to_use=(
            "The subject has made a general claim ('My mother was strict') "
            "but has not grounded it in a specific scene. Probing converts "
            "TELLING into SHOWING — essential for the chapter writer."
        ),
        example_trigger="Subject says: 'Work was really stressful back then.'",
        danger_zone=(
            "Do NOT probe immediately after an emotional disclosure. "
            "Let the emotion land before asking for specifics."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.PROBING,
        prompt_text="Could you say more about that?",
        when_to_use=(
            "Gentler than asking for an example. Use when the subject "
            "is circling around something difficult."
        ),
        example_trigger="Subject gives a one-sentence answer to a deep question.",
        danger_zone="Do NOT overuse. Three probes in a row feels like pressure.",
    ),
    KvalePrompt(
        kvale_type=KvaleType.PROBING,
        prompt_text=(
            "Do you remember any examples of that? "
            "Even a small moment would help me understand."
        ),
        when_to_use=(
            "The subject has expressed a feeling or opinion but cannot "
            "immediately recall a scene. The 'even a small moment' phrase "
            "lowers the bar and reduces performance pressure."
        ),
        example_trigger="Subject says: 'I always felt like an outsider.'",
        danger_zone="Accept 'no' gracefully. Not every claim yields a scene.",
    ),
]


# ──────────────────────────────────────────────
# Type 4: SPECIFYING QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Extract the exact sensory and factual details
# the chapter writer needs to construct scenes.

SPECIFYING_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.SPECIFYING,
        prompt_text="When you say '{vague_term}', what exactly do you mean?",
        when_to_use=(
            "The subject used a word that could mean many things. "
            "'We had a fight' — verbal? physical? silent treatment? "
            "Specifying nails down the reality."
        ),
        example_trigger="Subject says: 'Things got complicated with my family.'",
        danger_zone=(
            "Do NOT specify trivial details. Specify only what affects "
            "the scene's meaning or the reader's mental image."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.SPECIFYING,
        prompt_text=(
            "What did that actually look like? "
            "If I were watching a film of that moment, what would I see?"
        ),
        when_to_use=(
            "The subject has described an event abstractly. This prompt "
            "forces visual, cinematic thinking — exactly what the "
            "chapter writer needs for scene construction."
        ),
        example_trigger="Subject says: 'The wedding was beautiful.'",
        danger_zone=(
            "Do NOT use the 'film' metaphor with subjects who find it "
            "artificial. Some people respond better to 'walk me through it.'"
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.SPECIFYING,
        prompt_text=(
            "What did you feel in your body at that moment? "
            "Where did you feel it?"
        ),
        when_to_use=(
            "Somatic memory is often more reliable than cognitive memory. "
            "This extracts physical sensations: stomach dropping, chest "
            "tightening, hands shaking. Invaluable for 'show don't tell.'"
        ),
        example_trigger="Subject describes a moment of fear, joy, or shock.",
        danger_zone=(
            "Do NOT push if the subject is uncomfortable with body-awareness "
            "questions. Some trauma survivors find this retraumatizing."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.SPECIFYING,
        prompt_text=(
            "What were the exact words? As close as you can remember."
        ),
        when_to_use=(
            "The subject is paraphrasing dialogue. Direct quotes are gold "
            "for the chapter writer — they carry voice, rhythm, and "
            "emotional charge that paraphrase destroys."
        ),
        example_trigger="Subject says: 'My father told me I had to leave.'",
        danger_zone=(
            "Accept approximate quotes. Prefacing with 'as close as you "
            "can remember' signals that perfection is not expected."
        ),
    ),
]


# ──────────────────────────────────────────────
# Type 5: DIRECT QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Get a straight answer to a factual question.
# Use sparingly — too many feel like an interrogation.

DIRECT_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.DIRECT,
        prompt_text="How old were you when that happened?",
        when_to_use=(
            "Timeline construction requires dates. Direct questions "
            "are the fastest way to anchor events. Use after the subject "
            "has told the story — not before."
        ),
        example_trigger="Subject has told a vivid story but gave no date.",
        danger_zone=(
            "Do NOT lead with direct questions. They shut down narrative "
            "flow. Save them for after the story is told."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.DIRECT,
        prompt_text="Were you happy during that time?",
        when_to_use=(
            "Sometimes the subject narrates events without naming emotions. "
            "A direct emotional question can unlock reflection. But only "
            "after the subject has described the situation."
        ),
        example_trigger="Subject recounts a major life change without affect.",
        danger_zone=(
            "Do NOT use yes/no emotional questions with subjects who "
            "are emotionally guarded. Use indirect questions instead."
        ),
    ),
]


# ──────────────────────────────────────────────
# Type 6: INDIRECT QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Get the subject's true opinion by asking
# through a proxy — what others thought, what it looked
# like from the outside.

INDIRECT_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.INDIRECT,
        prompt_text=(
            "What do you think other people saw when they looked at you "
            "during that time? How would they describe what was happening?"
        ),
        when_to_use=(
            "The subject is rationalizing or minimizing. Asking for an "
            "outside perspective often reveals what they are not saying "
            "directly. Produces material for the Gornick 'narrator' — "
            "the gap between situation and story."
        ),
        example_trigger=(
            "Subject says: 'It wasn't that bad.' "
            "But other details suggest it was."
        ),
        danger_zone=(
            "Do NOT imply you disbelieve them. Frame it as curiosity "
            "about different perspectives, not as a challenge."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.INDIRECT,
        prompt_text=(
            "If your {relationship} were sitting here telling me about "
            "that same event, what would they say happened?"
        ),
        when_to_use=(
            "Multi-perspective scene construction. The chapter writer "
            "can use these alternate viewpoints for dramatic irony or "
            "to deepen character complexity."
        ),
        example_trigger="Subject describes a family conflict from one side.",
        danger_zone="Do NOT use for recent, unresolved conflicts.",
    ),
]


# ──────────────────────────────────────────────
# Type 7: STRUCTURING QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Redirect the conversation. The subject has
# wandered off topic or exhausted a thread.

STRUCTURING_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.STRUCTURING,
        prompt_text=(
            "Thank you for sharing that. I'd like to move to a "
            "different part of your story now. Let's talk about {next_topic}."
        ),
        when_to_use=(
            "Time management. The session has a target set of topics. "
            "Structuring questions are the interviewer's steering wheel. "
            "Use after a natural pause, never mid-sentence."
        ),
        example_trigger=(
            "Subject has been on one topic for 20+ minutes and other "
            "critical topics remain uncovered."
        ),
        danger_zone=(
            "Do NOT structure away from a subject who is in the middle "
            "of an important emotional disclosure. Let them finish first."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.STRUCTURING,
        prompt_text=(
            "Earlier you mentioned {previous_topic}. I'd like to come "
            "back to that for a moment."
        ),
        when_to_use=(
            "The subject mentioned something important earlier that "
            "was not explored. This creates cross-references between "
            "segments in the transcript schema."
        ),
        example_trigger="An earlier mention went unexplored due to tangent.",
        danger_zone=(
            "Do NOT loop back to something the subject clearly wants "
            "to avoid. One attempt is acceptable; two is pushing."
        ),
    ),
]


# ──────────────────────────────────────────────
# Type 8: SILENCE
# ──────────────────────────────────────────────
# Purpose: Let the subject fill the space. The most
# powerful tool in the interviewer's repertoire.

SILENCE_TEMPLATE = KvalePrompt(
    kvale_type=KvaleType.SILENCE,
    prompt_text="[Agent waits 5-10 seconds without speaking]",
    when_to_use=(
        "After the subject has said something emotionally significant. "
        "After they pause mid-thought. Silence communicates: 'I am "
        "listening. There is no rush. You can go deeper.' "
        "In the AI context, this translates to NOT immediately "
        "generating a follow-up. Instead, the agent outputs a "
        "brief acknowledgment ('...') or simply waits for the "
        "subject's next input."
    ),
    example_trigger=(
        "Subject says: 'That was the last time I saw him.' "
        "[pause] — Do NOT fill this pause with a question."
    ),
    danger_zone=(
        "Do NOT use silence when the subject is confused or waiting "
        "for direction. Silence works after emotional moments; it "
        "fails after logistical questions."
    ),
)

# Implementation note for AI context:
# The @interviewer agent implements silence by:
# 1. Detecting emotional_markers with intensity >= 7
# 2. Responding with only: "..." or "Take your time."
# 3. Waiting for the subject's next message before asking anything


# ──────────────────────────────────────────────
# Type 9: INTERPRETING QUESTIONS
# ──────────────────────────────────────────────
# Purpose: Offer the subject a mirror. Reflect back what
# you heard and ask if the interpretation is correct.
# This produces the "Story" (Gornick) — the meaning
# beneath the situation.

INTERPRETING_TEMPLATES = [
    KvalePrompt(
        kvale_type=KvaleType.INTERPRETING,
        prompt_text=(
            "So it sounds like what you're saying is {interpretation}. "
            "Is that right, or am I reading too much into it?"
        ),
        when_to_use=(
            "The subject has told a story but has not articulated its "
            "meaning. The interpreting question offers a meaning for "
            "them to confirm, modify, or reject. This is the bridge "
            "between raw memory and narrative theme."
        ),
        example_trigger=(
            "Subject tells a long story about changing jobs. "
            "Agent interprets: 'It sounds like what mattered most "
            "wasn't the new job itself, but proving to yourself that "
            "you could start over. Is that right?'"
        ),
        danger_zone=(
            "Do NOT project. The interpretation must arise from what "
            "the subject actually said, not from the agent's pattern "
            "matching. Always give them room to correct: 'or am I "
            "reading too much into it?' The subject's correction is "
            "often more revealing than the original story."
        ),
    ),
    KvalePrompt(
        kvale_type=KvaleType.INTERPRETING,
        prompt_text=(
            "I notice that when you talk about {topic_a}, you use "
            "similar language to when you talked about {topic_b}. "
            "Do you see a connection there?"
        ),
        when_to_use=(
            "Cross-session pattern detection. The agent has identified "
            "a thematic link across segments. Offering this link to "
            "the subject for confirmation produces validated themes "
            "for the story bible."
        ),
        example_trigger=(
            "Subject describes both their father's discipline and their "
            "own management style using words like 'fairness' and 'respect.'"
        ),
        danger_zone=(
            "Do NOT force connections. If the subject says 'No, those "
            "are completely different,' accept it. Document the agent's "
            "hypothesis as a rejected interpretation — it may still be "
            "useful for the story architect's theme analysis."
        ),
    ),
]
```

### Conversation Flow State Machine

The nine Kvale types form a state machine that the `@interviewer` agent traverses during each session:

```
                    ┌─────────────┐
                    │ INTRODUCING │ ← New topic entry
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
               ┌───▶│  FOLLOW-UP  │◀──┐
               │    └──────┬──────┘   │
               │           │          │
               │           ▼          │
               │    ┌─────────────┐   │
               │    │   PROBING   │───┘ (subject gives general answer)
               │    └──────┬──────┘
               │           │
               │           ▼
               │    ┌─────────────┐
               │    │ SPECIFYING  │ ← Extract sensory/factual details
               │    └──────┬──────┘
               │           │
               │           ▼
               │    ┌──────┴──────┐
               │    │   DIRECT    │ ← Pin down dates, names, facts
               │    └──────┬──────┘
               │           │
               │    ┌──────┴──────┐
               │    │  INDIRECT   │ ← Access guarded material
               │    └──────┬──────┘
               │           │
               │           ▼
               │    ┌─────────────┐
               │    │  SILENCE    │ ← After emotional disclosure
               │    └──────┬──────┘
               │           │
               │           ▼
               │    ┌─────────────┐
               │    │INTERPRETING │ ← Offer meaning, confirm themes
               │    └──────┬──────┘
               │           │
               │           ▼
               │    ┌──────┴──────┐
               └────┤ STRUCTURING │ ← Move to next topic
                    └─────────────┘
```

### Selection Logic

```python
def select_kvale_type(
    subject_response: str,
    current_segment_topic: str,
    emotional_intensity: int,
    elapsed_minutes: int,
    topics_remaining: list[str],
    response_word_count: int,
) -> KvaleType:
    """
    Decide which Kvale question type to use next.

    This is the interviewer agent's core decision function.
    It analyzes the subject's response and selects the
    appropriate follow-up type.
    """
    # Rule 1: Emotional moments get SILENCE
    if emotional_intensity >= 7:
        return KvaleType.SILENCE

    # Rule 2: One-word or very short answers get PROBING
    if response_word_count < 15:
        return KvaleType.PROBING

    # Rule 3: Abstract or generalized responses get SPECIFYING
    if _is_abstract(subject_response):
        return KvaleType.SPECIFYING

    # Rule 4: Rich stories without dates/names get DIRECT
    if response_word_count > 100 and _lacks_specifics(subject_response):
        return KvaleType.DIRECT

    # Rule 5: Time pressure with remaining topics → STRUCTURING
    if elapsed_minutes > 45 and len(topics_remaining) > 3:
        return KvaleType.STRUCTURING

    # Rule 6: Subject mentions something from a previous session → FOLLOW-UP
    if _references_earlier_topic(subject_response):
        return KvaleType.FOLLOW_UP

    # Rule 7: Subject seems guarded or minimizing → INDIRECT
    if _seems_guarded(subject_response):
        return KvaleType.INDIRECT

    # Rule 8: Rich story told, no meaning extracted → INTERPRETING
    if response_word_count > 80 and not _contains_reflection(subject_response):
        return KvaleType.INTERPRETING

    # Default: Keep exploring the current thread
    return KvaleType.FOLLOW_UP
```

---

## 3. Narrative Structure → Outline Schema

### Theoretical Foundation

Three craft traditions converge here:

1. **Vivian Gornick** (*The Situation and the Story*): Every memoir has a *situation* (what happened) and a *story* (what the narrator has come to understand about what happened). The situation provides material; the story provides meaning.

2. **The Scene/Summary Spectrum**: Scenes render moment-by-moment experience with dialogue, sensory detail, and real-time action. Summaries compress time, provide context, and move the narrative forward. Professional memoir maintains roughly 70-80% scene to 20-30% summary.

3. **Three-Act Structure Applied to Memoir**: Act I (the world before disruption), Act II (the struggle), Act III (the new understanding). This applies both to the memoir as a whole and to each individual chapter.

### Narrative Structure Schema (YAML)

```yaml
# narrative_structure.schema.yaml
# Extends story_bible.schema.json with craft-specific structure
# Used by @story-architect to build chapter plans

memoir_arc:
  # Gornick's framework: every memoir has both
  situation:
    description: >
      The raw material — what happened. The facts, events, and
      circumstances of the subject's life. This is the WHAT.
    source: "interview transcripts"
    schema_field: "story_bible.timeline[]"

  story:
    description: >
      The insight — what the narrator has come to understand about
      what happened. This is the WHY. The story is what separates
      a memoir from a diary entry. It is the wisdom gained, the
      pattern recognized, the meaning constructed from raw experience.
    source: "interpreting questions (Kvale Type 9) + ideology domain (McAdams)"
    schema_field: "story_bible.themes[]"

  narrator_persona:
    description: >
      The constructed 'I' who tells the story. Not the subject as
      they were when events happened, but the subject as they are
      now, looking back with understanding. The gap between the
      experiencing self and the narrating self is where memoir lives.
    implementation: >
      The @chapter-writer agent writes in first person but maintains
      two registers: (1) the experiencing voice — present-tense
      sensation, confusion, raw emotion; (2) the narrating voice —
      reflective, interpretive, connecting past to present.
      The balance between them is controlled by content_type:
      "scene" uses the experiencing voice; "reflection" uses
      the narrating voice.

overall_structure:
  # Three-act structure applied to the entire memoir
  act_1_setup:
    chapters: "1-3 (approximately first 25% of total word count)"
    purpose: >
      Establish the world the subject came from. The family, the
      place, the cultural context. Introduce the central tension
      or question that will drive the narrative. The reader must
      understand what 'normal' looked like before it was disrupted.
    must_contain:
      - "Origin scene (McAdams KS-04: earliest memory)"
      - "At least 2 primary characters introduced with full scenes"
      - "The physical world rendered in sensory detail"
      - "The seed of the central theme planted (not stated)"
    pacing: "Slow. Immersive. Heavy on scene, light on summary."

  act_2_confrontation:
    chapters: "4-8 (approximately 50% of total word count)"
    purpose: >
      The struggle. Whatever the central tension is — leaving home,
      building a career, surviving loss, finding identity — this is
      where it plays out. The longest act. Contains the turning points,
      the low points, and the pivotal relationships.
    must_contain:
      - "Turning point scene (McAdams KS-03)"
      - "Low point scene (McAdams KS-02)"
      - "Mentor/adversary relationships developed (McAdams SP-02, SP-04)"
      - "At least one chapter with primarily dialogue-driven scenes"
      - "The central theme tested — the subject's beliefs challenged"
    pacing: >
      Variable. Alternating between slow, deep scenes and faster
      summary passages. The pacing itself tells the story — slow
      down for what matters, speed up for transitions.

  act_3_resolution:
    chapters: "9-12 (approximately 25% of total word count)"
    purpose: >
      The new understanding. Not necessarily a happy ending, but
      a landing. The subject has been changed by the events of
      Act II and now sees the world differently. The 'story'
      (Gornick) is fully articulated here — not didactically,
      but through the final scenes and the narrator's voice.
    must_contain:
      - "High point scene or wisdom event (McAdams KS-01, KS-08)"
      - "Future script (McAdams FS-01)"
      - "Central theme resolved or reframed"
      - "Callback to an image or moment from Act I (circularity)"
    pacing: "Slowing down. Return to the immersive pace of Act I."

chapter_beat_sheet:
  # Each chapter follows its own mini-arc
  # This template is applied to every chapter_plan[] entry
  template:
    opening_beat:
      type: "hook"
      word_count_range: [100, 500]
      content_type: "scene"
      description: >
        The first paragraph. Must hook the reader with a concrete
        image, a provocative statement, or a scene already in motion.
        NEVER open with 'I was born...' or 'The year was...'
      validation: >
        Must contain at least one sensory detail. Must NOT begin
        with an abstract statement. Must NOT be longer than 500 words
        before the first scene break.

    establishing_beat:
      type: "context"
      word_count_range: [300, 800]
      content_type: "exposition"
      description: >
        Orient the reader in time and place. Who are we? When are we?
        What is the situation (Gornick)? This is one of the few places
        where summary/telling is appropriate — but keep it grounded
        in specific detail.

    rising_beat_1:
      type: "scene"
      word_count_range: [500, 2000]
      content_type: "scene"
      description: >
        First major scene of the chapter. A specific moment rendered
        in real time with dialogue, action, and sensory detail.
        This is where 'show don't tell' is non-negotiable.
      requirements:
        - "At least 2 characters present and interacting"
        - "Dialogue (at least 3 exchanges)"
        - "Sensory details from at least 2 senses"
        - "Grounded in a specific place (from places registry)"

    rising_beat_2:
      type: "scene_or_montage"
      word_count_range: [400, 1500]
      content_type: "scene | montage"
      description: >
        A second scene that advances the chapter's arc, or a montage
        (compressed time, multiple small moments) that shows a pattern.
        Montage is useful for 'the years of routine' — the parts of
        life that matter but don't contain single dramatic moments.

    pivot_beat:
      type: "turning_point"
      word_count_range: [300, 1000]
      content_type: "scene"
      description: >
        The moment when something shifts. A decision made, a truth
        revealed, a relationship changed. This is the chapter's
        mini-turning-point. Not every chapter has a dramatic pivot —
        sometimes the pivot is internal, a shift in understanding.
      validation: >
        The emotional tone after the pivot must differ from before it.
        Check emotional_markers: pre-pivot and post-pivot should show
        different dominant emotions.

    reflection_beat:
      type: "interiority"
      word_count_range: [200, 600]
      content_type: "reflection"
      description: >
        The narrator steps back from the scene and reflects. This is
        the 'story' (Gornick) — the meaning. What did the experiencing
        self not understand that the narrating self now sees? Use the
        narrating voice here, not the experiencing voice.
      validation: >
        Must contain at least one sentence that connects this chapter's
        events to a theme in the story bible. Must NOT be preachy or
        didactic — the reflection should feel like genuine thought,
        not a lecture.

    closing_beat:
      type: "bridge"
      word_count_range: [100, 400]
      content_type: "transition"
      description: >
        The final paragraph. Creates momentum toward the next chapter.
        Three techniques: (1) end on an unanswered question;
        (2) end on an image that will recur in the next chapter;
        (3) end with a one-sentence time skip ('Three months later...').
      validation: >
        Must NOT resolve everything. Must create forward pull.
        Check that it connects to the next chapter's opening_hook
        in the story bible chapter plan.

scene_vs_summary_ratio:
  # The balance between showing (scene) and telling (summary)
  # Applied as a validation metric in chapter_draft.schema.json
  target_scene_percentage: 75
  minimum_scene_percentage: 60
  maximum_summary_percentage: 40
  calculation: >
    Sum word counts of sections where content_type IN
    ('scene', 'dialogue') and divide by total chapter word count.
    Sections with content_type IN ('exposition', 'transition', 'montage')
    count as summary. 'reflection' counts as 50% scene (it is the
    narrator's interiority, a form of showing the thinking mind).
  remediation: >
    If scene percentage falls below 60%, the @reviewer agent flags
    ISS-xxx with category 'pacing-issue' and severity 'warning'.
    The chapter writer is instructed to convert at least one
    exposition passage into a rendered scene.
```

### Integration with Existing Schemas

The narrative structure schema extends `story_bible.schema.json` through the `chapter_plan[]` entries. Each chapter plan entry already has `opening_hook`, `closing_bridge`, and `narrative_technique`. The beat sheet above provides the internal structure that the `@chapter-writer` agent uses to organize the prose between those hooks and bridges.

The `content_type` enum in `chapter_draft.schema.json` already includes `"scene", "reflection", "exposition", "dialogue", "transition", "montage"` — these map directly to the beat types above.

---

## 4. Editorial Standards → Validation Rules

### Theoretical Foundation

Professional editors evaluate memoir along measurable dimensions: concreteness of language, balance of scene and exposition, sentence variety, voice consistency, and emotional modulation. These traditionally subjective judgments can be approximated with computable heuristics. The code below is designed to run as a post-processing step after the `@chapter-writer` produces a draft, feeding results into `chapter_draft.voice_metrics` and informing the `@reviewer` agent's evaluation.

### Complete Validation Module

```python
"""
editorial_validators.py — Writing craft rules as executable code.

Translates professional editorial standards into measurable metrics.
Each validator produces a score and diagnostic details that feed into
chapter_draft.schema.json voice_metrics and review_verdict.schema.json issues.

Usage:
    from scripts.editorial_validators import validate_chapter
    results = validate_chapter(prose_text, voice_guide)
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field


# ──────────────────────────────────────────────
# Data classes for validation results
# ──────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Result of a single editorial validation check."""
    check_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    locations: list[str] = field(default_factory=list)
    severity: str = "suggestion"  # "critical" | "warning" | "suggestion"


@dataclass
class ChapterValidation:
    """Aggregated validation results for a chapter."""
    chapter_number: int
    word_count: int
    results: list[ValidationResult]
    overall_score: float  # Average of all check scores

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results if r.severity == "critical")

    @property
    def critical_failures(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed and r.severity == "critical"]


# ──────────────────────────────────────────────
# Check 1: SHOW vs TELL Detector
# ──────────────────────────────────────────────
# Craft principle: "Show, don't tell."
# Implementation: Ratio of concrete/sensory language to
# abstract/emotional-label language.

# Words that TELL (state emotions directly)
TELLING_INDICATORS = {
    # Emotional labels — the writer names the emotion instead of showing it
    "happy", "sad", "angry", "afraid", "scared", "nervous",
    "excited", "worried", "anxious", "depressed", "elated",
    "furious", "terrified", "delighted", "miserable", "ecstatic",
    "frustrated", "disappointed", "grateful", "jealous", "lonely",
    "ashamed", "embarrassed", "proud", "guilty", "confused",
    # Abstract state verbs
    "felt", "realized", "understood", "knew", "believed",
    "thought", "wondered", "decided", "seemed", "appeared",
    # Evaluation words
    "beautiful", "terrible", "wonderful", "horrible", "amazing",
    "awful", "great", "good", "bad", "nice", "interesting",
}

# Words that SHOW (concrete, sensory, action)
SHOWING_INDICATORS = {
    # Sensory verbs
    "smelled", "tasted", "heard", "watched", "saw", "touched",
    "pressed", "gripped", "clenched", "shivered", "trembled",
    "whispered", "shouted", "murmured", "stammered", "gasped",
    "stumbled", "ran", "crept", "slammed", "grabbed",
    # Body language
    "flinched", "winced", "stiffened", "slouched", "paced",
    "fidgeted", "squinted", "blinked", "swallowed", "exhaled",
    "inhaled", "sighed", "groaned", "shrugged", "nodded",
    # Concrete nouns (partial — expanded in production)
    "door", "window", "floor", "ceiling", "wall", "table",
    "chair", "road", "sun", "rain", "wind", "shadow",
    "hand", "face", "voice", "eyes", "mouth", "fingers",
}


def check_show_vs_tell(text: str) -> ValidationResult:
    """
    Measure the ratio of concrete/sensory language to abstract/telling language.

    Craft rule: Professional editors expect a show:tell ratio of at least 2:1
    in scene sections. In reflection sections, the ratio naturally drops.
    A chapter-wide ratio below 1.5 signals over-reliance on telling.

    Returns:
        ValidationResult with score = show_count / (tell_count + 1)
    """
    words = re.findall(r'\b\w+\b', text.lower())
    word_set = Counter(words)

    tell_count = sum(word_set.get(w, 0) for w in TELLING_INDICATORS)
    show_count = sum(word_set.get(w, 0) for w in SHOWING_INDICATORS)

    # Find specific "telling" sentences for location reporting
    telling_locations = []
    sentences = _split_sentences(text)
    for i, sent in enumerate(sentences, 1):
        sent_words = set(re.findall(r'\b\w+\b', sent.lower()))
        tell_words_in_sent = sent_words & TELLING_INDICATORS
        show_words_in_sent = sent_words & SHOWING_INDICATORS
        # Flag sentences that are pure tell with no show
        if len(tell_words_in_sent) >= 2 and len(show_words_in_sent) == 0:
            telling_locations.append(
                f"Sentence {i}: '{sent[:80]}...' "
                f"(tell words: {', '.join(tell_words_in_sent)})"
            )

    ratio = show_count / (tell_count + 1)  # +1 to avoid division by zero
    passed = ratio >= 1.5
    severity = "critical" if ratio < 1.0 else "warning" if ratio < 1.5 else "suggestion"

    return ValidationResult(
        check_name="show_vs_tell_ratio",
        passed=passed,
        score=min(ratio / 3.0, 1.0),  # Normalize: 3.0 ratio = perfect score
        details=(
            f"Show:Tell ratio = {ratio:.2f} "
            f"(show_words={show_count}, tell_words={tell_count}). "
            f"Target >= 2.0 for scenes, >= 1.5 chapter-wide. "
            f"Found {len(telling_locations)} pure-telling sentences."
        ),
        locations=telling_locations[:10],  # Cap at 10 most egregious
        severity=severity,
    )


# ──────────────────────────────────────────────
# Check 2: Pacing Analysis
# ──────────────────────────────────────────────
# Craft principle: Vary pace. Slow down for important moments.
# Speed up for transitions. The reader's experience of time
# should match the emotional weight of events.

def check_pacing(
    text: str,
    sections: list[dict],
) -> ValidationResult:
    """
    Analyze pacing by measuring word count per section type.

    Craft rule: Turning-point scenes should be at least 2x the
    word count of transition sections. If a turning point gets
    fewer words than a transition, the pacing is inverted — the
    important moments are being rushed.

    Args:
        text: Full chapter prose
        sections: List of section dicts from chapter_draft.structure.sections
                  Each must have 'content_type' and 'word_count'
    """
    type_counts: dict[str, list[int]] = {}
    for section in sections:
        ct = section.get("content_type", "exposition")
        wc = section.get("word_count", 0)
        type_counts.setdefault(ct, []).append(wc)

    avg_by_type = {
        ct: statistics.mean(counts) for ct, counts in type_counts.items()
    }

    issues = []

    # Check 1: Scenes should be longer than transitions
    avg_scene = avg_by_type.get("scene", 0)
    avg_transition = avg_by_type.get("transition", 0)
    if avg_transition > 0 and avg_scene < avg_transition * 1.5:
        issues.append(
            f"Scenes avg {avg_scene:.0f} words vs transitions avg "
            f"{avg_transition:.0f} words. Scenes should be at least "
            f"1.5x transition length."
        )

    # Check 2: Dialogue sections should not dominate
    avg_dialogue = avg_by_type.get("dialogue", 0)
    total_words = sum(s.get("word_count", 0) for s in sections)
    total_dialogue = sum(type_counts.get("dialogue", []))
    dialogue_pct = (total_dialogue / total_words * 100) if total_words > 0 else 0
    if dialogue_pct > 50:
        issues.append(
            f"Dialogue is {dialogue_pct:.0f}% of chapter. "
            f"Memoir typically keeps dialogue under 40%."
        )

    # Check 3: Reflection should not exceed 25% of chapter
    total_reflection = sum(type_counts.get("reflection", []))
    reflection_pct = (total_reflection / total_words * 100) if total_words > 0 else 0
    if reflection_pct > 25:
        issues.append(
            f"Reflection is {reflection_pct:.0f}% of chapter. "
            f"Over 25% risks 'navel-gazing.' Show more, reflect less."
        )

    # Check 4: Scene percentage (the scene-vs-summary ratio)
    scene_words = sum(type_counts.get("scene", [])) + sum(type_counts.get("dialogue", []))
    scene_pct = (scene_words / total_words * 100) if total_words > 0 else 0
    if scene_pct < 60:
        issues.append(
            f"Scene content is {scene_pct:.0f}% of chapter. "
            f"Target is 60-80%. Chapter is too heavy on summary/exposition."
        )

    passed = len(issues) == 0
    score = max(0, 1.0 - len(issues) * 0.25)

    return ValidationResult(
        check_name="pacing_analysis",
        passed=passed,
        score=score,
        details=(
            f"Section type distribution: {avg_by_type}. "
            + (" ".join(issues) if issues else "Pacing is well-balanced.")
        ),
        locations=issues,
        severity="warning" if issues else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 3: Emotional Arc Tracker
# ──────────────────────────────────────────────
# Craft principle: Emotional variation. A chapter that stays
# at one emotional register is monotonous. A memoir that only
# escalates is exhausting. Track the emotional valence across
# sections and flag flatlines.

# Simple sentiment lexicon for emotional valence
POSITIVE_MARKERS = {
    "laughed", "smiled", "joy", "love", "warm", "bright",
    "hope", "peace", "gentle", "tender", "delighted", "grateful",
    "proud", "free", "relief", "comfort", "embrace", "kiss",
    "celebration", "triumph", "home", "safe", "trust", "light",
}

NEGATIVE_MARKERS = {
    "cried", "screamed", "pain", "loss", "cold", "dark",
    "fear", "rage", "bitter", "sharp", "grieved", "ashamed",
    "alone", "trapped", "broken", "betrayed", "abandoned",
    "silence", "empty", "helpless", "dread", "ache", "scar",
}


def check_emotional_arc(
    text: str,
    sections: list[dict],
) -> ValidationResult:
    """
    Track emotional valence across chapter sections.

    Craft rule: A good chapter has emotional variation — it moves
    between registers. A 'flat' chapter (all positive or all negative)
    lacks the contrast that makes individual moments land.

    Professional editors look for at least one emotional shift per chapter.
    """
    section_valences = []

    for section in sections:
        heading = section.get("heading", "")
        # Use heading as a proxy for section text boundary
        # In production, use actual section content boundaries
        section_text = text  # Simplified; production splits by section
        words = set(re.findall(r'\b\w+\b', section_text.lower()))

        pos_count = len(words & POSITIVE_MARKERS)
        neg_count = len(words & NEGATIVE_MARKERS)
        total = pos_count + neg_count

        if total == 0:
            valence = 0.0
        else:
            valence = (pos_count - neg_count) / total  # -1.0 to 1.0

        section_valences.append({
            "section": heading,
            "valence": valence,
            "positive_words": pos_count,
            "negative_words": neg_count,
        })

    # Check for emotional flatness
    if len(section_valences) >= 2:
        valences = [sv["valence"] for sv in section_valences]
        valence_range = max(valences) - min(valences)
        has_shift = valence_range >= 0.3  # At least 0.3 range
    else:
        has_shift = True  # Single-section chapters are exempt
        valence_range = 0

    passed = has_shift
    score = min(valence_range / 0.6, 1.0)  # 0.6 range = perfect

    return ValidationResult(
        check_name="emotional_arc",
        passed=passed,
        score=score,
        details=(
            f"Emotional valence range: {valence_range:.2f} "
            f"(target >= 0.3). Sections: "
            + ", ".join(
                f"{sv['section']}: {sv['valence']:+.2f}"
                for sv in section_valences
            )
        ),
        severity="warning" if not passed else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 4: Sensory Detail Frequency
# ──────────────────────────────────────────────
# Craft principle: Memoir lives in the senses. Every scene
# should engage at least 2 of the 5 senses. Sight alone
# is insufficient — the best memoir engages smell, sound,
# touch, and taste to anchor the reader in lived experience.

SENSORY_PATTERNS = {
    "sight": re.compile(
        r'\b(saw|watched|looked|glanced|stared|gazed|bright|dark|'
        r'shadow|color|light|red|blue|green|white|black|golden|'
        r'silver|glow|shimmer|dim|blinding|faded)\b',
        re.IGNORECASE,
    ),
    "sound": re.compile(
        r'\b(heard|listened|sound|noise|silence|quiet|loud|'
        r'whisper|shout|scream|murmur|hum|buzz|crack|thud|'
        r'ring|echo|rhythm|melody|voice|laugh|cry|rustle)\b',
        re.IGNORECASE,
    ),
    "smell": re.compile(
        r'\b(smelled|scent|odor|fragrance|aroma|stink|musty|'
        r'fresh|perfume|smoke|cooking|baking|pine|earth|'
        r'rain|salt|sweat|coffee|bread|flowers)\b',
        re.IGNORECASE,
    ),
    "touch": re.compile(
        r'\b(felt|touched|rough|smooth|soft|hard|cold|warm|'
        r'hot|wet|dry|sharp|dull|pressure|weight|heavy|'
        r'light|sticky|slippery|grip|squeeze|scratch|silk|'
        r'velvet|sand|stone|skin|fingers)\b',
        re.IGNORECASE,
    ),
    "taste": re.compile(
        r'\b(tasted|sweet|bitter|sour|salty|savory|bland|'
        r'spicy|rich|tang|metallic|mouth|tongue|swallow|'
        r'bite|chew|sip|drink|eat)\b',
        re.IGNORECASE,
    ),
}


def check_sensory_detail(text: str) -> ValidationResult:
    """
    Count sensory references per 1000 words and check sense diversity.

    Craft rule: Professional editors expect:
    - At least 5 sensory details per 1000 words in scenes
    - At least 3 different senses engaged per chapter
    - Smell and taste are the most underused and most evocative —
      their presence signals strong craft
    """
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    per_1000 = 1000 / max(word_count, 1)

    sense_counts = {}
    sense_examples = {}

    for sense_name, pattern in SENSORY_PATTERNS.items():
        matches = pattern.findall(text)
        sense_counts[sense_name] = len(matches)
        if matches:
            sense_examples[sense_name] = matches[:3]

    total_sensory = sum(sense_counts.values())
    sensory_per_1000 = total_sensory * per_1000
    senses_engaged = sum(1 for c in sense_counts.values() if c > 0)

    issues = []
    if sensory_per_1000 < 5:
        issues.append(
            f"Sensory density: {sensory_per_1000:.1f}/1000 words "
            f"(target: >= 5). Add more concrete sensory details."
        )
    if senses_engaged < 3:
        missing = [s for s, c in sense_counts.items() if c == 0]
        issues.append(
            f"Only {senses_engaged}/5 senses engaged. "
            f"Missing: {', '.join(missing)}. "
            f"Especially consider smell and taste — they are the "
            f"most memory-linked senses."
        )

    passed = sensory_per_1000 >= 5 and senses_engaged >= 3
    score = min(sensory_per_1000 / 10, 1.0) * (senses_engaged / 5)

    return ValidationResult(
        check_name="sensory_detail_frequency",
        passed=passed,
        score=score,
        details=(
            f"Sensory density: {sensory_per_1000:.1f}/1000 words. "
            f"Senses: {sense_counts}. "
            f"Examples: {sense_examples}"
        ),
        locations=issues,
        severity="warning" if not passed else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 5: Dialogue Authenticity
# ──────────────────────────────────────────────
# Craft principle: Dialogue in memoir must sound like real
# speech, not literary performance. Professional editors
# check for: attribution variety, unnatural phrasing,
# excessive dialogue tags, and information dumps disguised
# as conversation.

def check_dialogue_authenticity(text: str) -> ValidationResult:
    """
    Analyze dialogue quality using multiple heuristics.

    Craft rules:
    1. Vary attribution: not every line should end with 'he said'
    2. Avoid adverb-heavy tags: 'she said angrily' is telling, not showing
    3. Dialogue should sound spoken, not written
    4. No 'information dump' dialogue — characters explaining things
       they both already know for the reader's benefit
    """
    # Extract dialogue lines (text between quotes)
    dialogue_pattern = re.compile(r'["\u201c](.*?)["\u201d]', re.DOTALL)
    dialogue_lines = dialogue_pattern.findall(text)

    if not dialogue_lines:
        return ValidationResult(
            check_name="dialogue_authenticity",
            passed=True,
            score=0.5,  # Neutral — no dialogue to evaluate
            details="No dialogue found in this chapter.",
            severity="suggestion",
        )

    issues = []

    # Check 1: Attribution tag variety
    said_pattern = re.compile(
        r'(said|asked|replied|responded|answered|stated|exclaimed|declared)',
        re.IGNORECASE,
    )
    attribution_tags = said_pattern.findall(text)
    if attribution_tags:
        tag_counter = Counter(t.lower() for t in attribution_tags)
        most_common_tag, most_common_count = tag_counter.most_common(1)[0]
        if most_common_count / len(attribution_tags) > 0.7:
            issues.append(
                f"Attribution monotony: '{most_common_tag}' used "
                f"{most_common_count}/{len(attribution_tags)} times. "
                f"Vary tags or use action beats instead."
            )

    # Check 2: Adverb-laden tags ("said angrily", "whispered softly")
    adverb_tag_pattern = re.compile(
        r'\b(said|asked|replied|whispered|shouted|murmured)\s+\w+ly\b',
        re.IGNORECASE,
    )
    adverb_tags = adverb_tag_pattern.findall(text)
    if len(adverb_tags) > 2:
        issues.append(
            f"Found {len(adverb_tags)} adverb-laden dialogue tags. "
            f"'Said angrily' tells the reader what to feel. "
            f"Show the anger through the words or action instead."
        )

    # Check 3: Average dialogue line length
    avg_dialogue_len = statistics.mean(len(line.split()) for line in dialogue_lines)
    if avg_dialogue_len > 40:
        issues.append(
            f"Average dialogue length: {avg_dialogue_len:.0f} words. "
            f"Real speech rarely exceeds 30 words per turn. "
            f"Check for 'speech-ifying' or information dumps."
        )

    # Check 4: Contractions (real speech uses them)
    total_dialogue_text = " ".join(dialogue_lines)
    contraction_pattern = re.compile(r"\b\w+'(t|s|re|ve|ll|d|m)\b")
    contractions = contraction_pattern.findall(total_dialogue_text)
    dialogue_word_count = len(total_dialogue_text.split())
    contraction_rate = len(contractions) / max(dialogue_word_count, 1) * 100
    if contraction_rate < 2 and dialogue_word_count > 50:
        issues.append(
            f"Contraction rate in dialogue: {contraction_rate:.1f}%. "
            f"Natural speech uses contractions frequently. "
            f"Absence makes dialogue sound stilted."
        )

    passed = len(issues) <= 1  # Allow one minor issue
    score = max(0, 1.0 - len(issues) * 0.2)

    return ValidationResult(
        check_name="dialogue_authenticity",
        passed=passed,
        score=score,
        details=(
            f"Analyzed {len(dialogue_lines)} dialogue lines. "
            + (" ".join(issues) if issues else "Dialogue sounds natural.")
        ),
        locations=issues,
        severity="warning" if len(issues) > 1 else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 6: Sentence Variety
# ──────────────────────────────────────────────
# Craft principle: Vary sentence length. Short sentences
# create punch. Long sentences create flow. Monotonous
# length creates boredom.

def check_sentence_variety(text: str, voice_guide: dict | None = None) -> ValidationResult:
    """
    Analyze sentence length distribution.

    Craft rule: Standard deviation of sentence length should be
    at least 5 words. Professional prose oscillates between
    short, punchy sentences (3-8 words) and longer, flowing ones
    (20-35 words). A chapter with uniform 15-word sentences
    reads like a textbook.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 5:
        return ValidationResult(
            check_name="sentence_variety",
            passed=True,
            score=0.5,
            details="Too few sentences to analyze.",
            severity="suggestion",
        )

    lengths = [len(s.split()) for s in sentences]
    avg_length = statistics.mean(lengths)
    std_dev = statistics.stdev(lengths)
    min_length = min(lengths)
    max_length = max(lengths)

    # Check against voice guide if provided
    target_avg = None
    if voice_guide:
        target_avg = voice_guide.get("sentence_length", {}).get("average_words")

    issues = []

    if std_dev < 5:
        issues.append(
            f"Sentence length std dev: {std_dev:.1f} (target: >= 5). "
            f"Sentences are too uniform. Mix short punchy sentences "
            f"with longer flowing ones."
        )

    if min_length > 8:
        issues.append(
            f"Shortest sentence is {min_length} words. "
            f"Include some very short sentences (3-6 words) for impact."
        )

    if max_length < 20:
        issues.append(
            f"Longest sentence is {max_length} words. "
            f"Include some longer, flowing sentences (25-35 words) "
            f"for immersive passages."
        )

    if target_avg and abs(avg_length - target_avg) > 3:
        issues.append(
            f"Average sentence length: {avg_length:.1f} words. "
            f"Voice guide target: {target_avg} words. "
            f"Deviation of {abs(avg_length - target_avg):.1f} words "
            f"suggests voice drift."
        )

    passed = std_dev >= 5 and len(issues) <= 1
    score = min(std_dev / 10, 1.0)

    return ValidationResult(
        check_name="sentence_variety",
        passed=passed,
        score=score,
        details=(
            f"Sentences: {len(sentences)}, "
            f"avg length: {avg_length:.1f}, "
            f"std dev: {std_dev:.1f}, "
            f"range: [{min_length}, {max_length}]"
        ),
        locations=issues,
        severity="warning" if not passed else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 7: Forbidden Word Detector
# ──────────────────────────────────────────────
# Craft principle: Every voice has words it would never use.
# The voice guide contains a forbidden_words list. Any
# occurrence breaks voice fidelity.

def check_forbidden_words(
    text: str,
    forbidden_words: list[str],
) -> ValidationResult:
    """
    Detect words from the voice guide's forbidden list.

    The story bible's voice_guide.forbidden_words contains words
    the subject would never use. Their presence breaks the illusion
    that the subject wrote this themselves.
    """
    if not forbidden_words:
        return ValidationResult(
            check_name="forbidden_words",
            passed=True,
            score=1.0,
            details="No forbidden words defined in voice guide.",
            severity="suggestion",
        )

    violations = []
    text_lower = text.lower()

    for word in forbidden_words:
        pattern = re.compile(r'\b' + re.escape(word.lower()) + r'\b')
        matches = list(pattern.finditer(text_lower))
        if matches:
            # Find the sentences containing the violation
            for match in matches:
                start = max(0, text_lower.rfind('.', 0, match.start()) + 1)
                end = text_lower.find('.', match.end())
                if end == -1:
                    end = min(len(text_lower), match.end() + 80)
                context = text[start:end].strip()
                violations.append(
                    f"'{word}' found: '...{context[:100]}...'"
                )

    passed = len(violations) == 0
    score = max(0, 1.0 - len(violations) * 0.2)

    return ValidationResult(
        check_name="forbidden_words",
        passed=passed,
        score=score,
        details=(
            f"Checked {len(forbidden_words)} forbidden words. "
            f"Found {len(violations)} violations."
        ),
        locations=violations,
        severity="critical" if violations else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 8: Cliche Detector
# ──────────────────────────────────────────────
# Craft principle: Cliches are the enemy of memoir.
# They substitute pre-packaged language for authentic
# observation. Every cliche is a missed opportunity
# to see the world through the subject's unique eyes.

CLICHES = [
    "little did .{0,10} know",
    "everything changed",
    "nothing would ever be the same",
    "it was a dark and stormy",
    "at the end of the day",
    "only time would tell",
    "a roller coaster of emotions",
    "the best of times.{0,30}worst of times",
    "a turning point in .{0,10} life",
    "words cannot describe",
    "beyond .{0,10} wildest dreams",
    "a weight .{0,20} lifted",
    "light at the end of the tunnel",
    "defining moment",
    "against all odds",
    "a new chapter",
    "chapter of .{0,10} life",
    "bittersweet",
    "heart of gold",
    "the apple doesn.t fall far",
    "blood is thicker than water",
    "everything happens for a reason",
    "time heals all wounds",
    "what doesn.t kill .{0,10} makes .{0,10} stronger",
    "when one door closes",
    "tip of the iceberg",
    "in the blink of an eye",
    "stood the test of time",
    "a breath of fresh air",
    "crystal clear",
]


def check_cliches(text: str) -> ValidationResult:
    """
    Detect cliched phrases that undermine authentic voice.

    Every cliche found is a location where the chapter writer
    should replace packaged language with original observation
    rooted in the subject's actual experience.
    """
    violations = []

    for cliche_pattern in CLICHES:
        pattern = re.compile(cliche_pattern, re.IGNORECASE)
        matches = list(pattern.finditer(text))
        for match in matches:
            context_start = max(0, match.start() - 30)
            context_end = min(len(text), match.end() + 30)
            context = text[context_start:context_end].strip()
            violations.append(f"Cliche: '...{context}...'")

    passed = len(violations) == 0
    score = max(0, 1.0 - len(violations) * 0.15)

    return ValidationResult(
        check_name="cliche_detector",
        passed=passed,
        score=score,
        details=(
            f"Scanned for {len(CLICHES)} known cliche patterns. "
            f"Found {len(violations)}."
        ),
        locations=violations,
        severity="warning" if violations else "suggestion",
    )


# ──────────────────────────────────────────────
# Check 9: Passive Voice Percentage
# ──────────────────────────────────────────────

def check_passive_voice(text: str) -> ValidationResult:
    """
    Estimate passive voice usage.

    Craft rule: Memoir should be predominantly active voice.
    Passive voice above 15% signals weak, distanced prose.
    Exception: reflective sections may legitimately use more
    passive constructions.
    """
    passive_pattern = re.compile(
        r'\b(was|were|been|being|is|are|am)\s+'
        r'(\w+ed|(\w+en))\b',
        re.IGNORECASE,
    )

    sentences = _split_sentences(text)
    passive_sentences = []

    for i, sent in enumerate(sentences, 1):
        if passive_pattern.search(sent):
            passive_sentences.append(f"Sentence {i}: '{sent[:80]}...'")

    total = len(sentences)
    passive_count = len(passive_sentences)
    passive_pct = (passive_count / total * 100) if total > 0 else 0

    passed = passive_pct <= 15
    score = max(0, 1.0 - (passive_pct - 10) / 20) if passive_pct > 10 else 1.0

    return ValidationResult(
        check_name="passive_voice_percentage",
        passed=passed,
        score=score,
        details=(
            f"Passive voice: {passive_pct:.1f}% "
            f"({passive_count}/{total} sentences). "
            f"Target: <= 15%."
        ),
        locations=passive_sentences[:5],
        severity="warning" if not passed else "suggestion",
    )


# ──────────────────────────────────────────────
# Orchestrator: Run All Checks
# ──────────────────────────────────────────────

def validate_chapter(
    prose_text: str,
    voice_guide: dict | None = None,
    sections: list[dict] | None = None,
    chapter_number: int = 0,
) -> ChapterValidation:
    """
    Run all editorial validation checks on a chapter draft.

    Args:
        prose_text: The full chapter prose as a string
        voice_guide: Voice guide dict from story_bible.voice_guide
        sections: Section list from chapter_draft.structure.sections
        chapter_number: Chapter number for reporting

    Returns:
        ChapterValidation with results from all checks
    """
    forbidden = []
    if voice_guide:
        forbidden = voice_guide.get("forbidden_words", [])

    results = [
        check_show_vs_tell(prose_text),
        check_sensory_detail(prose_text),
        check_dialogue_authenticity(prose_text),
        check_sentence_variety(prose_text, voice_guide),
        check_forbidden_words(prose_text, forbidden),
        check_cliches(prose_text),
        check_passive_voice(prose_text),
    ]

    if sections:
        results.append(check_pacing(prose_text, sections))
        results.append(check_emotional_arc(prose_text, sections))

    word_count = len(re.findall(r'\b\w+\b', prose_text))
    overall = statistics.mean(r.score for r in results)

    return ChapterValidation(
        chapter_number=chapter_number,
        word_count=word_count,
        results=results,
        overall_score=overall,
    )


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling common abbreviations."""
    # Simple sentence splitter — production should use spaCy or similar
    text = re.sub(r'(Mr|Mrs|Ms|Dr|Prof|Jr|Sr|vs|etc|i\.e|e\.g)\.',
                  r'\1<DOT>', text)
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]
    return sentences
```

### Integration with Existing Pipeline

The validators above produce `ValidationResult` objects that map directly to existing schemas:

| Validator | `chapter_draft.voice_metrics` field | `review_verdict.issues[]` category |
|-----------|------------------------------------|------------------------------------|
| `check_show_vs_tell` | `show_vs_tell_ratio` | `style-issue` |
| `check_pacing` | (new: `pacing_score`) | `pacing-issue` |
| `check_emotional_arc` | (new: `emotional_arc_range`) | `pacing-issue` |
| `check_sensory_detail` | (new: `sensory_density_per_1k`) | `style-issue` |
| `check_dialogue_authenticity` | `dialogue_ratio` (enriched) | `voice-deviation` |
| `check_sentence_variety` | `avg_sentence_length`, `sentence_length_std` | `voice-deviation` |
| `check_forbidden_words` | `forbidden_word_violations` | `voice-deviation` |
| `check_cliches` | (new: `cliche_count`) | `style-issue` |
| `check_passive_voice` | `passive_voice_pct` | `style-issue` |

---

## 5. Ghostwriter Workflow → Pipeline Design

### The Traditional Process

Professional ghostwriting follows a consistent 7-phase process refined over decades. The total engagement typically spans 4-12 months with 20-40 hours of interviews.

### Phase-by-Phase Translation

```
TRADITIONAL GHOSTWRITING              AI AUTOBIOGRAPHY PIPELINE
─────────────────────────────────────────────────────────────────────

Phase 1: INITIAL CONSULTATION         Step 1: PROJECT INTAKE
─────────────────────────              ────────────────────────
- 1-2 hour meeting                    - User provides initial prompt
- Understand subject's goals          - Agent asks 4 scoping questions:
- Define scope and audience             1. "Who is the subject?"
- Set expectations                      2. "What time period to cover?"
                                        3. "Who is the intended reader?"
                                        4. "What is the book's purpose?"
                                      - Output: state.yaml initialized
                                      - Agent: Orchestrator
                                      ─────────────────────────────────

Phase 2: DEEP INTERVIEWS              Steps 2-5: INTERVIEW SESSIONS
──────────────────────                 ─────────────────────────────
- 15-30 hours across 10-20 sessions   - 4+ sessions covering McAdams domains:
- Record everything                     Session 1: Life Chapters (LC-01~05)
- Chronological sweep + thematic        Session 2: Key Scenes (KS-01~08)
  deep dives                            Session 3: Significant People (SP-01~06)
- Follow emotional energy               Session 4: Future + Ideology
- Extract direct quotes                   (FS-01~04, PI-01~07)
- Note speech patterns                 - Each session produces INT-xxx.json
- Research historical context          - Kvale types guide conversation flow
                                      - Agent: @interviewer
                                      ─────────────────────────────────

Phase 3: OUTLINE CREATION             Step 6: STORY BIBLE CREATION
─────────────────────────              ─────────────────────────────
- Organize raw material chronologically - Ingest all INT-xxx transcripts
- Identify narrative arc               - Build timeline, character registry
- Propose chapter structure             - Identify themes and arcs
- Subject approves structure            - Construct chapter plan with:
                                          - Beat sheet per chapter
                                          - Event/character/theme mapping
                                          - Voice guide from speech patterns
                                        - Output: story_bible.json
                                        - Agent: @story-architect
                                      ─────────────────────────────────

Phase 4: FIRST DRAFT                  Steps 7-N: CHAPTER DRAFTING
────────────────────                   ──────────────────────────
- Write one chapter at a time          - For each chapter in chapter_plan[]:
- Match subject's voice                  1. Assemble context package
- Convert interviews to scenes           2. Write prose following beat sheet
- Balance scene and summary              3. Run editorial validators
- Maintain chronological/thematic        4. Generate metadata JSON
  consistency                            5. Self-assess (pACS score)
- Target 60,000-80,000 words           - Each chapter: ch{NN}_draft_v1.md
                                        - Agent: @chapter-writer
                                      ─────────────────────────────────

Phase 5: SUBJECT REVIEW               Steps N+1: ADVERSARIAL REVIEW
────────────────────                   ─────────────────────────────
- Subject reads each chapter           - @reviewer runs pre-mortem:
- Corrects factual errors                "What is most likely wrong?"
- Adjusts voice ("I wouldn't say it    - Checks against story bible SOT
  that way")                           - Runs editorial validators
- Identifies missing stories or        - Produces review_verdict.json
  people                                 with issues[], pacs scores
- Approves or requests changes         - FAIL → revision cycle
                                        - PASS → advance pipeline
                                      ─────────────────────────────────

Phase 6: REVISION CYCLES              Steps N+2: REVISION LOOP
────────────────────────               ──────────────────────────
- 2-4 revision passes                 - @chapter-writer receives:
- Address all feedback                   review_verdict.json
- Tighten prose                        - Addresses all critical issues
- Check for consistency                - Increments draft_version
- Verify all names, dates, places      - Re-runs editorial validators
- Professional copyedit                - Resubmits for re-review
                                       - Max 3 revision cycles per chapter
                                         (bounded retry per ULW I-3)
                                      ─────────────────────────────────

Phase 7: FINAL POLISH                 Step Final: MANUSCRIPT ASSEMBLY
──────────────────────                 ──────────────────────────────
- Professional proofread               - Concatenate all approved chapters
- Format for publication               - Cross-chapter consistency check:
- Create front/back matter               * Character name consistency
- Subject final sign-off                  * Timeline continuity
                                          * Theme arc completion
                                        - Generate final manuscript.md
                                        - Run full-manuscript validation
                                        - Output: outputs/builds/
                                      ─────────────────────────────────
```

### Interview Time Compression

Traditional ghostwriting requires 20-40 hours of in-person interviews. The AI pipeline compresses this through structured prompting:

```
TRADITIONAL                          AI PIPELINE
─────────────────────────────────────────────────────────────
40 hours × 1 subject × 1 interviewer   4 sessions × ~40 questions each
= 40 hours of raw recording            = ~160 structured exchanges

Recording → Transcription (8-16 hrs)   Questions are structured to extract
Transcription → Notes (4-8 hrs)        the same information McAdams gets
Notes → Outline (8-16 hrs)             in longitudinal studies.
────────────────────────                ─────────────────────────────────
Total: 60-80 hours of work             Schema-compliant output eliminates
                                       transcription and note-taking phases.

                                       The Kvale conversation flow code
                                       ensures depth equivalent to a
                                       skilled human interviewer's probing.
```

### State Machine for Pipeline Steps

```
┌──────────────┐
│ PROJECT      │ state.yaml created
│ INTAKE       │ scoping questions answered
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ INTERVIEW    │ INT-001.json ... INT-004.json
│ SESSIONS     │ (4+ sessions, McAdams domains)
│ (loop)       │
└──────┬───────┘
       │ all sessions complete
       ▼
┌──────────────┐
│ STORY BIBLE  │ story_bible.json
│ CREATION     │ (timeline + characters + themes + plan)
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ CHAPTER      │────▶│ EDITORIAL    │
│ DRAFTING     │     │ VALIDATION   │
│ (per chapter)│◀────│ (automated)  │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ ADVERSARIAL  │────▶│ REVISION     │ ◀── max 3 cycles
│ REVIEW       │     │ LOOP         │
│ (@reviewer)  │◀────│              │
└──────┬───────┘     └──────────────┘
       │ PASS
       ▼
┌──────────────┐
│ MANUSCRIPT   │ Full book assembled
│ ASSEMBLY     │ Cross-chapter validation
└──────────────┘
```

---

## 6. Voice Capture Techniques → Prompt Code

### Theoretical Foundation

Professional ghostwriters identify six dimensions of a subject's voice: vocabulary level, sentence rhythm, favorite expressions, humor style, emotional register, and "the negative space" (what they would never say). These dimensions are captured during interviews and codified in the voice guide. The `@chapter-writer` agent then uses the voice guide as a binding constraint.

### Voice Analysis Prompt

The following prompt is executed by the `@story-architect` agent after ingesting all interview transcripts. It produces the `voice_guide` section of `story_bible.schema.json`.

```yaml
# voice_analysis.prompt.yaml
# Executed by: @story-architect
# Input: All interview transcripts (INT-001 through INT-N)
# Output: story_bible.voice_guide section

system: >
  You are a professional ghostwriter analyzing interview transcripts
  to create a comprehensive voice guide. Your job is to listen to
  HOW the subject speaks, not just WHAT they say. You are building
  a blueprint that another writer will use to reproduce this person's
  voice in prose.

instructions:
  step_1_vocabulary_analysis:
    prompt: >
      Read through all key_quotes across all interview transcripts.
      Analyze the subject's vocabulary:

      1. VOCABULARY LEVEL: Is their language colloquial, educated,
         academic, or a mix? Do they use jargon from their profession?
         Do they code-switch between registers?

      2. WORD FREQUENCY: What words appear unusually often in their
         speech? Not common words like 'the' or 'is' — words that
         reveal personality. Do they say 'absolutely' instead of 'yes'?
         'Folks' instead of 'people'? 'Basically' as a filler?

      3. AVOIDANCE: What words do they NEVER use? If every transcript
         avoids profanity, that's a signal. If they never say 'love'
         but say 'care about' — that's voice.

    output_fields:
      - voice_guide.sentence_length.average_words
      - voice_guide.forbidden_words[]
      - subject.speech_patterns.vocabulary_level
      - subject.speech_patterns.favorite_expressions[]

  step_2_rhythm_analysis:
    prompt: >
      Analyze sentence structure in the key_quotes:

      1. SENTENCE LENGTH: Calculate the average word count per sentence.
         Note the range — do they alternate between short punchy
         statements and long flowing ones, or are they consistently
         medium-length?

      2. PARAGRAPH RHYTHM: When they tell a story, do they build
         to a climax and then drop to a short sentence? Do they
         start with the punchline and then explain? Do they use
         repetition for emphasis?

      3. VERBAL TICS: Do they start sentences with 'Well,' or 'So,'
         or 'You know,'? Do they use hedges ('kind of', 'sort of',
         'I think')? These tics, used sparingly in prose, create
         authenticity.

    output_fields:
      - voice_guide.sentence_length.average_words
      - voice_guide.sentence_length.max_words
      - voice_guide.sentence_length.variation_note
      - voice_guide.preferred_constructions[]

  step_3_emotional_register:
    prompt: >
      Analyze how the subject expresses emotion:

      1. DIRECT vs INDIRECT: Do they name emotions ('I was angry')
         or describe them through action ('I slammed the door')?
         If they are indirect, the chapter writer must NEVER have
         them say 'I felt sad' — it would break voice.

      2. HUMOR: What kind of humor do they use? Self-deprecating?
         Dry? Sarcastic? Folksy? Do they use humor to deflect from
         difficult topics? Does the humor mask something?

      3. EMOTIONAL TEMPERATURE: Are they generally warm or reserved?
         Do they use superlatives ('the greatest', 'the worst')
         or understate ('it was tough', 'not ideal')?

      4. STORYTELLING STYLE: When they tell a story, do they build
         suspense or give away the ending first? Do they include
         details or stick to the big picture?

    output_fields:
      - subject.speech_patterns.humor_style
      - voice_guide.show_dont_tell_requirements[]

  step_4_sample_sentences:
    prompt: >
      From all interview transcripts, select 10-15 sentences that
      best capture this person's authentic voice. Choose sentences
      that are:

      1. CHARACTERISTIC: They sound like this person and no one else
      2. VARIED: Show different emotional registers
      3. USABLE: The chapter writer can use them as calibration —
         "Does my prose sound like it could sit next to these sentences?"

      For each sentence, note WHY it captures their voice.

    output_fields:
      - subject.speech_patterns.sample_sentences[]

  step_5_forbidden_constructions:
    prompt: >
      Based on your analysis, create two lists:

      FORBIDDEN (the subject would NEVER say these):
      - Words outside their vocabulary level
      - Emotional expressions inconsistent with their register
      - Sentence constructions they never use
      - Cliches they would find inauthentic

      PREFERRED (constructions that feel like them):
      - Their typical sentence openers
      - Their way of introducing quotes or dialogue
      - Their approach to transitions between topics
      - Their characteristic way of ending a thought

    output_fields:
      - voice_guide.forbidden_words[]
      - voice_guide.preferred_constructions[]
```

### The "Read It Aloud" Test as Validation Code

Professional ghostwriters use one decisive test: read the prose aloud. If a sentence doesn't sound like it could come out of the subject's mouth, rewrite it. In the AI pipeline, this becomes a validation step.

```python
"""
voice_fidelity_validator.py — The 'Read It Aloud' Test

Translates the ghostwriter's ear into computable metrics.
Compares prose against the voice guide to detect voice drift.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass


@dataclass
class VoiceFidelityResult:
    """Result of the voice fidelity check."""
    overall_score: float  # 0.0 to 1.0
    sentence_length_match: float
    vocabulary_match: float
    forbidden_word_violations: int
    preferred_construction_usage: float
    sample_sentence_similarity: float
    details: str
    recommendations: list[str]


def validate_voice_fidelity(
    prose: str,
    voice_guide: dict,
    sample_sentences: list[str],
) -> VoiceFidelityResult:
    """
    Compare generated prose against the voice guide.

    This is the computational equivalent of the ghostwriter's
    'read it aloud' test. It checks:

    1. Does the sentence length distribution match the subject's?
    2. Does the vocabulary stay within the subject's register?
    3. Are forbidden words absent?
    4. Are preferred constructions present?
    5. Does the prose 'feel' like the sample sentences?
    """
    recommendations = []

    # ── Check 1: Sentence Length Match ──
    sentences = _split_sentences(prose)
    prose_lengths = [len(s.split()) for s in sentences]
    prose_avg = statistics.mean(prose_lengths) if prose_lengths else 15

    target_avg = voice_guide.get("sentence_length", {}).get("average_words", 15)
    target_max = voice_guide.get("sentence_length", {}).get("max_words", 40)

    length_deviation = abs(prose_avg - target_avg) / target_avg
    length_score = max(0, 1.0 - length_deviation)

    if length_deviation > 0.2:
        recommendations.append(
            f"Sentence length avg is {prose_avg:.1f} words, "
            f"target is {target_avg}. {'Shorten' if prose_avg > target_avg else 'Lengthen'} "
            f"sentences to match the subject's natural rhythm."
        )

    over_max = sum(1 for l in prose_lengths if l > target_max)
    if over_max > 0:
        recommendations.append(
            f"{over_max} sentences exceed the voice guide maximum of "
            f"{target_max} words. Break them up."
        )

    # ── Check 2: Vocabulary Match ──
    prose_words = set(re.findall(r'\b\w+\b', prose.lower()))

    # Check vocabulary level alignment
    vocab_level = voice_guide.get("vocabulary_level", "educated")
    academic_markers = {"furthermore", "nevertheless", "paradigm", "discourse",
                        "methodology", "conceptualize", "juxtapose", "hegemony"}
    colloquial_markers = {"gonna", "wanna", "kinda", "gotta", "yeah", "nah",
                          "dude", "stuff", "cool", "awesome", "basically"}

    academic_count = len(prose_words & academic_markers)
    colloquial_count = len(prose_words & colloquial_markers)

    if vocab_level == "colloquial" and academic_count > 2:
        recommendations.append(
            f"Subject speaks colloquially but prose uses {academic_count} "
            f"academic terms: {prose_words & academic_markers}. "
            f"Replace with simpler words."
        )
        vocab_score = max(0, 1.0 - academic_count * 0.15)
    elif vocab_level == "academic" and colloquial_count > 2:
        recommendations.append(
            f"Subject speaks formally but prose uses {colloquial_count} "
            f"colloquial terms: {prose_words & colloquial_markers}."
        )
        vocab_score = max(0, 1.0 - colloquial_count * 0.15)
    else:
        vocab_score = 1.0

    # ── Check 3: Forbidden Words ──
    forbidden = voice_guide.get("forbidden_words", [])
    violations = 0
    for word in forbidden:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        count = len(pattern.findall(prose))
        if count > 0:
            violations += count
            recommendations.append(
                f"Forbidden word '{word}' appears {count} time(s). "
                f"The subject would never say this. Replace it."
            )

    forbidden_score = max(0, 1.0 - violations * 0.25)

    # ── Check 4: Preferred Constructions ──
    preferred = voice_guide.get("preferred_constructions", [])
    preferred_found = 0
    for construction in preferred:
        pattern = re.compile(re.escape(construction), re.IGNORECASE)
        if pattern.search(prose):
            preferred_found += 1

    preferred_score = preferred_found / max(len(preferred), 1)
    if preferred_score < 0.3 and preferred:
        recommendations.append(
            f"Only {preferred_found}/{len(preferred)} preferred constructions "
            f"detected. Incorporate more of the subject's natural phrasing: "
            f"{preferred[:3]}"
        )

    # ── Check 5: Sample Sentence Similarity ──
    # Compare prose sentence length distribution and word choice
    # to the sample sentences from the voice guide
    if sample_sentences:
        sample_lengths = [len(s.split()) for s in sample_sentences]
        sample_avg = statistics.mean(sample_lengths)
        sample_words = set()
        for s in sample_sentences:
            sample_words.update(re.findall(r'\b\w+\b', s.lower()))

        # Sentence length similarity
        length_sim = max(0, 1.0 - abs(prose_avg - sample_avg) / sample_avg)

        # Word overlap (Jaccard-like, but only on distinctive words)
        common_words = {"the", "a", "an", "is", "was", "were", "are", "be",
                        "to", "of", "and", "in", "that", "it", "for", "on",
                        "with", "as", "at", "by", "this", "from", "or", "but",
                        "not", "have", "had", "has", "my", "i", "me", "we",
                        "you", "he", "she", "they", "their", "his", "her"}
        distinctive_sample = sample_words - common_words
        distinctive_prose = prose_words - common_words
        if distinctive_sample:
            overlap = len(distinctive_prose & distinctive_sample)
            similarity_score = overlap / len(distinctive_sample)
        else:
            similarity_score = 0.5

        sample_sim = (length_sim + similarity_score) / 2
    else:
        sample_sim = 0.5  # No samples to compare

    # ── Aggregate ──
    overall = statistics.mean([
        length_score,
        vocab_score,
        forbidden_score,
        preferred_score,
        sample_sim,
    ])

    return VoiceFidelityResult(
        overall_score=overall,
        sentence_length_match=length_score,
        vocabulary_match=vocab_score,
        forbidden_word_violations=violations,
        preferred_construction_usage=preferred_score,
        sample_sentence_similarity=sample_sim,
        details=(
            f"Voice fidelity: {overall:.0%}. "
            f"Sentence rhythm: {length_score:.0%}, "
            f"Vocabulary: {vocab_score:.0%}, "
            f"Forbidden: {forbidden_score:.0%}, "
            f"Preferred: {preferred_score:.0%}, "
            f"Sample match: {sample_sim:.0%}."
        ),
        recommendations=recommendations,
    )


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    text = re.sub(r'(Mr|Mrs|Ms|Dr|Prof|Jr|Sr|vs|etc|i\.e|e\.g)\.',
                  r'\1<DOT>', text)
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]
```

### Voice Capture During Interviews: The `@interviewer` Agent's Hidden Work

The `@interviewer` agent does more than collect stories. It covertly performs voice analysis on every response. Here is the prompt section that drives this:

```yaml
# Addition to @interviewer agent prompt:
# Voice Capture Protocol (runs silently during every exchange)

voice_capture_protocol:
  description: >
    While conducting the interview, you are simultaneously analyzing
    the subject's speech patterns. This analysis happens in the
    background and is recorded in the emotional_markers and key_quotes
    sections of the transcript. You do NOT mention this analysis to
    the subject.

  per_response_analysis:
    - sentence_length: "Count words per sentence in the response"
    - favorite_words: "Note any word used 3+ times that is not a common function word"
    - emotional_expression: "How do they express emotion — directly or through metaphor/action?"
    - humor_markers: "Note any humor — what type? Self-deprecating? Dry? Sarcastic?"
    - storytelling_pattern: "Do they build to the climax or start with the punchline?"
    - hedging: "Do they hedge ('kind of', 'maybe', 'I think') or speak with certainty?"
    - verbal_tics: "Note repeated filler phrases ('you know', 'basically', 'I mean')"

  capture_in_transcript:
    key_quotes:
      selection_criteria: >
        Select quotes that capture VOICE, not just content.
        A quote is voice-relevant if removing it would lose something
        about HOW the subject speaks, not just WHAT they said.
        Prioritize quotes with:
        1. Characteristic rhythm (short-long sentence pairs)
        2. Distinctive word choice
        3. Humor or emotional candor
        4. Speech patterns (hedges, tics, emphasis)

    emotional_markers:
      capture: >
        Record not just WHAT emotion was expressed but HOW:
        - "Subject expressed anger through understatement: 'That wasn't ideal.'"
        - "Subject deflected grief with humor: 'Well, that was a fun year.'"
        - "Subject's voice dropped when mentioning father — long pauses."
        These markers tell the @story-architect HOW to calibrate
        the voice guide's emotional register.
```

### The Distinction Between Subject's Voice and "Good Writing"

This is the deepest craft principle translated into code. Professional ghostwriters know that "good writing" and "authentic voice" are often in tension. The subject may speak in fragments, use incorrect grammar, repeat themselves, or favor simple words. The ghostwriter's job is not to improve the voice but to render it on the page faithfully while making it readable.

```yaml
# Voice fidelity rules for @chapter-writer agent
# These override general "good writing" principles

voice_fidelity_rules:
  rule_1_grammar:
    principle: >
      If the subject speaks ungrammatically in a characteristic way,
      preserve it in dialogue and moderate it in narration. Example:
      A subject who says "Me and my brother went..." — use this in
      dialogue, but narration can silently correct to "My brother and I."
    implementation: >
      In key_quotes marked as voice-characteristic, preserve exact
      grammar. In narration, follow standard grammar unless the voice
      guide's preferred_constructions explicitly include non-standard forms.

  rule_2_simplicity:
    principle: >
      If the subject uses simple vocabulary, do NOT upgrade it.
      "Happy" is not worse than "elated." "Sad" is not worse than
      "melancholic." The chapter writer's vocabulary must not exceed
      the subject's vocabulary_level in the voice guide.
    implementation: >
      Check voice_guide.sentence_length.average_words and
      subject.speech_patterns.vocabulary_level. If vocabulary_level
      is "colloquial," flag any sentence with a Flesch-Kincaid grade
      level above 10.

  rule_3_rhythm:
    principle: >
      The subject's sentence rhythm is not a starting point — it is
      the target. If the subject speaks in short, punchy sentences,
      do not "improve" them into flowing prose. Short sentences are
      not a deficiency.
    implementation: >
      voice_guide.sentence_length.average_words is a constraint,
      not a suggestion. The voice_fidelity_validator flags deviations
      above 20%.

  rule_4_the_negative_space:
    principle: >
      What the subject does NOT say is as important as what they do.
      If they never use profanity, never curse in the prose.
      If they never say "I love you" but show love through action,
      the prose must do the same. The forbidden_words list captures
      this negative space.
    implementation: >
      voice_guide.forbidden_words[] is an absolute constraint.
      Any violation is severity="critical" in the review verdict.
      voice_guide.show_dont_tell_requirements[] lists emotions that
      must be shown, never stated — derived from how the subject
      actually expresses those emotions in interviews.
```

---

## Summary: The Craft-to-Code Translation Map

| Craft Tradition | Source | Code Artifact | Location |
|----------------|--------|---------------|----------|
| McAdams Life Story Interview | LSI-II (2007) | 30 structured questions across 5 domains | `@interviewer` prompt enhancement |
| Kvale's 9 Question Types | *InterViews* (1996) | Prompt templates + selection state machine | Conversation flow code |
| Gornick's Situation/Story | *The Situation and the Story* | `content_type` enum + narrator persona rules | `chapter_draft.schema.json` |
| Scene vs Summary balance | Memoir craft consensus | `scene_vs_summary_ratio` validator | `editorial_validators.py` |
| Three-Act Structure | Aristotle via memoir adaptation | `overall_structure` + `chapter_beat_sheet` | `narrative_structure.schema.yaml` |
| Show Don't Tell | Universal craft principle | `check_show_vs_tell()` with word lists | `editorial_validators.py` |
| Voice Capture | Professional ghostwriting | Voice analysis prompt + `voice_fidelity_validator.py` | `@story-architect` + validation |
| Read It Aloud Test | Ghostwriter practice | `validate_voice_fidelity()` with 5 dimensions | `voice_fidelity_validator.py` |
| Oral History Association | OHA Best Practices (2022) | Informed consent + open-ended protocol | `@interviewer` prompt structure |
| Professional editing | Publishing editorial standards | 9 validation checks with scoring | `editorial_validators.py` |

---

## Sources

- [McAdams Life Story Interview II (2007) — Northwestern University](https://cpb-us-e1.wpmucdn.com/sites.northwestern.edu/dist/4/3901/files/2020/11/The-Life-Story-Interview-II-2007.pdf)
- [McAdams Life Story Interview — SWK Empower Lab](https://swkempowerlab.com/wp-content/uploads/2024/02/Life-Story-Interview.pdf)
- [Kvale's Semi-Structured Interview Question Types](http://public-media.interaction-design.org/pdf/Different-Types-of-Questions-Template.pdf)
- [Probing in Qualitative Research Interviews: Theory and Practice](https://www.tandfonline.com/doi/full/10.1080/14780887.2023.2238625)
- [Oral History Association — Best Practices](https://oralhistory.org/best-practices/)
- [OHA Principles and Best Practices (2022)](https://oralhistory.org/wp-content/uploads/2022/08/OHA-Principles-and-Best-Practice-Print-Version-Updated-2022.pdf)
- [Vivian Gornick — The Art of Memoir No. 2 (Paris Review)](https://www.theparisreview.org/interviews/6343/the-art-of-memoir-no-2-vivian-gornick)
- [Structure is Everything: Interview with Vivian Gornick (Brevity)](https://brevity.wordpress.com/2019/08/26/structure-gornick_1/)
- [How Vivian Gornick Distinguishes Situation from Story (The Marginalian)](https://www.themarginalian.org/2015/06/22/vivian-gornick-the-situation-and-the-story-personal-narrative/)
- [Three-Act Structure for Memoir (Strike the Write Tone)](https://www.strikethewritetone.com/post/three-act-structure-for-memoir-ensures-the-best-read)
- [How Ghostwriters Capture Authentic Voice (Erick Mertz)](https://erickmertzwriting.com/how-ghostwriters-capture-authentic-voice-professional-ghostwriting-tips/)
- [The Art of Voice Matching (Marcia Layton Turner)](https://marcialaytonturner.com/blog/for-aspiring-authors/the-art-of-voice-matching-how-professional-ghostwriters-capture-your-unique-perspective/)
- [My Ghostwriting Process (Laura Sherman)](https://laurasherman.com/my-ghostwriting-process-from-start-to-finish/)
- [How I Ghostwrite Books (Amy Suto)](https://www.amysuto.com/desk-of-amy-suto/my-process-how-i-ghostwrite-books-as-a-memoir-ghostwriter)
- [From Memory to Manuscript (The Writers For Hire)](https://www.thewritersforhire.com/how-a-memoir-ghostwriter-can-help-you-shape-your-memoir/)
- [Emotional Pacing in Trauma Memoir (Brevity)](https://brevitymag.com/craft-essays/emotional-pacing/)
- [Show Don't Tell in Memoir (Write My Memoirs)](https://writemymemoirs.com/examples-of-show-dont-tell-in-memoir/)
- [Show and Tell Balance in Memoir (Peacock Proud Press)](https://peacockproud.com/the-importance-of-show-and-tell-in-memoir/)
- [Crafting Compelling Memoir Structure (Mary Kole)](https://www.marykole.com/memoir-structure)
