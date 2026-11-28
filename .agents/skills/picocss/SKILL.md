---
name: css-picocss
description: Build websites with Pico CSS v2 — a minimal, classless-first, semantic CSS framework. Covers philosophy, decision trees, composition patterns, state handling, layout, typography, forms, components, color system, CSS variables, Sass customization, RTL, and complete code recipes. Use this when the project imports `@picocss/pico`, links `pico.min.css`, or the user asks to style with Pico.
---

# Pico CSS (v2) — Complete Working Reference

Pico CSS is a minimal, **dependency-free**, semantic CSS framework (~10 KB min.gz). It styles native HTML elements directly, so most pages need **zero classes**. Works in all modern browsers, ships light/dark color schemes, and exposes ~130 `--pico-*` CSS variables for customization.

**Current version:** `@picocss/pico@2`.

---

## 0. Guiding philosophy — read this first

These are hard preferences. Apply them unless the user explicitly overrides.

1. **Classless-first.** Reach for semantic HTML (`<article>`, `<nav>`, `<header>`, `<section>`, `<details>`, `<dialog>`, `<fieldset>`, `<hgroup>`) before any class. A page of Pico with zero classes is the ideal.
2. **Use Pico's native components and styles first.** Before suggesting custom markup or CSS, confirm Pico doesn't already cover it (tooltip via `data-tooltip`, loading via `aria-busy`, modal via `<dialog>`, accordion via `<details>`, etc.).
3. **When asked how to do X**, lead with **"use the native Pico way"** — reach for custom CSS only after exhausting semantic HTML + built-in attributes + CSS variables.
4. **Avoid customizations unless absolutely necessary.** If the default styling is close-enough, use it. Custom styling is the escape hatch, not the starting point.
5. **Never rebuild from Sass just to change a value.** Overriding a `--pico-*` variable in a small external CSS file beats a Sass recompile. Sass is only justified when disabling whole modules for a slim build, or when the parent-selector/theme pattern must be baked in.
6. **When custom CSS is truly needed:** put it in a *tiny, precise* external stylesheet loaded **after** `pico.min.css`. Override via CSS variables where possible; use logical properties (`margin-inline`, `padding-block`, `border-inline-start`) — Pico itself does, which is how RTL works for free.

**Mental model:** semantic HTML → built-in Pico attributes/classes → `--pico-*` variable override → tiny scoped CSS rule. Stop at the first step that solves the problem.

---

## 1. Decision tree — "what should I use?"

Use this before writing markup.

### Layout
- Centered page wrapper → `<main class="container">`
- Full-width wrapper → `<main class="container-fluid">`
- **Equal responsive columns (simple)** → `.grid` (auto-layout, collapses at 768px)
- **Precise N-column grid (preferred for dashboards/cards/galleries)** → `.grid` + the custom `.grid-2` … `.grid-8` helpers (see §7.2)
- Complex asymmetric / spanned / ordered layout → raw CSS Grid (custom)
- Horizontal scroll wrapper (wide tables) → `<div class="overflow-auto">`

