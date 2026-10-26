---
name: "lecture-study-guide"
description: Turn one or more lectures (slides, notes, PDFs, textbook chapters) from any course, attached or pulled from a GitHub repo, local folder or cloud drive, into an interactive HTML study guide with sections, analogies, demos, quizzes, a final exam and a formula sheet. Use only when the user explicitly invokes /lecture-study-guide or asks for this skill by name. Do not use automatically for general studying or tutoring requests.
---

# Lecture Study Guide

Build a self-contained, interactive HTML study guide for each lecture the user picks, teaching it to someone who has never read it. The guide replaces the lecture: a reader should be able to learn the topic, solve the lecture's problems, and pass an exam using only this page.

Works for any course (engineering, physics, math, chemistry, economics, biology, and so on). Adapt the demos and examples to the subject, but keep the structure and style below fixed so every guide feels like part of the same set.

## Step 0: Find the lectures

Lectures can come from any of these places. Work out which one from what the user says, checking in this order:

1. **Attached files** in the conversation.
2. **A GitHub repo.** If the user names a repo (`owner/repo`, a github.com URL, or "my lectures repo"), attach it with the `add_repo` tool (read access is enough), clone it, and look for lecture files (`.pdf`, `.pptx`, `.docx`, `.md`, `.tex`, `.txt`, `.ipynb`). If they don't name the repo, ask once for `owner/repo`. Do not pre-check the repo with curl or `gh`; call `add_repo` directly and relay its error if access is denied (usually the fix is reconnecting GitHub in claude.ai Settings, Connectors).
3. **A local folder** on the user's computer, through the device bridge or device shell tools when the conversation is linked to the desktop app. If those tools are missing, tell the user to open this chat in the Claude desktop app, or to attach the files instead.
4. **A cloud drive** (Google Drive, or another connected storage app). Search it with the connector; if none is connected, say which connection would help.

If no lecture can be found in any of these, stop and ask the user to attach one or point to where it lives. Do not build a guide from memory, from a course title, or from a guess about what the lecture covers. A guide built on assumed content would teach notation, numbers and examples that differ from the user's course, which is worse than no guide.

If a file is unreadable (scanned images with no text, corrupted, password protected), say so and skip it rather than guessing its contents.

## Step 0.5: Pick the lectures (one or many)

The user may ask for one lecture or several at once ("lectures 5 to 8", "everything in /ece457/week3", "all of them").

- When a source holds more than one lecture and the request doesn't make the selection obvious, list what you found (file name, path, page count or slide count, and the lecture title if readable) and ask which ones to build, with "all" as an option. Ask this once, using AskUserQuestion when available.
- Treat a folder of files for one lecture (for example slides plus a separate examples PDF) as **one** lecture. Treat clearly separate lectures as separate guides.
- Skip anything already built unless the user asks to rebuild: check their artifacts for a guide with the same title.

### Running several lectures

- Create a task list with one item per lecture so progress is visible if the user steps away.
- Build each guide fully (Steps 1 to 9) before starting the next, one artifact per lecture. Finish and verify each one completely; never cut sections, quizzes or checks to fit more lectures in.
- If subagents are available and there are more than three lectures, you may hand each lecture to its own subagent, passing it this skill's path and the lecture's file path, then review each result against the Step 8 checks yourself before publishing.
- Keep titles consistent so the set reads as a series: `[Course] L[number]: [Topic]` when a number is known.
- If one lecture fails (unreadable, missing pages), note it and carry on with the rest.
- After the last guide, publish a small **course index** artifact in the same style: one card per guide with its title, a one-line summary, the number of sections, and a link. If an index for this course already exists, update it instead of making a new one.

## Step 1: Read the whole lecture and extract

Read every page before writing. Build a working list of:

- The lecture's order of topics, which becomes the section order.
- Every worked example, with all given values, units, notation and final answers exactly as the lecture states them.
- Every equation, and every variable with its meaning and unit.
- Gaps: skipped algebra steps, undefined variables, missing units, results stated without derivation, and anything that looks like a typo or arithmetic error.

## Step 2: Plan the structure

- Group the lecture into **parts** (2 to 5, by theme), each containing **numbered sections** (numbering runs continuously through the whole guide: 1, 2, 3, ...) that follow the lecture's order.
- Scale the number of sections to the lecture. Do not pad short lectures or merge unrelated topics in long ones.
- Decide where an interactive demo genuinely helps understanding (see Step 4).

## Step 3: Write the content

### Big picture intro

