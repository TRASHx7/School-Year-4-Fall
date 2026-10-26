# Study Guide Style Guide

The fixed visual style for every study guide. **All of this CSS and the quiz engine are already in `assets/` and are added by `build_guide.py`; do not paste them into guides.** Use this file to look up class names and component markup when writing `content.html`. Demo-specific styles can go in a `<style>` block inside the demo's markup.

## Contents
1. Page skeleton
2. Fonts
3. Color tokens (light and dark)
4. Layout and sidebar
5. Typography
6. Equations and fractions
7. Callouts (Analogy, Tricky bits, Filled in)
8. Big picture chain
9. Tables
10. Worked examples and practice problems
11. Demos and controls
12. Quizzes
13. Formula sheet and print
14. Behavior rules

## 1. Page skeleton

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>[Topic] Guide</title>  <!-- 2 to 4 words -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
<style>/* all CSS below */</style>
</head><body>
<div class="wrap">
  <nav class="toc" aria-label="Contents">
    <button class="btn" id="resetAll">Reset all progress</button>
    <h2>Start</h2><ol><li><a href="#big">Big picture</a></li></ol>
    <h2>Part 1 · [Theme]</h2>
    <ol><li><a href="#s1">1 [Section] <span class="chip" data-chip="q1"></span></a></li></ol>
    <!-- more parts -->
    <h2>Finish</h2>
    <ol>
      <li><a href="#final">Final exam <span class="chip" data-chip="final"></span></a></li>
      <li><a href="#formulas">Formula sheet</a></li>
    </ol>
  </nav>
  <main>
    <header class="hero">
      <div class="eyebrow">[Course code or subject] · Study guide</div>
      <h1>[Title]</h1>
      <p class="lede">[One-paragraph summary]</p>
    </header>
    <section class="sec" id="big">...</section>
    <h2 class="part">Part 1 · [Theme]</h2>
    <section class="sec" id="s1"><h3><span class="num">Section 1</span>[Title]</h3>...</section>
    ...
    <section class="sec final" id="final">...</section>
    <section class="sec" id="formulas">...</section>
    <footer>...</footer>
  </main>