### Grouping
- Row of buttons (visually joined) → `<div role="group">`
- Input + submit on one line (doesn't collapse on mobile) → `<fieldset role="group">`
- Search pattern → `<form role="search">`
- Vertical stack of labeled inputs → plain `<label>` elements (inputs are already 100% wide)
- Multi-column form → `.grid` (or `.grid-2`/`.grid-3`) inside the form

### Interactivity (prefer zero-JS, use Alpine JS if needed)
- Toggle/reveal a section → `<details><summary>`
- Mutually exclusive accordion → multiple `<details name="group">`
- Dropdown menu → `<details class="dropdown">`
- Tooltip → `data-tooltip="…" data-placement="…"`
- Loading state → `aria-busy="true"`
- Progress → `<progress value max>`
- Modal dialog → `<dialog>` + minimal JS (`.showModal()` / `.close()`)

### Styling / theming
- Change global accent → override `--pico-primary*` in a scoped `:root` rule, OR link the pre-compiled `pico.<color>.min.css`
- Light/dark toggle → `<html data-theme="light|dark">` + `localStorage`
- Invert a single card/section → `data-theme="dark"` on that element
- Validation color → `aria-invalid="true|false"` (do NOT write `.is-invalid` or similar)
- Brand tweak that can't be done via variables → tiny external CSS loaded after Pico

### When to bail out of Pico
If the user asks for a 12-column grid system, utility classes like `.mt-4`, heavy design-system overrides, or hundreds of lines of component CSS, say so. Pico isn't Tailwind/Bootstrap. Suggest either (a) a few CSS variable overrides, (b) a tiny bespoke stylesheet, or (c) a different framework.

---

## 2. Do / Don't — anti-pattern cheatsheet

### ✅ Do

- Use `<article>`, `<section>`, `<nav>`, `<header>`, `<main>`, `<footer>`, `<aside>`, `<hgroup>`, `<details>`, `<dialog>`, `<fieldset>`.
- Let inputs be `width: 100%` and let buttons auto-size — compose with `.grid` or `role="group"`.
- Use `aria-invalid`, `aria-busy`, `aria-current`, `data-theme`, `data-tooltip` — Pico hooks into ARIA and data-attrs, not bespoke classes.
- Theme via `--pico-*` CSS variables at `:root` or a scoped selector.
- Use native HTML behaviors: `<details>` for accordions, `<dialog>.showModal()` for modals, `<progress>` for progress bars, `<hr>` for separators.
- Add `autocomplete`, `inputmode`, and proper `type` on form fields — Pico leans on native a11y.
- Write custom CSS with **logical properties** (`margin-inline`, `padding-block`, `inset-inline-start`) so RTL keeps working.

### ❌ Don't

- Don't wrap everything in `<div>`s. A `<div>` with no semantic meaning is almost always wrong in Pico.
- Don't add classes in the classless build — you're defeating the purpose.
- Don't force `.grid` for complex layouts. It has ONE breakpoint (768px) and no span/offset/order.
- Don't replicate variants with custom CSS (`.btn-warning`, `.card-red`). Use `--pico-primary*` scoped to a selector, or `data-theme`.
- Don't override styles with `!important` or long selector chains — almost always the right fix is a `--pico-*` variable.
- Don't rebuild from Sass just to change a color, radius, or font. Override the variable.
- Don't use `overflow: hidden` on `<nav>` — Pico deliberately uses `overflow: visible` + negative margins so focus rings aren't clipped (see §14.7).
- Don't hand-roll `.is-valid` / `.is-invalid` — use `aria-invalid`.
- Don't write `margin-left`/`padding-right` in custom CSS; write `margin-inline-start`/`padding-inline-end` to preserve RTL (§19).
- Don't ship `pico.colors.min.css` whole for one accent — just override the `--pico-primary*` variables.

---

## 6. Color schemes (light / dark)

Pico auto-detects `prefers-color-scheme`. Force a scheme with `data-theme`:

```html
<html data-theme="light">  <!-- or "dark" -->
```

Scope per-element — inverted cards, hero sections, code blocks:

```html
<article data-theme="dark">This card is always dark.</article>
```

Toggle with Alpine (persistence recipe in §22.2):

```js
document.documentElement.setAttribute("data-theme", "dark");
```

Declare supported schemes so browsers render native controls correctly:

```html
<meta name="color-scheme" content="light dark" />
```

---

## 7. Layout

### 7.1 Containers

```html
<main class="container">...</main>        <!-- Fixed responsive widths -->
<main class="container-fluid">...</main>  <!-- Full width with padding -->
```

Breakpoints (default, Sass-configurable — see §17):

| Breakpoint | ≥ px  | Container width |
| ---------- | ----- | --------------- |
| xs         | 0     | 100%            |
| sm         | 576   | 510px           |
| md         | 768   | 700px           |
| lg         | 1024  | 950px           |
| xl         | 1280  | 1200px          |
| xxl        | 1536  | 1450px          |

### 7.2 Grid — `.grid` + custom `.grid-N` helpers **(preferred pattern)**

Pico's `.grid` is auto-layout only: equal-width columns that **collapse to a single column below 768px**. It has no column-span / offset / ordering.

**For precise N-column layouts, always pair `.grid` with these tiny helpers.** Paste this once into your app CSS (after `pico.min.css`) and reuse everywhere:

```css
/* grid.css — precise column counts, mobile-collapse at 768px */
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
.grid-5 { grid-template-columns: repeat(5, 1fr); }
.grid-6 { grid-template-columns: repeat(6, 1fr); }
.grid-8 { grid-template-columns: repeat(8, 1fr); }

@media only screen and (max-width: 768px) {
  .grid-2, .grid-3, .grid-4, .grid-5, .grid-6, .grid-8 {
    grid-template-columns: repeat(1, 1fr);
  }
}
```

Use it like this:

```html
<main class="container">
  <h2>grid-2</h2>
  <div class="grid grid-2">
    <article>1</article>
    <article>2</article>
    <article>3</article>
    <article>4</article>
    <article>5</article>
    <article>6</article>
    <article>7</article>
    <article>8</article>
  </div>

  <hr />

  <h2>grid-3</h2>
  <div class="grid grid-3">
    <article>1</article><article>2</article><article>3</article>
    <article>4</article><article>5</article><article>6</article>
    <article>7</article><article>8</article>
  </div>
</main>
```

**Rules of thumb:**
- Plain `.grid` for 2–4 siblings that should auto-fit and collapse.
- `.grid .grid-N` when you need exactly N columns on desktop. This is the default for card galleries, dashboards, pricing tables.
- For anything beyond equal columns (spans, offsets, asymmetric tracks, explicit ordering), drop into raw CSS Grid — don't try to force Pico's grid to do it.

### 7.3 Overflow auto

Horizontal scroll wrapper, typically for wide tables.

```html
<div class="overflow-auto">
  <table>…</table>
</div>
```

### 7.4 Landmarks (classless mode)

When using the classless build, `<header>`, `<main>`, `<footer>` **directly inside `<body>`** act as centered containers. `<section>` adds vertical spacing.

```html
<body>
  <header><h1>Site title</h1></header>
  <main>
    <section>…</section>
    <section>…</section>
  </main>
  <footer><small>© 2026</small></footer>
</body>
```

---

## 8. Typography

Fluid, rem-based, scales xs → xxl automatically. Zero classes.

```html
<h1>…</h1> … <h6>…</h6>

<hgroup>                           <!-- title + muted subtitle -->
  <h1>Main heading</h1>
  <p>Subtitle — collapsed margins and muted.</p>
</hgroup>

<p>Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to copy.</p>
<p><mark>Highlight</mark>, <del>removed</del>, <ins>added</ins>.</p>
<p><abbr title="Hypertext Markup Language">HTML</abbr> rules.</p>

<blockquote>
  "Simplicity is the ultimate sophistication."
  <footer><cite>— Leonardo da Vinci</cite></footer>
</blockquote>

<hr />

<p>Inline <code>const x = 1;</code></p>
<pre><code>function hello() { return "world"; }</code></pre>

<ul><li>…</li></ul>
<ol><li>…</li></ol>
```

All inline semantic elements styled: `<abbr>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<cite>`, `<del>`, `<ins>`, `<kbd>`, `<mark>`, `<s>`, `<small>`, `<sub>`, `<sup>`, `<u>`.

---

## 9. Links

```html
<a href="#">Default link</a>
<a href="#" class="secondary">Secondary</a>
<a href="#" class="contrast">Contrast</a>
<a href="#" role="button">Link as button</a>
<a href="#" role="button" class="outline secondary">Secondary outline</a>
```

---

## 10. Buttons

```html
<button>Primary</button>
<button class="secondary">Secondary</button>
<button class="contrast">Contrast</button>

<button class="outline">Primary outline</button>
<button class="outline secondary">Secondary outline</button>
<button class="outline contrast">Contrast outline</button>

<button disabled>Disabled</button>
<button aria-busy="true">Please wait…</button>
<button aria-busy="true" class="secondary" aria-label="Loading"></button>
```

### Inputs as buttons

```html
<input type="submit" value="Submit" />
<input type="button" value="Button" />
<input type="reset"  value="Reset"  />   <!-- styled as secondary -->
```

Form-type inputs and `<button>` inside `<form>` are `width: 100%`. To get inline width, wrap in `role="group"` or place outside the form.

### Button group (visually merged)

```html
<div role="group">
  <button>Day</button>
  <button aria-current="true">Week</button>
  <button>Month</button>
</div>
```

**Why `role="group"` and not `.grid`?** `role="group"` deliberately **collapses adjacent borders and connects border-radii** so the buttons read as a single segmented control. It also does not collapse on mobile. `.grid` is for independent siblings with gaps — different semantic purpose.

---

## 11. Forms

All form controls are `width: 100%` by default. Compose with `<fieldset>`, `.grid`/`.grid-N`, or `role="group"`. **Always include `autocomplete`, `inputmode` where relevant, and proper `type`** — Pico leans on native browser a11y.

### 11.1 Input + helper + validation

```html
<label>
  Email
  <input
    type="email"
    name="email"
    autocomplete="email"
    inputmode="email"
    placeholder="you@example.com"
    aria-describedby="email-helper"
    required
  />
  <small id="email-helper">We'll never share it.</small>
</label>
```

Validation uses **`aria-invalid`**, not classes:

```html
<input type="text" aria-invalid="false" value="ok" />   <!-- green -->
<input type="text" aria-invalid="true"  value="bad" />  <!-- red -->
```

Helper `<small>` below a field inherits the validation color.

Supported types (all styled): `text, email, number, password, tel, url, search, date, datetime-local, month, time, week, color, file, range, hidden` + `disabled`, `readonly`.

Common `autocomplete` tokens to use:
`email, current-password, new-password, username, name, given-name, family-name, tel, street-address, postal-code, country, cc-number, cc-exp, one-time-code, organization, url, bday`.

### 11.2 Textarea

```html
<label>
  Message
  <textarea name="msg" rows="4" placeholder="Your message"></textarea>
</label>
```

### 11.3 Select

```html
<label>
  Cuisine
  <select name="cuisine" autocomplete="off" required>
    <option selected disabled value="">Choose one…</option>
    <option>Italian</option>
    <option>Japanese</option>
    <option>Thai</option>
  </select>
</label>

<select multiple size="5" aria-label="Pick snacks">
  <option>Cheese</option>
  <option selected>Fruits</option>
  <option selected>Nuts</option>
</select>
```

### 11.4 Checkboxes, radios, switches

```html
<!-- Vertical checkboxes -->
<fieldset>
  <legend>Languages</legend>
  <label><input type="checkbox" name="en" checked /> English</label>
  <label><input type="checkbox" name="fr" /> French</label>
</fieldset>

<!-- Horizontal (split input + label) -->
<fieldset>
  <input type="checkbox" id="a" /><label for="a">Alpha</label>
  <input type="checkbox" id="b" /><label for="b">Beta</label>
</fieldset>

<!-- Radios -->
<fieldset>
  <legend>Size</legend>
  <label><input type="radio" name="size" value="s" checked /> Small</label>
  <label><input type="radio" name="size" value="m" /> Medium</label>
  <label><input type="radio" name="size" value="l" /> Large</label>
</fieldset>

<!-- Switch -->
<label>
  <input type="checkbox" role="switch" name="notify" />
  Notifications
</label>
```

Validation: same `aria-invalid` pattern. Indeterminate checkboxes need JS: `el.indeterminate = true`.

### 11.5 Range

```html
<label>
  Brightness
  <input type="range" min="0" max="100" value="40" />
</label>
```

### 11.6 Inline input + button (`role="group"`)

Visually merges the input and button into one pill. Does NOT collapse on mobile.

```html
<form>
  <fieldset role="group">
    <input
      type="email"
      name="email"
      autocomplete="email"
      placeholder="Your email"
    />
    <input type="submit" value="Subscribe" />
  </fieldset>
</form>

<form role="search">
  <input name="q" type="search" placeholder="Search" />
  <input type="submit" value="Go" />
</form>
```

### 11.7 Multi-column form via `.grid-2`

```html
<form>
  <div class="grid grid-2">
    <label>
      First name
      <input name="first" autocomplete="given-name" />
    </label>
    <label>
      Last name
      <input name="last" autocomplete="family-name" />
    </label>
  </div>

  <label>
    Email
    <input type="email" name="email" autocomplete="email" required />
  </label>

  <button type="submit">Save</button>
</form>
```

---

## 12. Tables

```html
<table>
  <thead>
    <tr><th scope="col">Planet</th><th scope="col">Diameter</th></tr>
  </thead>
  <tbody>
    <tr><th scope="row">Mercury</th><td>4,879 km</td></tr>
    <tr><th scope="row">Venus</th><td>12,104 km</td></tr>
  </tbody>
</table>

<table class="striped">…</table>

<div class="overflow-auto">
  <table>…</table>
</div>
```

Mix schemes per-section: `<thead data-theme="dark">`.

---

## 13. Components

### 13.1 Accordion — `<details>`/`<summary>` (zero JS)

```html
<details>
  <summary>Click me</summary>
  <p>Hidden content revealed.</p>
</details>

<!-- Mutually exclusive group, browser-native -->
<details name="faq" open>
  <summary>Question 1</summary><p>Answer.</p>
</details>
<details name="faq">
  <summary>Question 2</summary><p>Answer.</p>
</details>

<details>
  <summary role="button" class="secondary">Toggle</summary>
  <p>Body</p>
</details>
```

### 13.2 Card — `<article>`

```html
<article>Plain card body.</article>

<article>
  <header>Card header</header>
  Card body content.
  <footer>Card footer</footer>
</article>
```

### 13.3 Dropdown — `<details class="dropdown">`

```html
<details class="dropdown">
  <summary>Menu</summary>
  <ul>
    <li><a href="#">Profile</a></li>
    <li><a href="#">Settings</a></li>
    <li><a href="#">Sign out</a></li>
  </ul>
</details>

<details class="dropdown">
  <summary role="button" class="outline">Actions</summary>
  <ul><li><a href="#">Edit</a></li></ul>
</details>

<details class="dropdown">
  <summary>Menu</summary>
  <ul dir="rtl"><li><a href="#">Right-aligned</a></li></ul>
</details>
```

Inside `<nav>`, dropdowns shrink to content width.

### 13.4 Group — `role="group"` / `role="search"`

**Visual behavior (important):** `role="group"` does more than "stack horizontally." It **collapses adjacent borders between children and merges their outer border-radii** so the group reads as one control — an input+button pill, a segmented-button bar, etc. It also *does not collapse on mobile* (unlike `.grid`). Reach for it whenever you want siblings to read as a single unit.

See §10 (button group) and §11.6 (inline form) for examples.

### 13.5 Loading — `aria-busy="true"`

```html
<article aria-busy="true"></article>             <!-- block spinner -->
<span   aria-busy="true">Generating link…</span> <!-- inline spinner -->
<button aria-busy="true" aria-label="Please wait"></button>
<button aria-busy="true" class="outline">Please wait…</button>
```

### 13.6 Modal — `<dialog>` (minimal JS)

```html
<button onclick="confirmDlg.showModal()">Delete account</button>

<dialog id="confirmDlg">
  <article>
    <header>
      <button aria-label="Close" rel="prev" onclick="confirmDlg.close()"></button>
      <h3>Confirm delete</h3>
    </header>
    <p>This cannot be undone.</p>
    <footer>
      <button class="secondary" onclick="confirmDlg.close()">Cancel</button>
      <button onclick="confirmDlg.close()">Delete</button>
    </footer>
  </article>
</dialog>
```

Optional body-lock + animation classes on `<html>` (not on the dialog): `.modal-is-open`, `.modal-is-opening`, `.modal-is-closing`. Full pattern in §22.4.

### 13.7 Nav

```html
<nav>
  <ul><li><strong>Brand</strong></li></ul>
  <ul>
    <li><a href="#">Home</a></li>
    <li><a href="#">Docs</a></li>
    <li>
      <details class="dropdown">
        <summary>More</summary>
        <ul>
          <li><a href="#">Blog</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </details>
    </li>
    <li><a href="#" role="button">Sign in</a></li>
  </ul>
</nav>

<nav aria-label="breadcrumb">
  <ul>
    <li><a href="#">Home</a></li>
    <li><a href="#">Docs</a></li>
    <li>Nav</li>
  </ul>
</nav>

<aside>
  <nav>
    <ul>
      <li><a href="#">Getting started</a></li>
      <li><a href="#">Components</a></li>
    </ul>
  </nav>
</aside>
```

Breadcrumb divider: `--pico-nav-breadcrumb-divider` (default `">"`).

**Don't touch nav overflow.** Pico sets `overflow: visible` on `<nav>` on purpose, paired with negative margins on children, so that keyboard `:focus-visible` outlines aren't clipped. If a user asks you to tighten nav spacing, change `--pico-nav-element-spacing-*` / `--pico-nav-link-spacing-*` or spacing variables — never add `overflow: hidden`.

### 13.8 Progress

```html
<progress value="46" max="100"></progress>
<progress></progress>  <!-- indeterminate -->
```

### 13.9 Tooltip — `data-tooltip` (zero JS)

```html
<a href="#" data-tooltip="Top tooltip">Hover me</a>
<button data-tooltip="Right" data-placement="right">Right</button>
<button data-tooltip="Bottom" data-placement="bottom">Bottom</button>
<button data-tooltip="Left" data-placement="left">Left</button>
<em data-tooltip="Inline tooltip">inline element</em>
```

---

## 14. Color system (optional)

380 colors × 19 families × 19 shades.

Families: `red, pink, fuchsia, purple, violet, indigo, blue, azure, cyan, jade, green, lime, yellow, amber, pumpkin, orange, sand, grey, zinc, slate`.
Shades: `50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950`. `500` is canonical.

### Utility classes (needs `pico.colors.min.css`)

```html
<h2 class="pico-color-pink-500">Pink headline</h2>
<article class="pico-background-indigo-600">Indigo card</article>
```

This file is large — don't ship it whole just for an accent. Override `--pico-primary*` instead.

### Sass

```scss
@use "@picocss/pico/scss/colors" as *;

.alert {
  background: $pink-100;
  color:      $pink-800;
  border:     1px solid $pink-300;
}
```

---

## 15. CSS variables

### 15.1 Strategy — *where* to override

Pick the **smallest scope that does the job**:

| Intent                                                 | Where to put it                                   |
| ------------------------------------------------------ | ------------------------------------------------- |
| Whole-site theme (brand color, radius, font)           | `:root { … }` in a tiny app stylesheet loaded after Pico |
| Dark-mode tweaks                                       | `[data-theme="dark"] { … }` (see §15.5)           |
| One component variant (e.g. "highlighted" card)        | Scoped selector: `article.highlight { --pico-card-…: … }` |
| One-off, single element                                | Inline `style="--pico-…: …"` or `data-theme="dark"` |

**Almost never reach for property overrides** (`article { border-radius: 12px }`). Change the variable instead (`article { --pico-border-radius: 12px }`). Pico's internals consume the variable, and your override ripples through hover/focus/disabled states without you having to re-declare them.

### 15.2 Minimal theming example

```css
/* app.css — loaded AFTER pico.min.css */
:root {
  --pico-font-family: "Inter", system-ui, sans-serif;
  --pico-border-radius: 0.75rem;
  --pico-primary:            #5a4fcf;
  --pico-primary-background: #5a4fcf;
  --pico-primary-hover:      #4b41b0;
}
```

### 15.3 Layout, typography, spacing

```
--pico-font-family, --pico-font-family-sans-serif, --pico-font-family-monospace
--pico-font-size, --pico-font-weight, --pico-line-height
--pico-typography-spacing-vertical
--pico-block-spacing-vertical, --pico-block-spacing-horizontal
--pico-spacing                          (base unit for margins/padding)
--pico-border-radius, --pico-border-width, --pico-outline-width
--pico-text-underline-offset
--pico-transition                       (default 0.2s ease-in-out)
--pico-grid-column-gap, --pico-grid-row-gap
```

### 15.4 Colors (scheme-dependent)

```
Background & text
  --pico-background-color, --pico-color
  --pico-muted-color, --pico-muted-border-color
  --pico-h1-color … --pico-h6-color

Accent (primary / secondary / contrast)
  --pico-primary, --pico-primary-background, --pico-primary-border,
  --pico-primary-underline, --pico-primary-hover,
  --pico-primary-hover-background, --pico-primary-focus, --pico-primary-inverse
  (same suffixes exist for --pico-secondary-* and --pico-contrast-*)

Content
  --pico-mark-background-color, --pico-mark-color
  --pico-ins-color, --pico-del-color
  --pico-code-background-color, --pico-code-color
  --pico-blockquote-border-color, --pico-blockquote-footer-color
```

### 15.5 Overriding variables for dark mode

Scheme-dependent variables are re-assigned under `[data-theme="dark"]` and the `prefers-color-scheme: dark` media query. To override **only in dark mode**, target one of these — not `:root`:

```css
/* Applies only when data-theme="dark" is set explicitly */
[data-theme="dark"] {
  --pico-primary:            #a78bfa;
  --pico-primary-background: #7c3aed;
  --pico-card-background-color: #101014;
}

/* Or: apply to system dark mode too, when no explicit theme is set */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --pico-primary: #a78bfa;
  }
}
```

Putting dark tweaks at plain `:root` will leak them into light mode — a common mistake.

### 15.6 Forms

```
--pico-form-element-spacing-vertical, --pico-form-element-spacing-horizontal
--pico-form-element-background-color, --pico-form-element-border-color
--pico-form-element-color, --pico-form-element-placeholder-color
--pico-form-element-active-background-color, --pico-form-element-active-border-color
--pico-form-element-focus-color, --pico-form-element-disabled-opacity

Validation
--pico-form-element-valid-border-color,   --pico-form-element-valid-active-border-color,   --pico-form-element-valid-focus-color
--pico-form-element-invalid-border-color, --pico-form-element-invalid-active-border-color, --pico-form-element-invalid-focus-color

--pico-switch-background-color, --pico-switch-checked-background-color, --pico-switch-color
--pico-range-border-color, --pico-range-active-border-color, --pico-range-thumb-color, --pico-range-thumb-active-color
```

### 15.7 Components

```
--pico-card-background-color, --pico-card-border-color, --pico-card-box-shadow,
--pico-card-sectioning-background-color
--pico-dropdown-background-color, --pico-dropdown-border-color,
--pico-dropdown-color, --pico-dropdown-hover-background-color
--pico-modal-overlay-background-color, --pico-modal-overlay-backdrop-filter
--pico-nav-element-spacing-vertical, --pico-nav-element-spacing-horizontal,
--pico-nav-link-spacing-vertical,    --pico-nav-link-spacing-horizontal,
--pico-nav-breadcrumb-divider
--pico-progress-background-color, --pico-progress-color
--pico-tooltip-background-color,  --pico-tooltip-color
--pico-table-border-color, --pico-table-row-stripped-background-color
--pico-group-box-shadow, --pico-button-box-shadow
```

### 15.8 Icons (SVG data URIs)

```
--pico-icon-checkbox, --pico-icon-chevron, --pico-icon-date, --pico-icon-time,
--pico-icon-search, --pico-icon-close, --pico-icon-loading,
--pico-icon-valid, --pico-icon-invalid
```

Replace via variable, not by overriding element selectors.

---

## 16. Conditional styling — `.pico` wrapper

Use `pico.conditional.min.css` when integrating into an app that has its own styles. Only descendants of `.pico` get Pico styling.

```html
<!-- Styled -->
<form class="pico">
  <input type="email" />
  <button>Go</button>
</form>

<!-- Untouched -->
<form>
  <input type="email" />
  <button>Go</button>
</form>
```

---

## 17. Sass customization *(last resort)*

Use Sass only when a CSS variable override can't do the job — e.g. disabling modules for a slim build, baking in a parent selector, or changing breakpoints.

```scss
// Change accent color at build time
@use "@picocss/pico/scss/pico" with (
  $theme-color: "pink"
);

// Classless + semantic containers
@use "@picocss/pico/scss/pico" with (
  $enable-classes:            false,
  $enable-semantic-container: true
);

// Scoped build: .pico or #root
@use "@picocss/pico/scss/pico" with (
  $parent-selector: ".pico"   // or "#root" for React/Next
);

// Slim build — drop unused modules
@use "@picocss/pico/scss/pico" with (
  $modules: (
    "components/accordion": false,
    "components/card":      false,
    "components/dropdown":  false,
    "components/modal":     false,
    "components/nav":       false,
    "components/progress":  false,
    "components/tooltip":   false,
  )
);

// Custom breakpoints + container widths
@use "@picocss/pico/scss/pico" with (
  $breakpoints: (
    sm:  ( breakpoint: 640px,  viewport: 600px  ),
    md:  ( breakpoint: 820px,  viewport: 780px  ),
    lg:  ( breakpoint: 1100px, viewport: 1040px ),
    xl:  ( breakpoint: 1400px, viewport: 1300px ),
    xxl: ( breakpoint: 1700px, viewport: 1600px ),
  )
);
```

Key flags:

| Variable                         | Purpose                                            |
| -------------------------------- | -------------------------------------------------- |
| `$theme-color`                   | Accent color (20 options, see §4).                 |
| `$enable-classes`                | `false` → classless build.                         |
| `$enable-semantic-container`     | `<header>/<main>/<footer>` act as container.       |
| `$enable-responsive-typography`  | Fluid font sizes (default `true`).                 |
| `$enable-viewport`               | Centered vs. fluid layout.                         |
| `$parent-selector`               | `".pico"` / `"#root"` — scope everything.          |
| `$modules`                       | Map toggling individual modules on/off.            |
| `$breakpoints`                   | Map of `sm/md/lg/xl/xxl` → breakpoint + viewport.  |

CLI:

```bash
sass --load-path=node_modules/@picocss/pico/scss main.scss main.css
```

---

## 18. React / Vue / Next / Gatsby

```jsx
import "@picocss/pico/css/pico.min.css";
```

For SPAs whose root is `<div id="root">`, bake in the parent selector so semantic containers work there:

```scss
@use "@picocss/pico/scss/pico" with (
  $parent-selector: "#root"
);
```

```jsx
export default function App() {
  return (
    <main className="container">
      <h1>Hello Pico + React</h1>
      <button className="secondary outline">Click</button>
    </main>
  );
}
```

---

## 19. RTL & CSS logical properties

```html
<html dir="rtl" lang="ar">…</html>
<blockquote dir="rtl" lang="ar">…</blockquote>
```

**Why it just works:** Pico's internals use **CSS logical properties** (`margin-inline-start`, `padding-block-end`, `border-inline-end`, `inset-inline-start`, etc.) rather than physical properties (`margin-left`, `padding-right`). The browser flips direction automatically when `dir="rtl"` is set.

**Implication for your custom CSS:** Write logical properties too, or you'll break RTL.

| Avoid              | Prefer                        |
| ------------------ | ----------------------------- |
| `margin-left`      | `margin-inline-start`         |
| `margin-right`     | `margin-inline-end`           |
| `padding-top`      | `padding-block-start`         |
| `padding-bottom`   | `padding-block-end`           |
| `left`, `right`    | `inset-inline-start/end`      |
| `border-left`      | `border-inline-start`         |
| `text-align: left` | `text-align: start`           |

---

## 20. Composition patterns (real-world UI)

Primitives are easy; composition is where LLMs slip. Use these as templates.

### 20.1 Navbar: brand + links + dropdown + CTA

```html
<nav class="container-fluid">
  <ul>
    <li><strong>Acme</strong></li>
  </ul>
  <ul>
    <li><a href="#">Features</a></li>
    <li><a href="#">Docs</a></li>
    <li>
      <details class="dropdown">
        <summary>Resources</summary>
        <ul>
          <li><a href="#">Blog</a></li>
          <li><a href="#">Changelog</a></li>
          <li><a href="#">Community</a></li>
        </ul>
      </details>
    </li>
    <li><a href="#">Sign in</a></li>
    <li><a href="#" role="button">Sign up</a></li>
  </ul>
</nav>
```

### 20.2 Dashboard: sidebar + main

Pico doesn't ship a sidebar primitive. Use raw CSS Grid for the shell (two tracks), Pico for everything inside:

```html
<style>
  .app-shell {
    display: grid;
    grid-template-columns: 240px 1fr;
    min-block-size: 100vh;
  }
  @media (max-width: 768px) {
    .app-shell { grid-template-columns: 1fr; }
  }
</style>

<div class="app-shell">
  <aside>
    <nav>
      <ul>
        <li><strong>Acme</strong></li>
        <li><a href="#" aria-current="page">Overview</a></li>
        <li><a href="#">Projects</a></li>
        <li><a href="#">Team</a></li>
        <li><a href="#">Settings</a></li>
      </ul>
    </nav>
  </aside>

  <main class="container-fluid">
    <hgroup>
      <h1>Overview</h1>
      <p>Weekly summary</p>
    </hgroup>

    <section class="grid grid-3">
      <article><header>Revenue</header><h2>$48,250</h2></article>
      <article><header>Users</header><h2>1,204</h2></article>
      <article><header>Churn</header><h2>2.1%</h2></article>
    </section>
  </main>
</div>
```

### 20.3 Form + inline validation + grouped actions

```html
<form id="profileForm" novalidate>
  <div class="grid grid-2">
    <label>
      First name
      <input name="first" autocomplete="given-name" required />
    </label>
    <label>
      Last name
      <input name="last" autocomplete="family-name" required />
    </label>
  </div>

  <label>
    Email
    <input
      type="email"
      name="email"
      autocomplete="email"
      aria-describedby="email-msg"
      required
    />
    <small id="email-msg">Used for billing receipts.</small>
  </label>

  <label>
    Password
    <input
      type="password"
      name="password"
      autocomplete="new-password"
      minlength="8"
      aria-describedby="pwd-msg"
      required
    />
    <small id="pwd-msg">At least 8 characters.</small>
  </label>

  <fieldset role="group">
    <button type="button" class="secondary" onclick="history.back()">Cancel</button>
    <button type="submit">Save changes</button>
  </fieldset>
</form>
```

Pair with the validation flow in §22.3.

### 20.4 Table with filters + row actions

```html
<section>
  <header class="grid grid-2">
    <form role="search">
      <input type="search" name="q" placeholder="Filter projects…" />
    </form>
    <div role="group">
      <button class="secondary">Export</button>
      <button>New project</button>
    </div>
  </header>

  <div class="overflow-auto">
    <table class="striped">
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">Owner</th>
          <th scope="col">Status</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">Atlas</th>
          <td>Alex</td>
          <td><mark>Active</mark></td>
          <td>
            <div role="group">
              <button class="secondary outline">Edit</button>
              <button class="contrast outline">Archive</button>
            </div>
          </td>
        </tr>
        <!-- more rows -->
      </tbody>
    </table>
  </div>
</section>
```

### 20.5 Pricing cards (inverted middle tier)

```html
<section class="grid grid-3">
  <article>
    <header><h3>Starter</h3></header>
    <h2>$9<small>/mo</small></h2>
    <ul><li>10 projects</li><li>Email support</li></ul>
    <footer><button class="outline">Choose</button></footer>
  </article>
  <article data-theme="dark">
    <header><h3>Pro</h3></header>
    <h2>$29<small>/mo</small></h2>
    <ul><li>Unlimited projects</li><li>Priority support</li></ul>
    <footer><button>Choose</button></footer>
  </article>
  <article>
    <header><h3>Team</h3></header>
    <h2>$99<small>/mo</small></h2>
    <ul><li>SSO</li><li>Dedicated CSM</li></ul>
    <footer><button class="outline">Choose</button></footer>
  </article>
</section>
```

---

## 21. Full landing-page skeleton

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="light dark" />
    <title>My Product</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
    <link rel="stylesheet" href="/css/app.css" />
  </head>
  <body>
    <nav class="container">
      <ul><li><strong>Acme</strong></li></ul>
      <ul>
        <li><a href="#features">Features</a></li>
        <li><a href="#pricing">Pricing</a></li>
        <li><a href="#" role="button">Sign up</a></li>
      </ul>
    </nav>

    <main class="container">
      <hgroup>
        <h1>Ship faster with Acme</h1>
        <p>The all-in-one platform for busy teams.</p>
      </hgroup>

      <form role="search">
        <input
          type="email"
          name="email"
          autocomplete="email"
          placeholder="you@company.com"
        />
        <input type="submit" value="Request demo" />
      </form>

      <section id="features" class="grid grid-3">
        <article><h3>Fast</h3><p>Sub-100ms responses.</p></article>
        <article><h3>Secure</h3><p>SOC 2 compliant.</p></article>
        <article><h3>Simple</h3><p>Deploy in minutes.</p></article>
      </section>
    </main>

    <footer class="container">
      <small>© 2026 Acme · <a href="#">Privacy</a> · <a href="#">Terms</a></small>
    </footer>
  </body>
</html>
```

---

## 22. State handling patterns

### 22.1 `aria-busy` lifecycle (loading a button)

```html
<button id="saveBtn">Save</button>

<script>
  const btn = document.getElementById("saveBtn");
  btn.addEventListener("click", async () => {
    btn.setAttribute("aria-busy", "true");
    btn.disabled = true;
    btn.textContent = "";                // spinner-only look
    try {
      await save();
    } finally {
      btn.removeAttribute("aria-busy");
      btn.disabled = false;
      btn.textContent = "Save";
    }
  });
</script>
```

For a card-level loader: set `aria-busy="true"` on the `<article>` before the fetch, remove on completion.

### 22.2 `data-theme` persistence

```html
<button id="themeBtn" aria-label="Toggle theme">🌓</button>

<script>
  const root  = document.documentElement;
  const saved = localStorage.getItem("theme");
  if (saved) root.setAttribute("data-theme", saved);

  document.getElementById("themeBtn").addEventListener("click", () => {
    const current = root.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  });
</script>
```

If no `data-theme` is set, the page falls back to `prefers-color-scheme`. Only set it when the user explicitly chooses.

### 22.3 Form validation flow (before/after submit)

Start with fields **unvalidated** (omit `aria-invalid`). On submit, validate each field and reflect the state:

```html
<form id="signinForm" novalidate>
  <label>
    Email
    <input
      type="email" name="email" autocomplete="email"
      aria-describedby="email-msg" required
    />
    <small id="email-msg"></small>
  </label>
  <button type="submit">Sign in</button>
</form>

<script>
  const form = document.getElementById("signinForm");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    let ok = true;
    for (const field of form.querySelectorAll("input")) {
      const valid = field.checkValidity();
      field.setAttribute("aria-invalid", valid ? "false" : "true");
      const msg = document.getElementById(field.getAttribute("aria-describedby"));
      if (msg) msg.textContent = valid ? "Looks good" : field.validationMessage;
      if (!valid) ok = false;
    }
    if (ok) form.submit();
  });