Open with a hero header (course eyebrow, title, one-paragraph lede) followed by a **Big picture** block: a short explanation of what problem the lecture solves and how the parts connect, shown as a row of linked blocks (one per part, each naming its sections) with arrows between them. The reader should know where they are going before section 1.

### Each section contains, in this order

1. **Short explanation** in plain language. Teach the idea, not the lecture's wording. Skip detail that doesn't help the reader understand or solve problems.
2. **Key equations** in an equation box. Directly under or beside each equation, define every symbol that appears in it for the first time, with its unit (for example: "V<sub>s</sub> = supply voltage, in volts (V)"). Never introduce a variable without defining it, including in worked examples, demos and quizzes.
3. **Worked examples** from the lecture, in expandable panels. Include every example the lecture has, every step, the lecture's notation and the lecture's numbers. State the givens with units, show each substitution, and give the answer with units. If you filled a gap in a step, mark it (see Gaps below).
4. **Analogy** box: one everyday analogy that makes the idea intuitive, plus one sentence on where the analogy breaks down if that matters.
5. **Tricky bits** box: what students commonly confuse or get wrong on exams (sign conventions, peak vs RMS, degrees vs radians, which value to plug in, unit conversions, special cases).
6. **Interactive demo**, where one helps.
7. **Practice problems**: 2 or 3 new problems not in the lecture, using the same method with different numbers or a slightly different twist. Hide each solution in an expandable panel with full steps and units. Label them "Practice (not from the lecture)".
8. **Section quiz** (see Step 5).

### Math notation

All math must look like it does in a textbook, never like code. Render every equation, worked example step and derivation with **KaTeX** (setup in `references/style-guide.md`, section 6).

- **Never put math in a monospace font or a code-style box.** No `<pre>`, no `<code>`, no `.steps`-style listings for equations. Monospace is only for small UI labels like score chips.
- **Fractions are always stacked**: `\frac{\lambda}{\mu}`, `\frac{dS}{dG}`, `\frac{1}{1-\rho}`. A slash between two quantities (λ/μ, dS/dG, 1/(1 − ρ)) is never acceptable, including in quiz options and demo readouts.
- **Exponents are raised and sized properly**: `Ge^{-2G}`, `\rho^{n}P_0`. Sums and products show their limits under and over the symbol in display math: `\sum_{n=0}^{\infty}`.
- **Derivations and worked examples are display math, one step per line**, aligned on the equals sign with `\begin{aligned}...\end{aligned}`. Explanatory sentences between steps are normal prose paragraphs in the body font, not muted code comments. A step never runs off the side of the page; break long lines instead of relying on horizontal scrolling.
- Short references inside a sentence use inline math (`\(\rho\)`), still with stacked fractions when a fraction appears.
- Units are upright text inside math: `0.184\ \text{(18.4\%)}`, `5\ \text{V}`.

What this looks like for a derivation:

```html
<p>Set the derivative to zero to find the peak:</p>
<div class="math">\[
\begin{aligned}
\frac{dS}{dG} &= e^{-2G}\,(1-2G) = 0 \\
G &= 0.5 \\
S_{\max} &= 0.5\,e^{-1} = \mathbf{0.184}\ \text{(18.4\%)}
\end{aligned}
\]</div>
<p>Probabilities sum to 1, so</p>
<div class="math">\[
P_0\sum_{n=0}^{\infty}\rho^{n} = P_0\cdot\frac{1}{1-\rho} = 1
\quad\Longrightarrow\quad P_0 = 1-\rho,\qquad P_n=(1-\rho)\,\rho^{n}
\]</div>
```

### Units

Every given value, intermediate result and final answer carries its unit, in worked examples, practice problems, demo readouts, quiz options and explanations. Unitless quantities are labelled as such ("ratio, no unit"). Use standard SI prefixes and symbols.

### Gaps in the lecture

