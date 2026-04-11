# Quality Gates — Church Retreat App

> Complete definitions for Q1-Q11 technical gates, D1-D9 design gates, and T1-T3 translation gates.
> Each gate includes pass criteria, verification script, and failure action.

---

## Technical Quality Gates (Q1-Q11)

### Q1 — Server Running
| Field | Value |
|-------|-------|
| **Pass Criteria** | HTTP 200 from `localhost:PORT` |
| **Script** | `validate_gates.py` → `Q1` |
| **Method** | `HTTP GET localhost:PORT → response.status_code == 200` |
| **On Failure** | Port change + retry |
| **Hallucination Risk** | H-CRITICAL |

### Q2 — HTML Validity
| Field | Value |
|-------|-------|
| **Pass Criteria** | No render-blocking errors |
| **Script** | `validate_gates.py` → `Q2` |
| **Method** | Parse HTML with `html.parser` → error list → `len == 0` |
| **On Failure** | Auto-fix + recheck |
| **Hallucination Risk** | H-CRITICAL |

### Q3 — External Dependencies
| Field | Value |
|-------|-------|
| **Pass Criteria** | 0 external scripts (except CDN font) |
| **Script** | `validate_gates.py` → `Q3` |
| **Method** | Regex `<script[^>]+src=["']https?://` on all `.html` files → count == 0 |
| **On Failure** | Inline or remove |
| **Hallucination Risk** | H-CRITICAL |

### Q4 — Bundle Size
| Field | Value |
|-------|-------|
| **Pass Criteria** | ≤ 300KB target / ≤ 500KB hard limit |
| **Script** | `validate_gates.py` → `Q4` |
| **Method** | `sum(os.path.getsize(f) for f in project_files)` → bytes ≤ 512000 |
| **On Failure** | Image compression → code splitting → feature reduction |
| **Hallucination Risk** | H-CRITICAL |

### Q5 — Korean Rendering
| Field | Value |
|-------|-------|
| **Pass Criteria** | No broken text in titles/buttons/menus |
| **Script** | `validate_gates.py` → `Q5` |
| **Method** | Scan `.html` for `\uFFFD` (replacement char) → 0 found AND Korean chars `[\uAC00-\uD7AF]` > 0 |
| **On Failure** | Add font fallback |
| **Hallucination Risk** | H-CRITICAL |

### Q6 — Touch Targets
| Field | Value |
|-------|-------|
| **Pass Criteria** | All buttons/links ≥ 44x44px |
| **Script** | `validate_gates.py` → `Q6` |
| **Method** | Parse CSS for min-height/min-width/padding on button/a/[role=button] → effective size ≥ 44px |
| **On Failure** | Auto-add min-height/width/padding |
| **Hallucination Risk** | H-CRITICAL |

### Q7 — QR Code
| Field | Value |
|-------|-------|
| **Pass Criteria** | QR decodes to correct URL |
| **Script** | `validate_gates.py` → `Q7` |
| **Method** | Decode QR PNG → compare URL string to expected |
| **On Failure** | Regenerate QR |
| **Hallucination Risk** | H-CRITICAL |

### Q8 — Admin Protection
| Field | Value |
|-------|-------|
| **Pass Criteria** | `/admin` requires password |
| **Script** | `validate_gates.py` → `Q8` |
| **Method** | HTTP GET `/admin` without auth → status_code == 401 |
| **On Failure** | Add auth middleware |
| **Hallucination Risk** | H-CRITICAL |

### Q9 — XSS Prevention
| Field | Value |
|-------|-------|
| **Pass Criteria** | `<script>` in user input neutralized |
| **Script** | `validate_gates.py` → `Q9` |
| **Method** | HTTP POST `<script>alert(1)</script>` → response body does NOT contain unescaped `<script>` |
| **On Failure** | Add escape function |
| **Hallucination Risk** | H-CRITICAL |

### Q10 — Visual Check (Human)
| Field | Value |
|-------|-------|
| **Pass Criteria** | 사역자 sees app and approves |
| **Script** | SKIP (human — deferred to Phase 5) |
| **Method** | 사역자 feedback |
| **On Failure** | Modification loop in Phase 5 |
| **Hallucination Risk** | H-SAFE |

### Q11 — Response Latency
| Field | Value |
|-------|-------|
| **Pass Criteria** | WebSocket roundtrip ≤ 100ms (localhost) |
| **Script** | `validate_gates.py` → `Q11` |
| **Method** | WebSocket connect → send timestamped ping → measure pong delta → ≤ 100ms |
| **On Failure** | Event handler optimization + remove unnecessary broadcasts |
| **Hallucination Risk** | H-CRITICAL |

---

## Design Quality Gates (D1-D9)

### D1 — Card UI
| Field | Value |
|-------|-------|
| **Pass Criteria** | `border-radius ≥ 12px` + `box-shadow` present + glassmorphism (optional) |
| **Script** | `validate_design_gates.py` → `D1` |
| **Method** | Regex `border-radius:\s*(\d+)` → all ≥ 12 AND `box-shadow:` exists |
| **On Failure** | Add border-radius + shadow to card elements |

