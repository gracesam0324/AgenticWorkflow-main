# Privacy-Preserving Multi-Model Strategy

## Threat Model

The AI Autobiography Generator processes deeply personal life stories. The
pipeline uses three AI providers with different trust levels and data policies.
This document defines which data can be sent to which model, and how to enforce
those boundaries.

### Provider Trust Tiers

| Provider | Trust Level | Data Retention (Paid Tier) | Training on Data (Paid) | Our Tier |
|----------|------------|---------------------------|------------------------|----------|
| Claude (Anthropic) | HIGH | Not retained beyond session | No | Subscription |
| OpenAI | MEDIUM | 30-day retention for abuse monitoring | No (API) | Subscription |
| Gemini (Google) | MEDIUM | Logged for limited period, abuse monitoring | No (paid API) | Subscription |

**Critical distinction**: All three providers, when used via paid API tiers, do
NOT use submitted data for model training. However, all retain data temporarily
for abuse monitoring. The key difference is the *nature* of the data we send.

---

## Data Classification Matrix

### Classification Levels

- **L1-CONFIDENTIAL**: Raw personal data. Contains PII, private stories,
  identifiable information. ONLY Claude (primary orchestrator) processes this.
- **L2-INTERNAL**: Derived data with PII removed. Structural and stylistic
  analysis that does not contain identifying details.
- **L3-SHAREABLE**: Fully anonymized, structural, or technical data. No PII,
  no identifiable content. Safe for any provider.

### Data Routing Matrix

| Data Type | Classification | Claude | OpenAI | Gemini | Local Only |
|-----------|---------------|--------|--------|--------|------------|
| Raw interview transcripts | L1-CONFIDENTIAL | YES | NO | NO | backup |
| Story bible (full) | L1-CONFIDENTIAL | YES | NO | NO | backup |
| Subject's name and demographics | L1-CONFIDENTIAL | YES | NO | NO | backup |
| Direct quotes from subject | L1-CONFIDENTIAL | YES | NO | NO | -- |
| Character registry with real names | L1-CONFIDENTIAL | YES | NO | NO | -- |
| Chapter drafts (full text) | L1-CONFIDENTIAL | YES | NO | NO | backup |
| Fact registry | L1-CONFIDENTIAL | YES | NO | NO | -- |
| Anonymized prose excerpts (<500 words) | L2-INTERNAL | YES | YES | YES | -- |
| Voice profile (statistical metrics) | L2-INTERNAL | YES | YES | YES | -- |
| Style analysis request (anonymized) | L2-INTERNAL | YES | YES | YES | -- |
| Chapter structure outline (no names) | L2-INTERNAL | YES | YES | YES | -- |
| Sentence length distributions | L3-SHAREABLE | YES | YES | YES | -- |
| Readability scores | L3-SHAREABLE | YES | YES | YES | -- |
| Dialogue ratio metrics | L3-SHAREABLE | YES | YES | YES | -- |
| Word frequency analysis | L3-SHAREABLE | YES | YES | YES | -- |
| Schema validation results | L3-SHAREABLE | YES | YES | YES | -- |
| Build pipeline errors | L3-SHAREABLE | YES | YES | YES | -- |
| Template/CSS/LaTeX code | L3-SHAREABLE | YES | YES | YES | -- |

---

## Anonymization Protocol

Before sending any text to OpenAI or Gemini, apply these transformations:

### Step 1: Entity Replacement

Replace all named entities with deterministic tokens. The mapping is stored
locally and never sent to any provider.

```python
ENTITY_MAP = {
    "Park Jimin": "[SUBJECT]",
    "Park Jihoon": "[PERSON-A]",
    "Park Sangwoo": "[PERSON-B]",
    "Lee Eunji": "[PERSON-C]",
    "Kim Taehyung": "[PERSON-D]",
    "Busan": "[CITY-1]",
    "Seoul": "[CITY-2]",
    "Haeundae": "[DISTRICT-1]",
    "Yonsei University": "[UNIVERSITY-1]",
}
```

### Step 2: Date Generalization

Replace specific dates with relative references:
- "March 15, 1990" becomes "in their early childhood"
- "2008-2012" becomes "a four-year period in early adulthood"

### Step 3: Contextual Stripping

Remove or generalize details that could identify the subject:
- Specific job titles at named companies
- Exact addresses or neighborhoods
- Phone numbers, email addresses
- Unique biographical events that could be searched

### Step 4: Excerpt Length Limits

Never send more than 500 words of prose to external models. This prevents
reconstruction of the full narrative.

---

## Use Cases for Each Provider

### Claude (Primary — All Tasks)

Claude is the orchestrator and handles all pipeline stages directly:
- Interview conduction
- Story bible construction
- Chapter writing
- Quality review
- Consistency checking
- All tasks involving L1-CONFIDENTIAL data

