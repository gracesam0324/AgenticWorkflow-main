# Code Convention — Church Retreat App

## Naming

### Files
- Kebab-case: `quiz-buzzer.js`, `team-score.css`
- Test files: `test_<module>.js` (snake_case with test_ prefix)
- Entry points: `server.js`, `index.html`, `app.js`

### Variables & Functions
- camelCase: `teamScore`, `handleBuzzer()`
- Constants: UPPER_SNAKE: `MAX_TEAMS`, `WS_RECONNECT_INTERVAL`
- DOM elements: prefix with `el`: `elBuzzerBtn`, `elScoreBoard`
- Event handlers: prefix with `handle` or `on`: `handleBuzzerPress()`, `onWsMessage()`

### CSS
- CSS Custom Properties: `--primary`, `--font-size-base`
- BEM-like classes: `card`, `card__title`, `card--active`
- Utility classes: `text-center`, `mt-4`, `hidden`
- Animation classes: `fade-in`, `slide-up`, `pulse`

## Formatting

### JavaScript
- 2-space indentation
- Single quotes for strings
- Semicolons required
- Template literals for multi-line strings and interpolation
- Arrow functions for callbacks
- `const` by default, `let` when reassignment needed, NEVER `var`

### CSS
- 2-space indentation
- One property per line
- CSS custom properties at :root level
- Media queries at bottom of file, grouped by breakpoint
- Mobile-first: base styles for 375px, `@media (min-width: ...)` for larger

### HTML
- 2-space indentation
- Double quotes for attributes
- Self-closing tags for void elements: `<img />`, `<br />`
- Semantic elements: `<header>`, `<main>`, `<nav>`, `<section>`, `<article>`
- Korean text always in UTF-8

## Structure

### Project Layout
```
project-root/
├── index.html          ← Main entry point (student view)
├── admin.html          ← Admin console (password protected)
├── screen.html         ← Projector view (score/lyrics display)
├── server.js           ← Express + WebSocket server
├── app.js              ← Client-side main logic
├── styles.css          ← Design system + all styles
├── animations.css      ← Micro-interactions + transitions
├── manifest.json       ← PWA manifest
├── service-worker.js   ← PWA service worker
├── data.json           ← Persistent data snapshot
├── package.json        ← Dependencies
├── app-state.json      ← SOT (workflow state)
├── (verify-app.js removed — orchestrator calls P1 scripts directly via Bash, §9.4)
├── regenerate-qr.js    ← QR regeneration script
├── scripts/            ← P1 Deterministic Validation Scripts (copied from templates in Phase 3)
│   ├── validate_gates.py              (Q1-Q11)
│   ├── validate_design_gates.py       (D1-D9)
│   ├── validate_integration.py        (HTML↔CSS↔JS cross-ref)
│   ├── validate_translation_gates.py  (T1-T3)
│   ├── validate_content_insertion.py   (SOT↔HTML content match)
│   ├── validate_app_specific.py       (app-type-specific gates)
│   └── compute_pacs_data.py           (pACS objective data extraction)
│   # NOTE: validate_app_state_schema.py is NOT here — it lives at infrastructure level
│   #        (.claude/hooks/scripts/) because it must work before this project exists.
├── tests/              ← Test files
│   ├── test_server.js
│   ├── test_websocket.js
│   ├── test_admin.js
│   ├── test_content.js
│   ├── test_security.js
│   └── test_pwa.js
├── reports/            ← English phase reports + .ko translations (AC-4)
│   ├── phase1-intent-report.md
│   ├── phase1-intent-report.ko.md
│   └── ...
├── pacs-logs/          ← Translation pACS score logs (AC-4)
├── results/            ← Data export output
├── archives/           ← App archive for reuse
└── assets/
    ├── icon-192.png
    ├── icon-512.png
    └── qr-code.png
```

## Comments

- Comment WHY, not WHAT
- Korean comments allowed for user-facing message explanations
- JSDoc for public API functions only (server routes, WebSocket handlers)
- No comments on self-explanatory code

## Error Handling

- User-facing errors: Korean message, no technical details
- Server errors: console.error with English technical detail
- WebSocket: auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- HTTP fallback: 5-second polling when WebSocket unavailable

## Security

- ALL user input sanitized before DOM insertion (XSS prevention)
- No eval(), no innerHTML with user data (use textContent)
- Admin routes require password middleware
- No API keys in client-side code
- No data sent outside project folder
