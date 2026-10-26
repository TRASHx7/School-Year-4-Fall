#!/usr/bin/env python3
"""Assemble a study guide from a work folder.

Usage: python build_guide.py <work_dir> [out.html]

<work_dir> must contain:
  guide.json    {"title","eyebrow","lede","parts":[{"name","sections":[{"id":"s1","title":"..."}]}]}
  content.html  everything inside <main> after the hero: #big, part headings, sections,
                #final and #formulas. Quizzes are empty placeholders: <div class="quiz" data-quiz="q1"></div>
  quizzes.json  {"q1":{"title":"Section 1 quiz","questions":[{"q","options":[4],"answer":0-3,
                 "explain","mistakes":[4, null for the correct one],"review":"s1"}]}, "final":{...}}
  demos.js      optional; define window.initDemos = function(){...}
The sidebar, hero, CSS, KaTeX setup and quiz engine come from the skill's assets.
"""
import json, sys, html, pathlib
here = pathlib.Path(__file__).resolve().parent.parent / "assets"
work = pathlib.Path(sys.argv[1])
g = json.loads((work/"guide.json").read_text())
quizzes = json.loads((work/"quizzes.json").read_text())
content = (work/"content.html").read_text()
demos = (work/"demos.js").read_text() if (work/"demos.js").exists() else ""

nav = ['<nav class="toc" aria-label="Contents">', '<button class="btn" id="resetAll" type="button">Reset all progress</button>',
       '<h2>Start</h2><ol><li><a href="#big">Big picture</a></li></ol>']
n = 0
for i, p in enumerate(g["parts"], 1):
    nav.append(f'<h2>Part {i} · {html.escape(p["name"])}</h2><ol>')
    for s in p["sections"]:
        n += 1
        qid = s.get("quiz", "q%d" % n)
        chip = f' <span class="chip" data-chip="{qid}"></span>' if qid in quizzes else ""
        nav.append(f'<li><a href="#{s["id"]}">{n} {s["title"]}{chip}</a></li>')
    nav.append('</ol>')
nav.append('<h2>Finish</h2><ol><li><a href="#final">Final exam <span class="chip" data-chip="final"></span></a></li>')
nav.append('<li><a href="#formulas">Formula sheet</a></li></ol></nav>')

hero = (f'<header class="hero"><div class="eyebrow">{g.get("eyebrow","Study guide")}</div>'
        f'<h1>{g["title"]}</h1><p class="lede">{g.get("lede","")}</p></header>')
head = (here/"head.html").read_text().replace("{{TITLE}}", html.escape(g["title"])).replace("{{CSS}}", (here/"guide.css").read_text())
data = json.dumps({"title": g["title"], "quizzes": quizzes}, ensure_ascii=False).replace("</", "<\\/")
page = (head + '<div class="wrap">' + "\n".join(nav) + '<main>' + hero + content +
        '<footer>Study guide generated from the lecture. Check flagged notes against your class materials.</footer></main></div>\n'
        '<script>window.GUIDE=' + data + ';</script>\n<script>\n' + demos + '\n</script>\n<script>\n' +
        (here/"engine.js").read_text() + '\n</script>\n</body></html>\n')
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else work/"guide.html"
out.write_text(page)
print(f"built {out} ({len(page)//1024} KB, {n} sections, {len(quizzes)} quizzes)")