</script>
```

**Rules:**
- Omit `aria-invalid` before the user has interacted — don't show red boxes on page load.
- After a failed submit or on `blur`, set `aria-invalid="true"` / `"false"`.
- Put human-readable errors in the `<small>` referenced by `aria-describedby`.

### 22.4 Modal open/close with body-lock and animation

```html
<button onclick="openModal(confirmDlg)">Open</button>

<dialog id="confirmDlg">
  <article>
    <header>
      <button
        aria-label="Close" rel="prev"
        onclick="closeModal(confirmDlg)"
      ></button>
      <h3>Delete?</h3>
    </header>
    <p>This cannot be undone.</p>
    <footer>
      <button class="secondary" onclick="closeModal(confirmDlg)">Cancel</button>
      <button onclick="closeModal(confirmDlg)">Delete</button>
    </footer>
  </article>
</dialog>

<script>
  const html = document.documentElement;
  const ANIM = 400;

  function openModal(dlg) {
    html.classList.add("modal-is-open", "modal-is-opening");
    dlg.showModal();
    setTimeout(() => html.classList.remove("modal-is-opening"), ANIM);
  }
  function closeModal(dlg) {
    html.classList.add("modal-is-closing");
    setTimeout(() => {
      html.classList.remove("modal-is-open", "modal-is-closing");
      dlg.close();
    }, ANIM);
  }

  // Close on backdrop click
  document.querySelectorAll("dialog").forEach((d) => {
    d.addEventListener("click", (e) => {
      if (e.target === d) closeModal(d);
    });
  });
