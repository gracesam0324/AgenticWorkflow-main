# Code Quality Guide — Church Retreat App

## Quality Pyramid

```
              ┌─────────┐
              │ UX Feel │  ← D1-D9 design gates
             ┌┴─────────┴┐
             │ Functional │  ← Q1-Q11 technical gates
            ┌┴───────────┴┐
            │   Correct    │  ← TDD tests pass
           ┌┴─────────────┴┐
           │    Secure      │  ← XSS, auth, no data leak
          ┌┴───────────────┴┐
          │   Structured     │  ← Code convention compliance
         └───────────────────┘
```

## Quality Evaluation Criteria

### Tier 1: Correctness (Must Pass)
- [ ] Server starts without errors
- [ ] All HTML renders without broken characters
- [ ] All JavaScript executes without runtime errors
- [ ] Korean text displays correctly across all pages
- [ ] Navigation works on mobile (375px viewport)

### Tier 2: Security (Must Pass)
- [ ] XSS: `<script>` tags in user input are neutralized
- [ ] Auth: /admin requires password, rejects unauthorized access
- [ ] Data: No data sent outside project folder
- [ ] Keys: No API keys in client-side code
- [ ] Input: All user input (nickname, prayer requests) sanitized

### Tier 3: Functionality (Must Pass)
- [ ] WebSocket connects and maintains connection
- [ ] HTTP polling fallback activates on WS failure
- [ ] QR code decodes to correct server URL
- [ ] Admin actions reflect on student screens
- [ ] PWA installs and works offline (cached content)
- [ ] Bundle size <= 500KB hard limit

### Tier 4: Design (Must Pass for "진짜 앱" feel)
- [ ] Card UI with rounded corners and shadows
- [ ] Smooth animations (>= 150ms transitions)
- [ ] Dark mode support
- [ ] Consistent color scheme (CSS variables only)
- [ ] Touch targets >= 44x44px
- [ ] Mobile-native feel (fixed header, bottom nav)
- [ ] Loading states (skeleton UI or spinner)
- [ ] Micro-interactions (button press feedback)
- [ ] Projector screen effects (confetti, sound)

### Tier 5: Polish (Should Pass)
- [ ] Font: Pretendard loads, Korean readable
- [ ] Responsive: works 375px to 1920px
- [ ] Offline: graceful degradation when disconnected
- [ ] Reconnection: auto-reconnect within 30 seconds
- [ ] Error messages: Korean, friendly, actionable
- [ ] Bundle target <= 300KB (gzip)

## pACS Scoring

| Dimension | Full Name | What It Measures |
|-----------|-----------|-----------------|
| F | Content Accuracy | Does the app contain exactly what the user requested? |
| C | Feature Completeness | Are all requested features implemented and working? |
| L | Code Correctness | Does the app run without errors and pass quality gates? |

**Score Calculation**: `pACS = min(F, C, L)`

| Score | Color | Action |
|-------|-------|--------|
| >= 70 | GREEN | Auto-proceed to next phase |
| 50-69 | YELLOW | Proceed with flag, note in SOT |
| < 50 | RED | Rework required, do not proceed |

## Code Review Checklist (for quality-checker)

### Before marking any code generation complete:
1. [ ] All test files exist and pass (`node --test tests/`)
2. [ ] verify-app.js exists and returns overall: "PASS"
3. [ ] No TODO/FIXME/HACK comments in production code
4. [ ] No console.log in production code (use proper logging)
5. [ ] No hardcoded Korean strings in JavaScript logic (use data attributes or constants)
6. [ ] All CSS colors use CSS custom properties
7. [ ] All file paths use path.join() (Windows compatibility)
8. [ ] Package.json has no unnecessary dependencies
9. [ ] Git checkpoint exists for the completed step
10. [ ] app-state.json updated with completion status

## "Beautiful Code" Standards (예쁜 코드 기준)

### Readability
- Function length: <= 30 lines (extract if longer)
- Nesting depth: <= 3 levels (extract or early return)
- Variable names: self-documenting (no single-letter except loop indices)
- Consistent patterns: same problem → same solution pattern

### Simplicity
- One function, one responsibility
- No premature abstraction (3 similar blocks > 1 forced generic)
- No speculative features ("might need this later")
- Prefer built-in APIs over library imports

### Consistency
- Same formatting everywhere (2-space indent, single quotes)
- Same error handling pattern everywhere
- Same naming convention everywhere
- Same file structure for all app types

### Maintainability
- New app type = add content + routes (no core changes needed)
- Style change = modify CSS variables only (no hunting through code)
- Content update = modify data file or HTML content section only
