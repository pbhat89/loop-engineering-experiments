"""Build the self-contained web version of the article (images embedded as data URIs).

    uv run python articles/loop-engineering-markdown-skills/build_html.py

Reads article.md next to this file, converts the small Markdown subset it uses (headings,
paragraphs, emphasis, links, inline code, fenced code, lists, blockquotes, pipe tables,
images with an italic caption line beneath) and writes article.html with the page design
inline. No external assets except Google Fonts; every colour is a theme token.
"""
from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "article.md"
OUT = HERE / "article.html"

CSS = """
:root{--bg:#f6f7f4;--surface:#fdfdfb;--ink:#1b2a24;--ink2:#5b6b65;--muted:#8a9791;--line:#dce2de;--accent:#00795c;--amber:#b87400;--code:#eef1ee;--shadow:0 1px 2px rgba(27,42,36,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#101715;--surface:#17211d;--ink:#e6ece8;--ink2:#9baaa3;--muted:#728079;--line:#26332d;--accent:#3fbf95;--amber:#e0a52e;--code:#1d2924;--shadow:none}}
:root[data-theme="dark"]{--bg:#101715;--surface:#17211d;--ink:#e6ece8;--ink2:#9baaa3;--muted:#728079;--line:#26332d;--accent:#3fbf95;--amber:#e0a52e;--code:#1d2924;--shadow:none}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.topbar{display:flex;justify-content:space-between;gap:16px;max-width:1040px;margin:0 auto;padding:18px 24px;font:500 12px/1.4 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2)}
article{max-width:760px;margin:0 auto;padding:24px 24px 80px}
h1{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:clamp(34px,5vw,50px);line-height:1.08;letter-spacing:-.01em;margin:8px 0 14px;text-wrap:balance;font-variation-settings:"opsz" 144}
h2{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:28px;line-height:1.2;margin:52px 0 14px;text-wrap:balance}
.subtitle{font-family:"Fraunces",Georgia,serif;font-style:italic;font-size:21px;line-height:1.35;color:var(--ink2);margin:0 0 28px}
p{margin:0 0 18px}
p+p{margin-top:-2px}
strong{font-weight:600}
code{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;background:var(--code);padding:.1em .35em;border-radius:4px}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:16px 18px;overflow-x:auto;margin:0 0 22px;font-size:13.5px;line-height:1.55}
pre code{background:none;padding:0;font-size:inherit}
ul,ol{margin:0 0 20px;padding-left:26px}
li{margin:0 0 8px}
li>p{margin:0}
blockquote{margin:24px 0;padding:12px 20px;border-left:3px solid var(--amber);background:var(--surface);color:var(--ink);font-size:16.5px}
blockquote p{margin:0}
blockquote.pull{border-left-color:var(--accent);font-family:"Fraunces",Georgia,serif;font-style:italic;font-size:22px;line-height:1.35;background:none;padding:6px 0 6px 20px}
figure{margin:30px calc(50% - min(50vw - 24px, 470px)) 30px;max-width:940px}
figure img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff;box-shadow:var(--shadow)}
figure.hero img{border:none}
figcaption{margin-top:8px;font:13px/1.45 "IBM Plex Mono",ui-monospace,monospace;color:var(--muted)}
.tablewrap{overflow-x:auto;margin:0 0 24px}
table{border-collapse:collapse;width:100%;font-size:15px;font-variant-numeric:tabular-nums}
th{font:600 12px/1.4 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
td:not(:first-child),th:not(:first-child){text-align:right;white-space:nowrap}
tr:last-child td{border-bottom:none}
.endcard{margin-top:56px;padding:22px 24px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
.endcard h2{margin:0 0 10px;font-size:22px}
.endcard p{margin:0 0 8px}
.foot{max-width:760px;margin:0 auto;padding:0 24px 48px;font:12px/1.5 "IBM Plex Mono",ui-monospace,monospace;color:var(--muted)}
@media (prefers-reduced-motion:no-preference){a{transition:color .15s}}
@media (max-width:700px){body{font-size:16px}h2{font-size:24px}figure{margin-left:0;margin-right:0}}
"""

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITAL = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
IMG = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
BARE_URL = re.compile(r"(?<![\"(>])(https?://[^\s<)]+)")


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def inline(text: str) -> str:
    """Escape, then apply inline code, bold, italic, links and bare URLs."""
    parts = INLINE_CODE.split(text)  # odd indices are code spans
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f"<code>{html.escape(part)}</code>")
            continue
        s = html.escape(part, quote=False)
        s = LINK.sub(lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', s)
        s = BARE_URL.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', s)
        s = BOLD.sub(r"<strong>\1</strong>", s)
        s = ITAL.sub(r"<em>\1</em>", s)
        out.append(s)
    return "".join(out)


def convert(md: str) -> tuple[str, str, str]:
    """Return (title, subtitle, body_html)."""
    md = re.sub(r"<!--.*?-->\s*", "", md, count=1, flags=re.S)
    lines = md.splitlines()
    body: list[str] = []
    title, subtitle = "", ""
    i = 0
    first_fig = True
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            j = i + 1
            code: list[str] = []
            while j < len(lines) and not lines[j].startswith("```"):
                code.append(lines[j])
                j += 1
            body.append(f'<pre><code class="language-{html.escape(lang)}">{html.escape(chr(10).join(code))}</code></pre>')
            i = j + 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            body.append(f"<h1>{inline(title)}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            body.append(f"<h2>{inline(line[3:].strip())}</h2>")
            i += 1
            continue
        m = IMG.match(line)
        if m:
            caption = ""
            if i + 1 < len(lines) and lines[i + 1].startswith("*") and lines[i + 1].endswith("*"):
                caption = lines[i + 1].strip("*")
                i += 1
            src = HERE / m.group(2)
            cls = ' class="hero"' if first_fig else ""
            first_fig = False
            body.append(f'<figure{cls}><img src="{data_uri(src)}" alt="{html.escape(m.group(1))}"><figcaption>{inline(caption)}</figcaption></figure>')
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            header, data = rows[0], [r for r in rows[2:]] if len(rows) > 2 and set("".join(rows[1])) <= set("-:| ") else rows[1:]
            thead = "".join(f"<th>{inline(c)}</th>" for c in header)
            tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in data)
            body.append(f'<div class="tablewrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
            continue
        if line.startswith("> "):
            quote: list[str] = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:])
                i += 1
            text = " ".join(quote)
            cls = ' class="pull"' if not text.startswith("**") else ""
            body.append(f"<blockquote{cls}><p>{inline(text)}</p></blockquote>")
            continue
        if re.match(r"^(\d+)\. ", line) or line.startswith("- "):
            ordered = not line.startswith("- ")
            items: list[str] = []
            while i < len(lines) and (re.match(r"^(\d+)\. ", lines[i]) or lines[i].startswith("- ")):
                item = re.sub(r"^(\d+\. |- )", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    item += " " + lines[i].strip()
                    i += 1
                items.append(f"<li>{inline(item)}</li>")
            tag = "ol" if ordered else "ul"
            body.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue
        # subtitle: first italic-only line right after the title
        if line.startswith("*") and line.endswith("*") and title and not subtitle:
            subtitle = line.strip("*")
            body.append(f'<p class="subtitle">{inline(subtitle)}</p>')
            i += 1
            continue
        para: list[str] = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|```|\||> |- |\d+\. |!\[)", lines[i]):
            para.append(lines[i])
            i += 1
        body.append(f"<p>{inline(' '.join(para))}</p>")
    return title, subtitle, "\n".join(body)


def main() -> int:
    title, subtitle, body = convert(SRC.read_text(encoding="utf-8"))
    words = len(re.sub(r"```.*?```", "", SRC.read_text(encoding="utf-8"), flags=re.S).split())
    page = f"""<title>Teaching a Claims Agent the House Rules</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="topbar"><span>claims-skill-loop · experiment notes</span><span>{words // 230 + 1} min read · synthetic data</span></div>
<article>
{body}
</article>
<div class="foot">Figures are generated from the run's JSONL logs by <code>assets/make_figures.py</code>; every number in the text traces to <code>docs/writeup.md</code>'s evidence index. Synthetic data; illustrative single runs; not evidence of anything operational.</div>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.name}: {OUT.stat().st_size / 1024:.0f} KB, title={title!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