### D2 — Animation
| Field | Value |
|-------|-------|
| **Pass Criteria** | ≥ 2 transitions with duration ≥ 150ms + page transition exists |
| **Script** | `validate_design_gates.py` → `D2` |
| **Method** | Regex `transition[^;]*(\d+)ms` → count ≥ 2 AND all ≥ 150 AND `@keyframes` or `animation` exists |
| **On Failure** | Add transition declarations |

### D3 — Dark Mode
| Field | Value |
|-------|-------|
| **Pass Criteria** | `prefers-color-scheme: dark` media query exists |
| **Script** | `validate_design_gates.py` → `D3` |
| **Method** | Regex `prefers-color-scheme:\s*dark` in CSS |
| **On Failure** | Add dark mode media query |

### D4 — Color Consistency
| Field | Value |
|-------|-------|
| **Pass Criteria** | CSS variables only, 0 hardcoded colors (outside `:root`) |
| **Script** | `validate_design_gates.py` → `D4` |
| **Method** | Extract all color values → exclude `var()` and `:root` → remaining count == 0 |
| **On Failure** | Replace hardcoded colors with CSS variables |

### D5 — Mobile Native Feel
| Field | Value |
|-------|-------|
| **Pass Criteria** | Fixed header (required) + bottom tab (for combined/quiz apps) |
| **Script** | `validate_design_gates.py` → `D5` |
| **Method** | `position: fixed` in CSS for header + `<nav>` with bottom positioning for applicable types |
| **On Failure** | Add fixed header + bottom navigation |

### D6 — Font Readability
| Field | Value |
|-------|-------|
| **Pass Criteria** | Body font ≥ 16px, headings ≥ 24px, Pretendard loaded |
| **Script** | `validate_design_gates.py` → `D6` |
| **Method** | Parse CSS font-size → body ≥ 16 → headings ≥ 24 AND `Pretendard` in font-family |
| **On Failure** | Update font sizes + add Pretendard import |

### D7 — Micro-interactions
| Field | Value |
|-------|-------|
| **Pass Criteria** | Button tap `scale` transform + list stagger animation |
| **Script** | `validate_design_gates.py` → `D7` |
| **Method** | `transform: scale` in CSS/JS AND (`animation-delay` or `stagger` or sequential delay pattern) |
| **On Failure** | Add scale feedback + stagger animations |

### D8 — Loading UX
| Field | Value |
|-------|-------|
| **Pass Criteria** | Skeleton UI or spinner present during data loading |
| **Script** | `validate_design_gates.py` → `D8` |
| **Method** | `.skeleton`, `.loading`, or `.spinner` in HTML class attributes |
| **On Failure** | Add skeleton/spinner components |

### D9 — Screen Impact
| Field | Value |
|-------|-------|
| **Pass Criteria** | Score change effect + confetti + sound on `/screen` route |
| **Script** | `validate_design_gates.py` → `D9` |
| **Method** | `confetti`, `AudioContext`, `playSound`, or `new Audio` in JS files |
| **On Failure** | Add confetti library + sound effects |

---

## Translation Gates (T1-T3)

### T1 — Translation Files Exist
| Field | Value |
|-------|-------|
| **Pass Criteria** | `.ko` files exist for all phase reports |
| **Script** | `validate_translation_gates.py` → `T1` |
| **Method** | Check `reports/phase{N}-*.ko.md` exists for each phase |

### T2 — Translation Quality
| Field | Value |
|-------|-------|
| **Pass Criteria** | pACS ≥ 70 for each translation |
| **Script** | `validate_translation_gates.py` → `T2` |
| **Method** | Parse `pacs-logs/phase*-translation-pacs.md` → extract pACS score → ≥ 70 |

### T3 — Glossary Consistency
| Field | Value |
|-------|-------|
| **Pass Criteria** | All glossary terms correctly translated |
| **Script** | `validate_translation_gates.py` → `T3` |
| **Method** | Load glossary YAML → for each term in source, verify Korean term in `.ko.md` |

---

## 4-Layer QA Architecture

```
L0: Anti-Skip Guard    — SOT outputs exist (산출물 존재 확인)
L1: Verification Gate  — Q1-Q11 + D1-D9 (P1 deterministic scripts)
L1.5: pACS Self-Rating — F/C/L 0-100 scoring (AI judges script data)
L2: Human Calibration  — 사역자 confirms in Phase 5 (Q10)
```

## Gate-to-Script Mapping

| Gate Range | Script | Execution Phase |
|------------|--------|-----------------|
| Q1-Q11 | `validate_gates.py` | Phase 4 (Pass 1) |
| D1-D9 | `validate_design_gates.py` | Phase 4 (Pass 1) |
| App-specific | `validate_app_specific.py` | Phase 4 (Pass 1) |
| Content accuracy | `validate_content_insertion.py` | Phase 4 (Pass 1) |
| Integration | `validate_integration.py` | Phase 3 (T-3.11) |
| T1-T3 | `validate_translation_gates.py` | Post-Phase 6 |
| pACS data | `compute_pacs_data.py` | Phase 4 |