</div>
<script>/* all JS inline */</script>
</body></html>
```

Everything is in one file. The only external scripts are KaTeX from cdnjs.cloudflare.com.

## 2. Fonts

- `--display`: Archivo (headings, labels, buttons, sidebar)
- `--body`: Source Serif 4 (prose, equations)
- `--mono`: JetBrains Mono (score chips, eyebrow and small UI labels only; never for math)
- Math: KaTeX's own fonts (Computer Modern look), via the KaTeX stylesheet

## 3. Color tokens

```css
:root{
  --bg:#F3F5F2; --surface:#FFFFFF; --surface-2:#E8ECE7; --ink:#18212B; --muted:#56616D; --line:#D3D9D2;
  --accent:#1D5FC2; --accent-soft:#E2EBFA; --on-accent:#FFFFFF;
  --c1:#1D5FC2; --c2:#C24E12; --c3:#23804D; --grid:#DCE1DB;   /* plot series 1, 2, 3 and grid */
  --ana-bg:#FFF5DC; --ana-line:#C9920F; --ana-ink:#6B4B00;
  --trk-bg:#FBEAE8; --trk-line:#C0392B; --trk-ink:#8A2318;
  --fill-bg:#E9F0FB; --fill-line:#5B7DB8; --fill-ink:#2A4677;
  --good:#1E7A47; --good-bg:#E3F3E9; --bad:#B3261E; --bad-bg:#FBE6E4; --hl:#FFF1C2;
  --display:"Archivo","Helvetica Neue",Arial,sans-serif;
  --body:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){ /* dark set */ }
}
:root[data-theme="dark"]{ /* same dark set */ }
```

Dark set (use in both dark blocks):

```css
color-scheme:dark;
--bg:#10151A; --surface:#172028; --surface-2:#1F2A34; --ink:#E3E8ED; --muted:#9AA6B2; --line:#2B3742;
--accent:#78AAFF; --accent-soft:#1B2B45; --on-accent:#0E1620;
--c1:#78AAFF; --c2:#F0935A; --c3:#5CC48A; --grid:#26313B;
--ana-bg:#2A2413; --ana-line:#C9982A; --ana-ink:#F1D48A;
--trk-bg:#2E1B1B; --trk-line:#E0675A; --trk-ink:#F4B4AB;
--fill-bg:#18243A; --fill-line:#6F93D6; --fill-ink:#B9CDF2;
--good:#5CC48A; --good-bg:#16301F; --bad:#F07167; --bad-bg:#361B1A; --hl:#3A3316;
```

Canvas drawings read these tokens with `getComputedStyle(document.documentElement)` and redraw when the color scheme changes.

## 4. Layout and sidebar

```css
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg); color:var(--ink); font-family:var(--body); font-size:17px; line-height:1.6; margin:0; padding-inline:16px}
.wrap{max-width:1140px; margin:0 auto; display:grid; grid-template-columns:230px minmax(0,1fr); gap:48px; padding-block:40px 80px}
main{max-width:760px; min-width:0}
nav.toc{position:sticky; top:24px; align-self:start; font-family:var(--display); font-size:14px; max-height:calc(100vh - 48px); overflow:auto}
nav.toc h2{font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin:18px 0 6px; font-weight:700}
nav.toc ol{list-style:none; margin:0; padding:0; display:grid; gap:2px}
nav.toc a{display:flex; justify-content:space-between; gap:8px; color:var(--ink); text-decoration:none; padding:5px 8px; border-radius:6px; font-weight:500}
nav.toc a:hover, nav.toc a:focus-visible{background:var(--surface-2); outline:none}
nav.toc a.active{background:var(--accent-soft); color:var(--accent)}
nav.toc .chip{font-family:var(--mono); font-size:11px; color:var(--muted); white-space:nowrap}
nav.toc .chip.done{color:var(--good); font-weight:600}
@media (max-width:920px){
  .wrap{grid-template-columns:minmax(0,1fr); gap:24px; padding-block:24px 64px}
  nav.toc{position:static; max-height:none; background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:14px}
  nav.toc ol{grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}
}
```

Highlight the sidebar link of the section in view (IntersectionObserver adds `.active`).

## 5. Typography

```css
.eyebrow{font-family:var(--mono); font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted)}
h1{font-family:var(--display); font-weight:800; font-size:clamp(34px,5.4vw,50px); line-height:1.05; letter-spacing:-.02em; margin:10px 0 14px; text-wrap:balance}
.lede{font-size:19px; color:var(--muted); margin:0 0 22px; max-width:62ch}
header.hero{padding-bottom:28px; border-bottom:1px solid var(--line); margin-bottom:8px}
h2.part{font-family:var(--display); font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin:56px 0 0; font-weight:700}
section.sec{padding-top:28px; scroll-margin-top:16px}
h3{font-family:var(--display); font-weight:700; font-size:28px; line-height:1.15; margin:4px 0 14px; text-wrap:balance}
h3 .num{font-family:var(--mono); font-weight:400; font-size:15px; color:var(--muted); display:block; margin-bottom:4px}
h4{font-family:var(--display); font-size:17px; font-weight:700; margin:26px 0 8px}
p{margin:0 0 14px; max-width:68ch}
sub,sup{font-size:.72em; line-height:0}
code,.mono{font-family:var(--mono); font-size:.86em}
footer{margin-top:56px; padding-top:18px; border-top:1px solid var(--line); color:var(--muted); font-size:14px}
```

## 6. Equations and math (KaTeX)

All math is written in LaTeX and rendered by KaTeX. Nothing mathematical is hand-built with spans or shown in a monospace font.

```css
.eq{background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:12px 18px; margin:6px 0 18px}
.math{margin:8px 0 14px; overflow-x:auto; overflow-y:hidden}
.katex{font-size:1.12em; color:var(--ink)}
.katex-display{margin:.6em 0}
.eq .note{font-family:var(--display); font-size:13px; color:var(--muted)}
.eq .defs{font-size:15px; line-height:1.7; color:var(--muted); border-top:1px dashed var(--line); margin-top:10px; padding-top:8px}
```

Render once on load (and again after any content is injected, such as quizzes):

```js
function typeset(root){ renderMathInElement(root||document.body,{
  delimiters:[{left:"\\[",right:"\\]",display:true},{left:"\\(",right:"\\)",display:false}],
  throwOnError:false }); }
