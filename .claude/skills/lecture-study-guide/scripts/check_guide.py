#!/usr/bin/env python3
"""Automated checks for a study guide work folder (run before publishing).

Usage: python check_guide.py <work_dir>

Checks structure, quiz data, math notation and (when Node is available) that every
math expression renders in KaTeX and demos.js parses. Prints ERROR lines that must be
fixed and WARN lines to review. Exit code 1 if any ERROR.
Numbers are NOT checked here: write and run a per-guide numbers script for that (SKILL.md Step 8).
"""
import json, re, sys, pathlib, shutil, subprocess, os

work = pathlib.Path(sys.argv[1])
g = json.loads((work/"guide.json").read_text())
Q = json.loads((work/"quizzes.json").read_text())
C = (work/"content.html").read_text()
errors, warns = [], []
E = errors.append; W = warns.append

# ---------- structure ----------
sections = [s for p in g["parts"] for s in p["sections"]]
ids = set(re.findall(r'id="([^"]+)"', C))
for k in ("big", "final", "formulas"):
    if k not in ids: E(f'content.html has no section with id="{k}"')
for n, s in enumerate(sections, 1):
    m = re.search(r'<section[^>]*id="%s"[^>]*>(.*?)</section>' % re.escape(s["id"]), C, re.S)
    if not m: E(f'section {n} id="{s["id"]}" missing from content.html'); continue
    body = m.group(1)
    for cls, name in (("callout analogy", "Analogy box"), ("callout tricky", "Tricky bits box")):
        if cls not in body: E(f"section {n}: no {name}")
    if 'data-quiz=' not in body: E(f"section {n}: no quiz placeholder")
    if 'practice' not in body: W(f"section {n}: no practice problems found")
    if 'class="eq"' not in body: W(f"section {n}: no key equation box")

# ---------- quizzes ----------
placeholders = re.findall(r'data-quiz="([^"]+)"', C)
for p in placeholders:
    if p not in Q: E(f'quiz placeholder "{p}" has no data in quizzes.json')
for k in Q:
    if k not in placeholders: E(f'quizzes.json "{k}" is never placed in content.html')
for k, quiz in Q.items():
    qs = quiz.get("questions", [])
    if k == "final":
        if len(qs) != 12: E(f"final exam has {len(qs)} questions, needs 12")
    elif not 3 <= len(qs) <= 5: E(f"{k}: {len(qs)} questions, needs 3 to 5")
    for i, q in enumerate(qs, 1):
        t = f"{k} Q{i}"
        o = q.get("options", [])
        if len(o) != 4: E(f"{t}: {len(o)} options, needs 4")
        if len(set(map(str.strip, o))) != len(o): E(f"{t}: duplicate options")
        a = q.get("answer")
        if not isinstance(a, int) or not 0 <= a < len(o): E(f"{t}: answer index invalid"); continue
        if not q.get("explain"): E(f"{t}: no explanation")
        mk = q.get("mistakes") or []
        for j in range(len(o)):
            if j != a and (j >= len(mk) or not mk[j]): W(f"{t}: option {'ABCD'[j]} has no mistake note")
        if k == "final":
            if not q.get("review"): E(f"{t}: final exam question has no review section")
            elif q["review"] not in ids: E(f'{t}: review "{q["review"]}" is not a section id')

# ---------- math ----------
texts = [("content", C)] + [(f"{k} Q{i}", json.dumps(q, ensure_ascii=False)) for k, v in Q.items() for i, q in enumerate(v["questions"], 1)]
def unjson(s): return s.replace("\\\\", "\\")
maths = []
for where, t in texts:
    t2 = unjson(t) if where != "content" else t
    if t2.count("\\[") != t2.count("\\]"): E(f"{where}: unbalanced \\[ \\]")
    if t2.count("\\(") != t2.count("\\)"): E(f"{where}: unbalanced \\( \\)")
    for d_expr, i_expr in re.findall(r"\\\[(.*?)\\\]|\\\((.*?)\\\)", t2, re.S):
        disp, expr = (1, d_expr) if d_expr else (0, i_expr)
        maths.append((where, disp, expr))
        bare = re.sub(r"\\text\{[^}]*\}", "", expr)
        if re.search(r"[\w\)\}]\s*/\s*[\w\(\\{]", bare): E(f"{where}: slash fraction in math: {expr.strip()[:70]}")
for m in re.finditer(r"<(pre|code)[^>]*>(.*?)</\1>", C, re.S):
    if re.search(r"[=\\^_]|\d\s*[+\-×·]", m.group(2)): E(f"math-like text inside <{m.group(1)}>: {m.group(2)[:60]}")
# slash fractions outside math, in visible text (skip tags, urls, units like m/s)
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>|\\\[.*?\\\]|\\\(.*?\\\)|https?://\S+", " ", C, flags=re.S)
for m in re.finditer(r"(?<![\w/])([A-Za-z0-9α-ωΑ-Ω\)]{1,6})\s*/\s*\(?([A-Za-z0-9α-ωΑ-Ω]{1,6})", vis):
    if not re.fullmatch(r"(and|or|and/or)", m.group(0).replace(" ", "")) and not re.fullmatch(r"[a-zA-Zµ]{1,3}/[a-zA-Z]{1,3}", m.group(0).replace(" ", "")):
        W(f"possible slash fraction outside math: '{m.group(0)}'")
if re.search(r"\\(frac|sum|alpha|rho|lambda|mu)\b", vis): E("LaTeX commands found outside \\( \\) or \\[ \\] delimiters")

# ---------- KaTeX render + JS syntax (needs Node) ----------
node = shutil.which("node")
if node:
    cache = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home()/".cache"))/"lsg-katex"
    if not (cache/"node_modules"/"katex").exists():
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "i", "--silent", "--prefix", str(cache), "katex@0.16.9"], capture_output=True)
    if (cache/"node_modules"/"katex").exists():
        js = ("const k=require(process.argv[1]);const d=JSON.parse(require('fs').readFileSync(0,'utf8'));"
              "for(const [w,disp,e] of d){try{k.renderToString(e,{displayMode:!!disp,throwOnError:true})}"
              "catch(x){console.log(w+': '+String(x.message).slice(0,140))}}")
        r = subprocess.run([node, "-e", js, str(cache/"node_modules"/"katex")], input=json.dumps(maths), capture_output=True, text=True)
        for line in r.stdout.strip().splitlines(): E("KaTeX: " + line)
    else: W("could not install KaTeX; math render check skipped")
    if (work/"demos.js").exists():
        r = subprocess.run([node, "--check", str(work/"demos.js")], capture_output=True, text=True)
        if r.returncode: E("demos.js syntax: " + r.stderr.strip().splitlines()[-1][:160])
else: W("Node not found; KaTeX render and demos.js syntax checks skipped")

print(f"{len(sections)} sections, {len(Q)} quizzes, {len(maths)} math expressions checked")
for e in errors: print("ERROR", e)
for w in warns[:40]: print("WARN ", w)
if len(warns) > 40: print(f"WARN  ... {len(warns)-40} more")
print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
sys.exit(1 if errors else 0)
