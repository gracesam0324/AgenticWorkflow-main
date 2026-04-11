# Design System — Church Retreat App

> Mobile-first design system reflecting 2026 middle school trends.
> Complete CSS/JS pattern definitions to achieve the "This is a real app!" impression.

---

## Color Palettes (3 Presets)

### [A] Calm / Subtle (Default)
```css
:root {
  --primary: #4F46E5;
  --secondary: #10B981;
  --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### [B] Vibrant / Energetic
```css
:root {
  --primary: #8B5CF6;
  --secondary: #F59E0B;
  --gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}
```

### [C] Warm / Cozy
```css
:root {
  --primary: #EC4899;
  --secondary: #06B6D4;
  --gradient: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
}
```

### Common Colors
```css
:root {
  --background: #F9FAFB;
  --surface: #FFFFFF;
  --text: #111827;
  --text-sub: #6B7280;
  --danger: #EF4444;
  --success: #22C55E;
}
```

---

## Glassmorphism

```css
/* Card / Modal glassmorphism (D1) */
.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* CSS Variables */
--glass-bg: rgba(255, 255, 255, 0.15);
--glass-blur: blur(12px);
--glass-border: 1px solid rgba(255, 255, 255, 0.2);
```

---

## Typography (Pretendard)

```css
/* Font loading — subset (~50KB, 2350 Korean chars + Latin + numbers) */
@font-face {
  font-family: 'Pretendard';
  src: url('./fonts/Pretendard-Regular.subset.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}
@font-face {
  font-family: 'Pretendard';
  src: url('./fonts/Pretendard-Bold.subset.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}

:root {
  --font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
  --font-size-base: 16px;   /* D6: body minimum */
  --font-size-lg: 18px;
  --font-size-xl: 24px;     /* D6: heading minimum */
  --font-size-2xl: 32px;
  --font-size-3xl: 48px;    /* Score display */
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: 1.6;
  color: var(--text);
}

h1, h2, h3 {
  font-weight: 700;
  line-height: 1.3;
}
h1 { font-size: var(--font-size-2xl); }
h2 { font-size: var(--font-size-xl); }
h3 { font-size: var(--font-size-lg); }
```

---

## Spacing & Layout

```css
:root {
  --radius: 16px;           /* D1: minimum 12px, we use 16px (2026 trend) */
  --max-width: 480px;       /* Mobile-first constraint */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}
```

---

## Animations (D2, D7)

### Transition Presets
```css
:root {
  --transition-fast: 150ms ease-out;    /* Button tap (D7) */
  --transition-normal: 250ms ease-out;  /* Card transition */
  --transition-slow: 400ms ease-out;    /* Page transition */
}
```

### D7: Button Tap Micro-interaction
```css
/* Scale feedback on tap — required by D7 */
.btn, button, [role="button"] {
  transition: transform var(--transition-fast);
  min-height: 44px;        /* Q6: touch target */
  min-width: 44px;         /* Q6: touch target */
}
.btn:active, button:active, [role="button"]:active {
  transform: scale(0.95);
}
```

### D7: List Stagger Animation
```css
/* Stagger animation for list items — required by D7 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.list-item {
  animation: fadeInUp 300ms ease-out both;
}
.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 50ms; }
.list-item:nth-child(3) { animation-delay: 100ms; }
.list-item:nth-child(4) { animation-delay: 150ms; }
.list-item:nth-child(5) { animation-delay: 200ms; }
/* Pattern: delay = index * 50ms */
```

### Page Transition
```css
@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.page-enter {
  animation: slideIn var(--transition-slow) both;
}
```

---

## Dark Mode (D3)

```css
@media (prefers-color-scheme: dark) {
  :root {
    --background: #111827;
    --surface: #1F2937;
    --text: #F9FAFB;
    --text-sub: #9CA3AF;

    --glass-bg: rgba(0, 0, 0, 0.3);
    --glass-border: 1px solid rgba(255, 255, 255, 0.1);
  }
}
```

---

## D5: Mobile Native Feel

### Fixed Header (Required)
```css
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--surface);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  z-index: 100;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-md);
}

.app-content {
  padding-top: 56px;   /* header height */
  padding-bottom: 72px; /* tab bar height, if present */
}
```

### Bottom Tab Navigation (Combined/Quiz apps)
```html
<nav class="tab-bar">
  <a href="/" class="tab-item active">
    <svg><!-- icon --></svg>
    <span>홈</span>
  </a>
  <a href="/quiz" class="tab-item">
    <svg><!-- icon --></svg>
    <span>퀴즈</span>
  </a>
  <!-- more tabs -->
</nav>
```
```css
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: var(--surface);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom);
}
```

---

## D8: Loading UX

### Skeleton UI
```html
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-card"></div>
```
```css
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius);
}
.skeleton-text { height: 16px; width: 60%; margin-bottom: 8px; }
.skeleton-card { height: 120px; width: 100%; }

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

### Spinner
```css
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## D9: Screen Impact Effects

### Confetti (Score change on /screen)
```javascript
// Minimal confetti implementation (no external dependency)
function showConfetti() {
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = Array.from({length: 100}, () => ({
    x: Math.random() * canvas.width,
    y: -10,
    vx: (Math.random() - 0.5) * 6,
    vy: Math.random() * 3 + 2,
    color: ['#ff6b6b','#ffd93d','#6bcb77','#4d96ff'][Math.floor(Math.random()*4)],
    size: Math.random() * 6 + 4
  }));

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let active = false;
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.1;
      if (p.y < canvas.height) { active = true; }
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x, p.y, p.size, p.size);
    });
    if (active) requestAnimationFrame(animate);
    else canvas.remove();
  }
  animate();
}
```

### Sound Effect
```javascript
// Score change sound (no external file needed)
function playScoreSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
  osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1); // E5
  osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2); // G5
  gain.gain.setValueAtTime(0.3, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.5);
}
```

---

## PWA Manifest Template

```json
{
  "name": "{{APP_NAME}}",
  "short_name": "{{SHORT_NAME}}",
  "description": "{{DESCRIPTION}}",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#F9FAFB",
  "theme_color": "{{PRIMARY_COLOR}}",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## Design Gate Checklist

| Gate | Requirement | CSS Pattern |
|------|-------------|-------------|
| D1 | `border-radius ≥ 12px` + `box-shadow` | `border-radius: var(--radius)` + `box-shadow: 0 8px 32px...` |
| D2 | ≥ 2 transitions ≥ 150ms + page transition | `transition: ... 150ms` + `@keyframes` |
| D3 | Dark mode query | `@media (prefers-color-scheme: dark)` |
| D4 | CSS variables only | All colors via `var(--name)` |
| D5 | Fixed header + bottom tab | `position: fixed` on header |
| D6 | Font sizes + Pretendard | `font-size: 16px` body, `24px` headings |
| D7 | Scale + stagger | `transform: scale(0.95)` + `animation-delay` |
| D8 | Skeleton/spinner | `.skeleton` or `.spinner` class |
| D9 | Confetti + sound | `confetti` + `AudioContext` in JS |