</script>
```

**Pattern rules:**
- Always pair `html.classList.add("modal-is-open")` with `dlg.showModal()` to prevent background scroll.
- Always remove `modal-is-open` *after* the closing animation completes, or the body unlocks mid-animation.
- Use `rel="prev"` on the close `<button>` — Pico styles it as the small ✕ in the header.

---

## 23. Gotchas & tips

- Form controls are 100% wide. Wrap in `role="group"`, `.grid-N`, or a narrower container for inline widths.
- Pico's built-in `.grid` has ONE breakpoint (768px) and no spans. For precise columns use `.grid-N` helpers (§7.2); for asymmetric tracks drop into raw CSS Grid.
- Variants are classed-only. `.secondary`, `.contrast`, `.outline`, `.striped`, `.dropdown`, `.container`, `.grid`, `.modal-is-*`, `.overflow-auto` don't exist in `pico.classless.*`.
- `<dialog>` needs JS. Pico styles it but doesn't open/close it.
- Validation uses `aria-invalid`, not classes. Omit the attribute for neutral; `"false"` = green; `"true"` = red.
- `.pico-colors.min.css` is heavy — don't ship it just for one accent. Override `--pico-primary*` instead.
- Icons are SVG data URIs. Replace via `--pico-icon-*`, not by selector override.
- `data-theme` cascades. Setting it on any element re-themes its subtree via scheme-dependent variables.
- Multiple `<ul>` inside `<nav>` split left/right. Put `<nav>` inside `<aside>` for a vertical stack.
- Never `overflow: hidden` on `<nav>` — clips focus rings.
- Indeterminate checkboxes require JS (`el.indeterminate = true`).

---

## 24. Quick lookup cheatsheet

| Need                       | Write                                                            |
| -------------------------- | ---------------------------------------------------------------- |
| Centered page              | `<main class="container">`                                       |
| Full-width page            | `<main class="container-fluid">`                                 |
| 2/3/4/N equal columns      | `<div class="grid grid-3">…</div>` (+ §7.2 helper CSS)           |
| Auto-layout columns        | `<div class="grid">…</div>`                                      |
| Card                       | `<article>…</article>`                                           |
| Modal                      | `<dialog id="x"><article>…</article></dialog>` + `x.showModal()` |
| Dropdown                   | `<details class="dropdown"><summary>…</summary>…</details>`      |
| Accordion                  | `<details><summary>…</summary>…</details>`                       |
| Tooltip                    | `data-tooltip="…" data-placement="top\|right\|bottom\|left"`     |
| Spinner (inline/card/btn)  | `aria-busy="true"`                                               |
| Progress                   | `<progress value="50" max="100"></progress>`                     |
| Switch                     | `<input type="checkbox" role="switch" />`                        |
| Button row (merged)        | `<div role="group">…</div>`                                      |
| Inline form (input+submit) | `<fieldset role="group">…</fieldset>`                            |
| Search form                | `<form role="search">…</form>`                                   |
| Valid/invalid input        | `aria-invalid="false"` / `"true"`                                |
| Force dark (global)        | `<html data-theme="dark">`                                       |
| Force dark (one element)   | `<article data-theme="dark">`                                    |
| Secondary/contrast button  | `<button class="secondary">` / `class="contrast"`                |
| Outline button             | `<button class="outline">` (+ secondary/contrast)                |
| Striped table              | `<table class="striped">`                                        |
| Scrollable wrapper         | `<div class="overflow-auto">`                                    |
| Breadcrumb                 | `<nav aria-label="breadcrumb"><ul>…</ul></nav>`                  |
| Subtitle pattern           | `<hgroup><h1>…</h1><p>…</p></hgroup>`                            |

**Philosophy recap:** semantic HTML → Pico attribute/class → CSS variable override → tiny scoped CSS. Stop at the first step that works.