When the lecture skips a step, leaves a variable undefined, omits a unit, or appears to contain an error, fill the gap so the guide is complete and correct, and point it out with a small **"Filled in"** note (or **"Possible lecture error"** if the lecture's value looks wrong) saying what was added or corrected and why. Keep the lecture's original number visible next to the correction so the reader can match it against class materials. Never silently change a lecture result.

## Step 4: Interactive demos and calculators

Add a demo wherever manipulating something builds intuition or lets the reader check an answer: sliders, toggles, clickable circuits or diagrams, live waveforms, spectra, graphs, step-through calculators. Choose demos that fit the subject (a supply and demand graph for economics, a projectile path for physics, a titration curve for chemistry).

- Calculators load with the **lecture's example numbers already filled in**, so the readout reproduces the lecture's answer on first view. Label which example the defaults come from.
- Show the calculation steps in the readout as typeset math (render with `katex.render`), with units, not just the final number.
- Every slider and input shows its variable name and unit.
- Draw with canvas or SVG using the theme colors so it works in dark mode. Resize correctly on phones.

## Step 5: Quizzes and final exam

**Section quizzes**: 3 to 5 multiple-choice questions after every section, mostly calculations and "why" questions, few pure definitions.

**Final exam**: 12 questions covering the whole lecture, mixing calculations from different parts. Each explanation ends with "Review: Section N" naming the section to revisit.

For every question:

- 4 options. **Wrong options are plausible**: each one is the result of a real, specific mistake (forgot to square, used peak instead of RMS, dropped a factor of 2, wrong unit conversion, sign flipped, used diameter instead of radius). Do not use obviously absurd distractors.
- The explanation, shown after answering, works through the correct answer with units and, when the reader picks a wrong option, names the mistake that produces that option.
- Clicking an option locks the question, marks right and wrong, and shows the explanation.

**Interactions**:

- A **Reset** button on each quiz clears its answers.
- After the final exam is complete, show a **"Review my wrong answers"** list: each missed question, the reader's answer, the correct answer, and the section to review, with links.
- **Sidebar scores**: each section entry in the table of contents shows its quiz score chip (for example "3/4"), turning green when complete. The final exam gets its own entry and chip.
- **Saved progress**: store quiz answers and scores in `localStorage` under a key unique to this guide (derived from the title), so scores and answered questions are restored on return. Wrap every read and write in try/catch so the page works when storage is blocked. Include a "Reset all progress" button near the top of the sidebar.

## Step 6: Formula sheet

End with a formula sheet: cards grouped by part, each formula typeset with stacked fractions and proper notation, one formula per line, each followed by its variable definitions with units and the section number it comes from. Give it generous spacing; nothing crammed together or squeezed onto one line.

Add print styles (`@media print`) so the formula sheet prints cleanly on one or two pages: hide the sidebar, demos, quizzes and buttons when printing, use black on white, avoid breaking a card across pages. Include a "Print formula sheet" button that prints only the formula sheet.

## Step 7: Style

Follow `references/style-guide.md` exactly for layout, colors, fonts, components and dark mode. Read it before writing any HTML. It defines the look shared by all of the user's guides.

## Step 8: Verify before publishing

Do not publish until every check passes. Run these in code (Python or Node), not by eye:

1. **Worked examples**: recompute every lecture example from its givens. Confirm the guide's steps and final answers match the lecture (or the flagged correction).
2. **Demo defaults**: for each calculator, run its formula with the default inputs and confirm the output equals the lecture's answer to the displayed precision.
3. **Quiz answers**: for every calculation question, compute the correct answer and confirm the marked correct option matches it. Compute each distractor from its stated mistake and confirm it differs from the correct answer and from the other options.
4. **Practice problems**: recompute each solution.
5. **Units**: confirm every number in examples, readouts, options and explanations has a unit or is labelled unitless.
6. **Variables**: confirm every symbol is defined at or before its first use.
7. **Notation**: search the HTML for slash fractions in math (a digit, letter or closing bracket, then "/", then a digit, letter, Greek letter or opening bracket, outside URLs and code) and replace them with `\frac`. Confirm no equation sits inside `<pre>`, `<code>` or a monospace element, and that every math block renders without KaTeX errors.
8. **Page checks**: the page loads without console errors, the quizzes record and restore scores, the sidebar chips update, the layout works at phone width, and dark mode is readable.

Fix anything that fails and rerun the checks.

## Step 9: Publish and report

Publish each guide as its own HTML artifact (load the `artifact-design` skill first if the session has it). If the lectures came from a repo or folder and the user asked for the guides to be saved there too, also write each HTML file into a `study-guides/` folder next to the lectures (commit and push only if they asked for that).

Then reply briefly with:

- One line per guide saying what it covers (parts and sections). For a batch, a short table: lecture, guide, sections, notes.
- Any **Filled in** or **Possible lecture error** notes, grouped by lecture, so the user can check them against their class.
- Any lectures that were skipped and why.
- Suggestions: anything that would make the guides more useful (for example, a topic a lecture references but doesn't explain, or a demo that needs data the lecture doesn't give).