window.addEventListener("DOMContentLoaded",()=>typeset());
```

For demo readouts that change live, call `katex.render(tex, el, {displayMode:true, throwOnError:false})` on each update.

Key equation box:

```html
<div class="eq">
  <div class="math">\[ S = G\,e^{-2G} \]</div>
  <span class="note">throughput of pure ALOHA</span>
  <div class="defs">\(S\) = throughput, successful frames per frame time (no unit) · \(G\) = offered load, attempted frames per frame time (no unit)</div>
</div>
```

Derivation inside a worked example (prose between steps is normal body text):

```html
<p>Probabilities sum to 1:</p>
<div class="math">\[
\begin{aligned}
P_0\left(1+\rho+\rho^2+\cdots\right) &= P_0\cdot\frac{1}{1-\rho} = 1, \qquad 0<\rho<1\\
P_0 &= 1-\rho\\
P_n &= (1-\rho)\,\rho^{n}
\end{aligned}\]</div>
<p>The average number in the system, \(L\), is the mean of \(N\):</p>
<div class="math">\[
L = E(N) = \sum_{n=0}^{\infty} n(1-\rho)\rho^{n} = \frac{\rho}{1-\rho} = \frac{\lambda}{\mu-\lambda}
\]</div>
```

Rules: `\frac` for every fraction, `\dfrac` when a small fraction sits inside a larger expression and would be hard to read, `\sum_{lower}^{upper}` with limits shown, `\text{}` for units and words, `\mathbf{}` for the boxed final number, `aligned` for multi-step work. Keep each line short enough to fit a phone; split long chains across lines.

## 7. Callouts

```css
.callout{border-left:4px solid; border-radius:0 8px 8px 0; padding:12px 16px 4px; margin:18px 0}
.callout .tag{font-family:var(--display); font-weight:700; font-size:12px; letter-spacing:.1em; text-transform:uppercase; display:block; margin-bottom:4px}
.callout p{margin-bottom:10px} .callout ul{margin:0 0 10px; padding-left:20px} .callout li{margin-bottom:6px}
.analogy{background:var(--ana-bg); border-color:var(--ana-line)} .analogy .tag{color:var(--ana-ink)}
.tricky{background:var(--trk-bg); border-color:var(--trk-line)} .tricky .tag{color:var(--trk-ink)}
.filled{background:var(--fill-bg); border-color:var(--fill-line); font-size:15.5px} .filled .tag{color:var(--fill-ink)}
```

```html
<div class="callout analogy"><span class="tag">Analogy</span><p>...</p></div>
<div class="callout tricky"><span class="tag">Tricky bits</span><ul><li>...</li></ul></div>
<div class="callout filled"><span class="tag">Filled in</span><p>The lecture skips ... Added ...</p></div>
<div class="callout filled"><span class="tag">Possible lecture error</span><p>Lecture gives 12.4 V; recomputing gives 12.7 V because ...</p></div>
```

## 8. Big picture chain

```css
.chain{display:flex; flex-wrap:wrap; align-items:stretch; gap:8px; margin:12px 0 18px}
.blk{flex:1 1 118px; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-family:var(--display); font-size:14px; line-height:1.3}
.blk b{display:block; font-size:15px}
.blk span{color:var(--muted); font-size:12.5px; font-weight:500}
.blk .secs{display:block; font-family:var(--mono); font-size:11px; color:var(--accent); margin-top:6px}
.arrow{align-self:center; color:var(--muted); font-family:var(--mono)}
@media (max-width:560px){ .arrow{display:none} }
```

## 9. Tables

```css
.tbl{overflow-x:auto; margin:6px 0 18px; border:1px solid var(--line); border-radius:8px; background:var(--surface)}
table{border-collapse:collapse; width:100%; font-size:15px; font-variant-numeric:tabular-nums}
th,td{padding:9px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top}
th{font-family:var(--display); font-size:13px; font-weight:700; background:var(--surface-2)}
tr:last-child td{border-bottom:none}
td.num{text-align:right; font-family:var(--mono); font-size:13.5px}
.hlcol{background:var(--hl)}
```

## 10. Worked examples and practice problems

```css
details.work{background:var(--surface); border:1px solid var(--line); border-radius:8px; margin:12px 0 18px}
details.work summary{cursor:pointer; padding:12px 16px; font-family:var(--display); font-weight:700; font-size:15px; list-style:none}
details.work summary::-webkit-details-marker{display:none}
details.work summary::before{content:"+ "; font-family:var(--mono); color:var(--accent)}
details.work[open] summary::before{content:"− "}
details.work .body{padding:0 16px 8px}
details.work.practice summary{color:var(--muted)}
.givens{font-size:15.5px; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:8px 12px; margin-bottom:10px}
.answer{font-family:var(--display); font-weight:700; background:var(--good-bg); color:var(--good); border-radius:6px; padding:6px 10px; display:inline-block; margin:6px 0 12px}
```

Worked example summary: "Example N (lecture): [short title]". Practice summary: "Practice N.k (not from the lecture): [short title]". Body order: givens with units (inline math), then the steps as display math (`aligned`, one step per line) with short prose sentences between them, then `.answer` with units. Never a monospace step listing.

## 11. Demos and controls

```css
.demo{background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:14px; margin:14px 0 20px}
.demo .dtitle{font-family:var(--display); font-weight:700; font-size:14px; margin-bottom:8px}
.demo .src{font-family:var(--mono); font-size:11.5px; color:var(--muted)}
.demo canvas, .demo svg{width:100%; display:block}
.controls{display:flex; flex-wrap:wrap; gap:10px 22px; align-items:center; margin-top:10px; font-family:var(--display); font-size:14px}
.controls label{display:flex; align-items:center; gap:8px}
.controls input[type=range]{width:160px; accent-color:var(--accent)}
.controls input[type=number]{width:92px; font-family:var(--mono); font-size:13.5px; padding:5px 8px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--ink)}
.controls output{font-family:var(--mono); font-size:13px; min-width:44px}
.readout{font-family:var(--mono); font-size:13px; color:var(--muted); margin-top:10px; line-height:1.7}
.readout b{color:var(--ink); font-weight:600}
.btn{font-family:var(--display); font-weight:700; font-size:13px; border:1px solid var(--line); background:var(--surface-2); color:var(--ink); border-radius:6px; padding:6px 12px; cursor:pointer}
.btn:hover{border-color:var(--accent)}
.seg{display:inline-flex; border:1px solid var(--line); border-radius:7px; overflow:hidden}
.seg button{font-family:var(--display); font-weight:700; font-size:13px; border:0; background:var(--surface-2); color:var(--ink); padding:7px 12px; cursor:pointer}
.seg button + button{border-left:1px solid var(--line)}
.seg button[aria-pressed="true"]{background:var(--accent); color:var(--on-accent)}
.legend{display:flex; flex-wrap:wrap; gap:14px; font-family:var(--display); font-size:12.5px; color:var(--muted); margin-top:6px}
.legend i{display:inline-block; width:14px; height:3px; vertical-align:middle; margin-right:6px; border-radius:2px}
.verdict{display:inline-block; font-family:var(--display); font-weight:700; font-size:13px; padding:3px 10px; border-radius:99px}
.verdict.ok{background:var(--good-bg); color:var(--good)} .verdict.no{background:var(--bad-bg); color:var(--bad)}
*:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
```

Every demo has a `.dtitle`, a `.src` line ("Defaults: Example 3 from the lecture"), labelled controls with units, a `.readout` whose formulas and result are KaTeX-rendered, with units, and a `.btn` "Reset to lecture values". Use `--c1`, `--c2`, `--c3` for plotted series and `--grid` for gridlines, with a `.legend`. Canvases scale with `devicePixelRatio` and redraw on resize.

## 12. Quizzes

```css
.quiz{margin:26px 0 8px; border:1px solid var(--line); border-radius:12px; background:var(--surface); overflow:hidden}
.quiz-head{display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 16px; background:var(--accent-soft); flex-wrap:wrap}
.quiz-head .qt{font-family:var(--display); font-weight:800; font-size:15px}
.quiz-head .score{font-family:var(--mono); font-size:13px}
.qitem{padding:16px; border-top:1px solid var(--line)} .qitem:first-child{border-top:none}
.qq{font-weight:600; margin-bottom:10px}
.qq .qn{font-family:var(--mono); font-weight:400; color:var(--muted); margin-right:6px; font-size:14px}
.opts{display:grid; gap:8px}
.opt{display:flex; gap:10px; align-items:flex-start; text-align:left; width:100%; font-family:var(--body); font-size:16px; line-height:1.45; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:9px 12px; cursor:pointer}
.opt .L{font-family:var(--mono); font-size:13px; color:var(--muted); padding-top:2px}
.opt:hover:not([disabled]){border-color:var(--accent)}
.opt[disabled]{cursor:default}
.opt.right{background:var(--good-bg); border-color:var(--good)} .opt.right .L{color:var(--good); font-weight:600}
.opt.wrong{background:var(--bad-bg); border-color:var(--bad)} .opt.wrong .L{color:var(--bad); font-weight:600}
.expl{margin-top:10px; font-size:15.5px; padding:10px 12px; border-radius:8px; background:var(--surface-2)}
.expl b.ok{color:var(--good)} .expl b.no{color:var(--bad)}
.quiz-foot{display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; padding:12px 16px; border-top:1px solid var(--line); font-family:var(--display); font-size:14px; color:var(--muted)}
.final .quiz-head{background:var(--ink); color:var(--bg)} .final .quiz-head .score{color:var(--bg)}
.review{margin-top:16px} .review li{margin-bottom:10px}
```

Define quizzes as data in the script (question, options A to D, correct index, explanation, per-option mistake notes, review section) and render them, so storage and scoring share one source. Option text and explanations use inline KaTeX for any math; call `typeset()` after rendering. Options labelled A to D in `.L`. Head shows "Section N quiz" and "Score: x/y". Foot holds the "Reset" button. The final exam foot also holds the wrong-answer review list once all 12 are answered.

Explanation format: "**Correct.**" or "**Not quite.** You chose B, which comes from [mistake]." then the worked reasoning with units. Final exam explanations end with "Review: Section N" as a link.

## 13. Formula sheet and print

```css
.sheet{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px}
.sheet .card{background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px; break-inside:avoid}
.sheet .card h5{font-family:var(--display); font-size:13px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin:0 0 10px}
.sheet .f{padding:8px 0; border-top:1px solid var(--line); line-height:2.1} .sheet .f:first-of-type{border-top:none}
.sheet .f .expr{display:block; overflow-x:auto}
.sheet .f .d{font-size:13.5px; color:var(--muted); line-height:1.5; display:block}
.sheet .f .s{font-family:var(--mono); font-size:11px; color:var(--accent)}
@media print{
  body{background:#fff; color:#000; padding:0; font-size:12pt}
  nav.toc, .demo, .quiz, .btn, details.practice, header.hero .lede{display:none!important}
  .wrap{display:block; padding:0} main{max-width:none}
  .sheet .card{border:1px solid #999; background:#fff}
  .sheet .f .d, .sheet .f .s, .sheet .card h5{color:#333}
  body.print-sheet main > *:not(#formulas){display:none!important}
}
```

One card per part. Each `.f` holds one formula: `.expr` (display math with `\\[ \\]`), `.d` (every variable with unit), `.s` ("Section N"). "Print formula sheet" button adds `print-sheet` to body, calls `window.print()`, and removes the class on `afterprint`.

## 14. Behavior rules

- Storage key: `"guide:" + slug of the title`. Save `{quizId: {answers:[...]}}`. Restore on load, re-render answered questions as locked with explanations, update chips. Every `localStorage` access in try/catch; the page works without it.
- Chips show `x/y` once any question is answered, `.done` when all are answered.
- "Reset all progress" asks for confirmation, clears the key, and re-renders.
- Respect `prefers-reduced-motion` (no smooth scroll, no animated transitions).
- No horizontal page scroll at 360px width; wide equations and tables scroll inside their own box.