### OpenAI (Supplementary — Style Analysis Only)

Used exclusively for L2/L3 data:
- **Comparative style analysis**: Send anonymized excerpts from two chapters to
  check voice consistency across the manuscript
- **Prose quality scoring**: Send anonymized passages for independent quality
  assessment (second opinion to Claude's self-review)
- **Genre benchmarking**: Compare anonymized excerpts against published memoir
  style patterns

### Gemini (Supplementary — Technical Analysis Only)

Used exclusively for L2/L3 data:
- **Structural analysis**: Analyze chapter outlines (anonymized) for pacing
  and narrative arc effectiveness
- **Readability optimization**: Send anonymized passages for reading level
  analysis and suggestions
- **Cross-validation**: Independent second opinion on style metrics where
  both OpenAI and Gemini agree = high confidence

### Local-Only Processing

Some operations never leave the machine:
- Raw file I/O (reading interviews, writing chapters)
- JSON Schema validation
- Deterministic text metrics (textstat, word counts)
- Git operations
- Build pipeline (Pandoc, XeLaTeX)
- Credential management

---

## Enforcement Mechanisms

### 1. Adapter Layer Enforcement

The `integration_adapters.py` module enforces data classification at the API
boundary. The `AIClient` interface is designed for anonymized data only.
Pipeline code that needs to send data to OpenAI/Gemini MUST use the adapter,
which applies anonymization automatically.

### 2. Pre-Send Validation

Before any external API call, the adapter runs a PII detection check:

```python
PII_PATTERNS = [
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Proper names (heuristic)
    r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone numbers
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{1,5}\s\w+\s(?:Street|St|Avenue|Ave|Road|Rd)\b",  # Street addresses
]
```

If PII patterns are detected in text destined for OpenAI or Gemini, the call
is blocked and an error is raised.

### 3. Audit Logging

Every external API call is logged locally (never sent externally):

```json
{
    "timestamp": "2026-03-17T14:30:00Z",
    "provider": "openai",
    "model": "gpt-4o",
    "data_classification": "L2-INTERNAL",
    "text_length_chars": 487,
    "pii_check_passed": true,
    "anonymization_applied": true,
    "purpose": "style_analysis",
    "tokens_used": {"prompt": 120, "completion": 450}
}
```

### 4. Cost Tracking

External API calls are metered to prevent unexpected charges:

| Provider | Budget Cap (per book) | Estimated Usage |
|----------|----------------------|-----------------|
| OpenAI | $5.00 | ~$1-2 for style analysis across 12 chapters |
| Gemini | $5.00 | ~$1-2 for structural analysis |
| Claude | Subscription | Primary usage (subscription covers) |

---

## Decision Tree: Should This Data Go External?

```
Is the data raw interview transcripts or story bible?
  YES -> Claude ONLY (L1-CONFIDENTIAL)
  NO  -> Continue

Does the data contain real names, dates, or locations?
  YES -> Anonymize first, then re-check
  NO  -> Continue

Is the data >500 words of prose?
  YES -> Truncate or split, then re-check
  NO  -> Continue

Is the task style/structural analysis (not content generation)?
  YES -> Safe for OpenAI/Gemini (L2-INTERNAL or L3-SHAREABLE)
  NO  -> Claude ONLY
```

---

## Gemini-Specific Warning

As of February 2026, Google API keys that previously had no AI access now
silently authenticate to Gemini endpoints when the Generative Language API is
enabled on a GCP project. If you use the same GCP project for other services:

1. **Create a dedicated API key** for Gemini, restricted to the Generative
   Language API only
2. **Apply API restrictions** in Google Cloud Console
3. **Do not reuse** keys from other Google services

See: [Google API Keys Security Risk](https://simonwillison.net/2026/Feb/26/google-api-keys/)

---

## Sources

- [Gemini API Terms of Service](https://ai.google.dev/gemini-api/terms)
- [Gemini API & Data Privacy (2025)](https://redact.dev/blog/gemini-api-terms-2025)
- [Gemini Abuse Monitoring](https://ai.google.dev/gemini-api/docs/usage-policies)
- [LLM Data Privacy: Protecting Enterprise Data](https://www.lasso.security/blog/llm-data-privacy)
- [Privacy-Preserving Techniques in Generative AI (MDPI)](https://www.mdpi.com/2078-2489/15/11/697)
- [Privacy Considerations for LLMs (Frontiers)](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2025.1600750/full)
- [Building LLMs with Sensitive Data (Sigma AI)](https://sigma.ai/llm-privacy-security-phi-pii-best-practices/)
- [Vertex AI Zero Data Retention](https://cloud.google.com/vertex-ai/generative-ai/docs/data-governance)
