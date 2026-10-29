#!/usr/bin/env python3
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
DOCS = ROOT / "docs"
SITE = ROOT / "site"

COMMAND_LANGS = {"bash", "sh", "shell", "powershell", "pwsh", "cmd"}
REQUIRED_H2 = [
    "この章のゴール",
    "前提",
    "手を動かす",
    "何が起きたか",
    "壊してみる",
    "確認テスト",
    "まとめ",
    "片付け",
]
FORBIDDEN_HEADINGS = [
    "確認したバージョン",
    "たとえ話",
]
FORBIDDEN_TEXT = ["楓真", "最初の読者"]
COMMAND_PHRASES = ["何をするコマンドか", "期待する出力", "出力が違うとき"]
# 出力例（```text）に書いてよいURLのホスト。著者のパソコンだけが持つ配布元は入れない。
ALLOWED_OUTPUT_HOSTS = frozenset({
    "127.0.0.1",
    "archive.ubuntu.com",
    "bugs.launchpad.net",
    "docs.docker.com",
    "download.docker.com",
    "help.ubuntu.com",
    "hub.docker.com",
    "localhost",
    "pip.pypa.io",
    "security.ubuntu.com",
    "ubuntu.com",
    "www.ubuntu.com",
})
OUTPUT_URL_RE = re.compile(r"https?://[^\s\"'`<>)]+", re.IGNORECASE)
# 1段落に置ける外部リンクの本数。出典を1文へ詰め込まないため。
# 既存の章で一番多い段落は2本なので、3本以上を失敗にする。
MAX_EXTERNAL_LINKS_PER_PARAGRAPH = 2
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class BuildError(Exception):
    pass


def load_outline():
    data = json.loads((BOOK / "outline.json").read_text(encoding="utf-8"))
    part_titles = {part["id"]: part["title"] for part in data["parts"]}
    return part_titles, data["chapters"]


def split_front_matter(text, path):
    if not text.startswith("---\n"):
        raise BuildError(f"{path}: front matter がありません")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise BuildError(f"{path}: front matter が閉じていません")
    raw = text[4:end]
    body = text[end + 5 :]
    meta = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise BuildError(f"{path}: front matter の行を読めません: {line}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta, body


def parse_blocks(text, path):
    lines = text.splitlines()
    return parse_range(lines, 0, len(lines), path)[0]


def parse_range(lines, start, end, path):
    blocks = []
    i = start
    while i < end:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block, i = parse_fence(lines, i, path)
            blocks.append(block)
            continue
        if line.strip().startswith(":::"):
            block, i = parse_directive(lines, i, path)
            blocks.append(block)
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level > 3:
                raise BuildError(f"{path}: 見出しは h3 までです: {line}")
            blocks.append({"type": "heading", "level": level, "text": line[level:].strip()})
            i += 1
            continue
        if line.startswith("|"):
            block, i = parse_table(lines, i, path)
            blocks.append(block)
            continue
        if re.match(r"\d+\. ", line):
            items = []
            start = int(re.match(r"(\d+)\. ", line).group(1))
            while i < end and re.match(r"\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            blocks.append({"type": "ol", "items": items, "start": start})
            continue
        if line.startswith("- "):
            items = []
            while i < end and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue
        if line.startswith("> "):
            quoted = []
            while i < end and lines[i].startswith("> "):
                quoted.append(lines[i][2:])
                i += 1
            blocks.append({"type": "quote", "text": " ".join(quoted)})
            continue
        para = [line]
        i += 1
        while i < end and lines[i].strip() and not starts_block(lines[i]):
            para.append(lines[i])
            i += 1
        blocks.append({"type": "p", "text": " ".join(para)})
    return blocks, i


def starts_block(line):
    return (
        line.startswith("```")
        or line.strip().startswith(":::")
        or line.startswith("#")
        or line.startswith("|")
        or line.startswith("- ")
        or line.startswith("> ")
        or bool(re.match(r"\d+\. ", line))
    )


def parse_fence(lines, i, path):
    info = lines[i][3:].strip()
    lang = info.split()[0] if info else ""
    file_path = None
    for part in info.split()[1:]:
        if part.startswith("file="):
            file_path = part[5:]
    buf = []
    i += 1
    while i < len(lines) and not lines[i].startswith("```"):
        buf.append(lines[i])
        i += 1
    if i >= len(lines):
        raise BuildError(f"{path}: コードブロックが閉じていません")
    body = "\n".join(buf)
    if lang in COMMAND_LANGS and re.search(r"(?m)^\s*(?:\.\.\.|…)\s*$", body):
        raise BuildError(f"{path}: コマンドを省略記号で省かないでください")
    return {"type": "code", "lang": lang, "file": file_path, "body": body}, i + 1


def capture_directive(lines, i, path):
    buf = []
    in_code = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            in_code = not in_code
            buf.append(line)
            i += 1
            continue
        if not in_code and line.strip() == ":::":
            return "\n".join(buf), i + 1
        buf.append(line)
        i += 1
    raise BuildError(f"{path}: ::: が閉じていません")


def parse_directive(lines, i, path):
    kind = lines[i].strip()[3:].strip()
    if kind == "windows":
        windows, i = capture_directive(lines, i + 1, path)
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or lines[i].strip() != ":::linux":
            raise BuildError(f"{path}: Windows タブの直後に Linux タブがありません")
        linux, i = capture_directive(lines, i + 1, path)
        return {
            "type": "tabs",
            "windows": parse_blocks(windows, path),
            "linux": parse_blocks(linux, path),
        }, i
    if kind in {"warn", "svg"}:
        body, i = capture_directive(lines, i + 1, path)
        return {"type": kind, "body": body}, i
    if kind == "quiz":
        body, i = capture_directive(lines, i + 1, path)
        parts = {"q": [], "a": [], "e": []}
        mode = "q"
        for line in body.splitlines():
            if line.strip() == ":::answer":
                mode = "a"
                continue
            if line.strip() == ":::explain":
                mode = "e"
                continue
            parts[mode].append(line)
        if not "\n".join(parts["q"]).strip() or not "\n".join(parts["a"]).strip() or not "\n".join(parts["e"]).strip():
            raise BuildError(f"{path}: 確認テストには問題、:::answer、:::explain が必要です")
        return {
            "type": "quiz",
            "question": parse_blocks("\n".join(parts["q"]), path),
            "answer": parse_blocks("\n".join(parts["a"]), path),
            "explain": parse_blocks("\n".join(parts["e"]), path),
        }, i
    raise BuildError(f"{path}: 未知の記法です: {kind}")


def parse_table(lines, i, path):
    rows = []
    while i < len(lines) and lines[i].startswith("|"):
        rows.append([cell.strip() for cell in lines[i].strip().strip("|").split("|")])
        i += 1
    if len(rows) < 2 or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
        raise BuildError(f"{path}: 表の2行目は --- にしてください")
    return {"type": "table", "header": rows[0], "rows": rows[2:]}, i


def render_inline(text, glossary_href):
    pattern = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|\[\[([^\]|]+)\]\]|\[([^\]]+)\]\(([^)]+)\)")
    out = []
    pos = 0
    for match in pattern.finditer(text):
        out.append(html.escape(text[pos : match.start()]))
        if match.group(1) is not None:
            out.append("<code>" + html.escape(match.group(1)) + "</code>")
        elif match.group(2) is not None:
            out.append("<strong>" + html.escape(match.group(2)) + "</strong>")
        elif match.group(3) is not None:
            term = match.group(3)
            out.append(f'<a href="{html.escape(glossary_href)}#term-{html.escape(term)}">{html.escape(term)}</a>')
        else:
            label, url = match.group(4), match.group(5)
            out.append(
                f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'
            )
        pos = match.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def slugify(text, used):
    base = re.sub(r"\s+", "-", text.strip())
    base = re.sub(r"[^\w\-]", "", base)
    base = base or "section"
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


class Render:
    def __init__(self, glossary_href, path):
        self.glossary_href = glossary_href
        self.path = path
        self.toc = []
        self.plain = []
        self.commands = []
        self.unverified = []
        self.quiz_count = 0
        self.used_slugs = set()
        self.errors = []

    def add_plain(self, text):
        if text:
            self.plain.append(text)

    def html_blocks(self, blocks):
        self.check_commands(blocks, "本文")
        return "".join(self.render_block(block) for block in blocks)

    def render_block(self, block):
        kind = block["type"]
        if kind == "heading":
            slug = slugify(block["text"], self.used_slugs)
            self.toc.append((block["level"], block["text"], slug))
            self.add_plain(block["text"])
            return f'<h{block["level"]} id="{slug}">{render_inline(block["text"], self.glossary_href)}</h{block["level"]}>'
        if kind == "p":
            self.add_plain(block["text"])
            css = "unverified" if block["text"].startswith("未確認") else ""
            attr = f' class="{css}"' if css else ""
            return f"<p{attr}>{render_inline(block['text'], self.glossary_href)}</p>"
        if kind == "ul":
            self.add_plain(" ".join(block["items"]))
            items = "".join(f"<li>{render_inline(item, self.glossary_href)}</li>" for item in block["items"])
            return f"<ul>{items}</ul>"
        if kind == "ol":
            self.add_plain(" ".join(block["items"]))
            items = "".join(f"<li>{render_inline(item, self.glossary_href)}</li>" for item in block["items"])
            start = f' start="{block["start"]}"' if block.get("start", 1) != 1 else ""
            return f"<ol{start}>{items}</ol>"
        if kind == "quote":
            self.add_plain(block["text"])
            return f"<blockquote><p>{render_inline(block['text'], self.glossary_href)}</p></blockquote>"
        if kind == "code":
            self.add_plain(block["body"])
            self.check_file(block)
            if block["lang"] in COMMAND_LANGS:
                self.commands.append(block["body"])
            lang = html.escape(block["lang"] or "text")
            body = html.escape(block["body"])
            return f'<pre data-lang="{lang}"><code>{body}</code></pre>'
        if kind == "warn":
            inner = self.html_blocks(parse_blocks(block["body"], self.path))
            return f'<div class="warn">{inner}</div>'
        if kind == "svg":
            raw = block["body"].strip()
            if not raw.startswith("<svg") or "<script" in raw.lower():
                raise BuildError(f"{self.path}: SVG 以外は入れられません")
            self.add_plain("図")
            return raw
        if kind == "quiz":
            self.quiz_count += 1
            number = self.quiz_count
            title = f"問題{number}"
            slug = slugify(title, self.used_slugs)
            self.toc.append((3, title, slug))
            question = self.html_blocks(block["question"])
            answer = self.html_blocks(block["answer"])
            explain = self.html_blocks(block["explain"])
            return (
                f'<section class="quiz"><h3 id="{slug}">{title}</h3>{question}'
                f"<details><summary>解答と解説</summary>{answer}{explain}</details></section>"
            )
        if kind == "tabs":
            self.check_tab_parity(block)
            windows = self.panel(block["windows"], "windows", "Windows")
            linux = self.panel(block["linux"], "linux", "Linux")
            return (
                '<div class="os-tabs">'
                '<div class="os-tablist" role="tablist">'
                '<button type="button" data-os-choice="windows">Windows</button>'
                '<button type="button" data-os-choice="linux">Linux</button>'
                "</div>"
                f"{windows}{linux}</div>"
            )
        if kind == "table":
            head = "".join(f"<th>{render_inline(cell, self.glossary_href)}</th>" for cell in block["header"])
            body = []
            for row in block["rows"]:
                self.add_plain(" ".join(row))
                cells = "".join(f"<td>{render_inline(cell, self.glossary_href)}</td>" for cell in row)
                body.append(f"<tr>{cells}</tr>")
            return f'<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
        raise BuildError(f"未知のブロックです: {kind}")

    def panel(self, blocks, os_name, label):
        self.check_commands(blocks, label)
        inner = "".join(self.render_block(block) for block in blocks)
        return f'<div class="os-panel" data-os="{os_name}" role="tabpanel">{inner}</div>'

    def check_file(self, block):
        if not block["file"]:
            return
        rel = block["file"]
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise BuildError(f"{self.path}: file= のパスが不正です: {rel}")
        target = ROOT / rel
        if not target.is_file():
            raise BuildError(f"{self.path}: {rel} がありません")
        expected = target.read_text(encoding="utf-8")
        got = block["body"]
        if not expected.endswith("\n"):
            expected += "\n"
        if not got.endswith("\n"):
            got += "\n"
        if got != expected:
            raise BuildError(f"{self.path}: {rel} と本文のコードが一致しません")

    def check_tab_parity(self, block):
        win = count_shape(block["windows"])
        lin = count_shape(block["linux"])
        if win != lin:
            raise BuildError(
                f"{self.path}: Windows と Linux の手順が一致しません。手順 {win[0]} 対 {lin[0]}、コマンド {win[1]} 対 {lin[1]}"
            )

    def check_commands(self, blocks, where):
        pending = None
        prose = []

        def close():
            nonlocal pending, prose
            if pending is None:
                return
            text = "\n".join(prose)
            for phrase in COMMAND_PHRASES:
                if phrase not in text:
                    self.errors.append(f"{self.path}: {where} のコマンドの後に「{phrase}」がありません\n{pending['body']}")
            if "未確認" in text:
                self.unverified.append({"where": where, "command": pending["body"]})
            pending = None
            prose = []

        for block in blocks:
            if block["type"] == "code" and block["lang"] in COMMAND_LANGS:
                close()
                pending = block
                continue
            if block["type"] == "tabs":
                close()
                continue
            if block["type"] == "heading" and block["level"] <= 2:
                close()
                continue
            if pending is not None:
                prose.append(block_prose(block))
        close()

    def finish_checks(self, strict):
        if self.errors:
            raise BuildError("\n".join(self.errors))
        if not strict:
            return
        if self.quiz_count != 3:
            raise BuildError(f"{self.path}: 確認テストは3問です。今は {self.quiz_count} 問です")


def count_shape(blocks):
    steps = 0
    commands = 0
    for block in blocks:
        if block["type"] == "ol":
            steps += len(block["items"])
        if block["type"] == "code" and block["lang"] in COMMAND_LANGS:
            commands += 1
    return steps, commands


def block_prose(block):
    kind = block["type"]
    if kind in {"p", "quote"}:
        return block["text"]
    if kind in {"ul", "ol"}:
        return "\n".join(block["items"])
    if kind == "heading":
        return block["text"]
    if kind == "warn":
        return block["body"]
    if kind == "quiz":
        return "問題"
    return ""


def require_chapter_shape(blocks, path, concepts):
    headings = [(b["level"], b["text"]) for b in blocks if b["type"] == "heading"]
    forbidden = [text for _, text in headings if text in FORBIDDEN_HEADINGS]
    if forbidden:
        raise BuildError(f"{path}: 使わない見出しです: {forbidden}")
    h2 = [text for level, text in headings if level == 2]
    if h2 != REQUIRED_H2:
        raise BuildError(f"{path}: 見出しの並びが違います\n期待: {REQUIRED_H2}\n実際: {h2}")
    names = [part.strip() for part in concepts.split(",") if part.strip()]
    if len(names) > 3:
        raise BuildError(f"{path}: 新しい概念は3つまでです: {names}")
    goal = section_text(blocks, "この章のゴール")
    if "できる" not in goal:
        raise BuildError(f"{path}: ゴールは「できる」で書いてください")
    if not any(block["type"] == "svg" for block in section_blocks(blocks, "何が起きたか")):
        raise BuildError(f"{path}: 「何が起きたか」に SVG の図がありません")
    return names


def section_blocks(blocks, title):
    take = False
    found = []
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 2:
            if block["text"] == title:
                take = True
                continue
            if take:
                break
        if take:
            found.append(block)
    return found


def section_text(blocks, title):
    take = False
    chunks = []
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 2:
            if block["text"] == title:
                take = True
                continue
            if take:
                break
        if take:
            chunks.append(block_prose(block))
    return "\n".join(chunks)


def summary_terms(blocks, path):
    terms = []
    take = False
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 2:
            if block["text"] == "まとめ":
                take = True
                continue
            if take:
                break
        if take and block["type"] == "ul":
            for item in block["items"]:
                match = re.fullmatch(r"\*\*(.+?)\*\*: (.+)", item)
                if not match:
                    raise BuildError(f"{path}: まとめの用語は「- **用語**: 説明」です: {item}")
                terms.append((match.group(1), match.group(2)))
    if not 3 <= len(terms) <= 5:
        raise BuildError(f"{path}: まとめの用語は3個から5個です。今は {len(terms)} 個です")
    return terms


def linked_terms(text):
    return re.findall(r"\[\[([^\]|]+)\]\]", text)


def page_shell(title, body, depth, active, toc, part_titles, chapters, written):
    root = "../" if depth else ""
    nav = [
        '<div class="book-nav">',
        '<input class="nav-toggle" id="nav-toggle" type="checkbox">',
        '<label for="nav-toggle">章の一覧</label>',
    ]
    current_part = None
    for chapter in chapters:
        if chapter["part"] != current_part:
            if current_part is not None:
                nav.append("</ol>")
            current_part = chapter["part"]
            nav.append(f'<p class="part-label">第{current_part}部 {html.escape(part_titles[current_part])}</p><ol>')
        href = f'{root}chapters/{chapter["id"]}.html'
        if chapter["id"] not in written:
            nav.append(f'<li><span>{html.escape(chapter["title"])}</span></li>')
            continue
        current = ' aria-current="page"' if chapter["id"] == active else ""
        nav.append(
            f'<li><a href="{href}" data-chapter="{chapter["id"]}"{current}>第{int(chapter["id"])}章 {html.escape(chapter["title"])}</a></li>'
        )
    if current_part is not None:
        nav.append("</ol>")
    nav.append("</div>")
    toc_html = ""
    if toc:
        items = []
        for level, text, slug in toc:
            if level == 1:
                continue
            items.append(f'<li><a class="depth-{level}" href="#{html.escape(slug)}">{html.escape(text)}</a></li>')
        toc_html = '<details class="ontoc" open><summary>この章の見出し</summary><ol>' + "".join(items) + "</ol></details>"
    os_script = (
        "<script>try{document.documentElement.dataset.os="
        "localStorage.getItem('docker-k8s-textbook-os')||'linux';}"
        "catch(e){document.documentElement.dataset.os='linux';}</script>"
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{root}assets/site.css">
{os_script}
</head>
<body data-root="{root}">
<a class="skip" href="#main">本文へ</a>
<header class="site-header">
<a class="brand" href="{root}index.html">DockerとKubernetesの教科書</a>
<nav class="header-links" aria-label="関連ページ">
<a href="{root}glossary.html">用語集</a>
<a href="{root}commands.html">コマンド</a>
</nav>
<form class="search" role="search">
<label class="visually-hidden" for="search">検索</label>
<input id="search" type="search" placeholder="章のタイトルと本文を検索" autocomplete="off">
<ul id="search-results" class="search-results"></ul>
</form>
<div class="os-switch" role="group" aria-label="手順のOS">
<button type="button" data-os-choice="windows" aria-pressed="false">Windows</button>
<button type="button" data-os-choice="linux" aria-pressed="false">Linux</button>
</div>
</header>
<div class="layout">
{''.join(nav)}
<main id="main">
{body}
</main>
{toc_html}
</div>
<script src="{root}assets/search-index.js"></script>
<script src="{root}assets/site.js"></script>
</body>
</html>
"""


def pager(chapter, chapters, written):
    ids = [item["id"] for item in chapters]
    index = ids.index(chapter["id"])
    prev_link = '<span><small>前の章</small>これが最初の章です</span>'
    next_link = '<span><small>次の章</small>これが最後の章です</span>'
    for item in reversed(chapters[:index]):
        if item["id"] in written:
            prev_link = f'<a class="prev" rel="prev" href="{item["id"]}.html"><small>前の章</small>第{int(item["id"])}章 {html.escape(item["title"])}</a>'
            break
    for item in chapters[index + 1 :]:
        if item["id"] in written:
            next_link = f'<a class="next" rel="next" href="{item["id"]}.html"><small>次の章</small>第{int(item["id"])}章 {html.escape(item["title"])}</a>'
            break
    return f'<nav class="pager">{prev_link}{next_link}</nav>'


def iter_blocks(blocks, path):
    for block in blocks:
        yield block
        kind = block["type"]
        if kind == "tabs":
            yield from iter_blocks(block["windows"], path)
            yield from iter_blocks(block["linux"], path)
        elif kind == "quiz":
            yield from iter_blocks(block["question"], path)
            yield from iter_blocks(block["answer"], path)
            yield from iter_blocks(block["explain"], path)
        elif kind == "warn":
            yield from iter_blocks(parse_blocks(block["body"], path), path)


def output_host(url):
    authority = url.split("://", 1)[1].split("/", 1)[0].rstrip(").,;\"'")
    if authority.startswith("["):
        end = authority.find("]")
        if end > 1:
            return authority[1:end].lower()
    return authority.split(":")[0].lower()


def check_output_hosts(blocks, path):
    for block in iter_blocks(blocks, path):
        if block["type"] != "code" or block["lang"] != "text" or block["file"]:
            continue
        for match in OUTPUT_URL_RE.finditer(block["body"]):
            host = output_host(match.group(0))
            if host not in ALLOWED_OUTPUT_HOSTS:
                raise BuildError(f"{path}: 出力例に許可していないホストがあります: {match.group(0)}")


def check_paragraph_external_links(blocks, path):
    """段落（type p）の http(s) リンク本数。コードブロック内のURL検査と同じく、docs/ 置換前に呼ぶ。"""
    for block in iter_blocks(blocks, path):
        if block["type"] != "p":
            continue
        count = 0
        for _label, url in MARKDOWN_LINK_RE.findall(block["text"]):
            if url.strip().startswith(("http://", "https://")):
                count += 1
        if count > MAX_EXTERNAL_LINKS_PER_PARAGRAPH:
            raise BuildError(
                f"{path}: 1段落の外部リンクは{MAX_EXTERNAL_LINKS_PER_PARAGRAPH}本までです（{count}本）"
            )


def publish_site(files):
    """検査が通ったあとで docs/ を置き換える。途中で失敗しても、今の docs/ は残す。"""
    staging = ROOT / ".docs-build"
    previous = ROOT / ".docs-previous"
    if staging.exists():
        shutil.rmtree(staging)
    if previous.exists():
        shutil.rmtree(previous)
    try:
        for rel, content in files.items():
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        if DOCS.exists():
            DOCS.rename(previous)
        try:
            staging.rename(DOCS)
        except Exception:
            if previous.exists() and not DOCS.exists():
                previous.rename(DOCS)
            raise
        if previous.exists():
            shutil.rmtree(previous)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def main():
    part_titles, chapters = load_outline()
    if len(chapters) != 21:
        raise BuildError("章立ては21章です")
    written = {}
    all_terms = []
    all_unverified = []
    all_commands = []
    known_terms = set()
    for chapter in chapters:
        path = BOOK / "chapters" / f"{chapter['id']}.md"
        if not path.is_file():
            continue
        meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
        if meta.get("id") != chapter["id"] or meta.get("title") != chapter["title"] or meta.get("part") != chapter["part"]:
            raise BuildError(f"{path}: outline.json と front matter が一致しません")
        blocks = parse_blocks(body, path)
        check_output_hosts(blocks, path)
        check_paragraph_external_links(blocks, path)
        concepts = require_chapter_shape(blocks, path, meta.get("concepts", ""))
        terms = summary_terms(blocks, path)
        for term, _ in terms:
            if term in known_terms:
                raise BuildError(f"{path}: 用語「{term}」は前の章ですでに説明しています")
        for term in linked_terms(body):
            if term not in known_terms and term not in {name for name, _ in terms}:
                raise BuildError(f"{path}: [[{term}]] は、この章までのまとめで説明されていません")
        known_terms.update(name for name, _ in terms)
        renderer = Render("../glossary.html", path)
        article = renderer.html_blocks(blocks)
        renderer.finish_checks(True)
        written[chapter["id"]] = {
            "meta": meta,
            "concepts": concepts,
            "terms": terms,
            "article": article,
            "toc": renderer.toc,
            "plain": "\n".join(renderer.plain),
        }
        for term, definition in terms:
            all_terms.append((term, definition, chapter))
        for item in renderer.unverified:
            all_unverified.append((chapter, item))
        for command in renderer.commands:
            all_commands.append((chapter, command))

    for md in [BOOK / "home.md", *sorted((BOOK / "chapters").glob("*.md"))]:
        body = md.read_text(encoding="utf-8")
        for word in FORBIDDEN_TEXT:
            if word in body:
                raise BuildError(f"{md}: 本文に「{word}」は書けません")

    total_minutes = sum(chapter["minutes"] for chapter in chapters)
    home_renderer = Render("glossary.html", BOOK / "home.md")
    home_body = (BOOK / "home.md").read_text(encoding="utf-8")
    home_blocks = parse_blocks(home_body, BOOK / "home.md")
    check_output_hosts(home_blocks, BOOK / "home.md")
    check_paragraph_external_links(home_blocks, BOOK / "home.md")
    home_html = home_renderer.html_blocks(home_blocks)
    home_renderer.finish_checks(False)
    files = {
        "assets/site.css": (SITE / "site.css").read_text(encoding="utf-8"),
        "assets/site.js": (SITE / "site.js").read_text(encoding="utf-8"),
        ".nojekyll": "",
    }
    catalog = [
        f'<p id="progress-count" data-total="{len(chapters)}">0 / {len(chapters)} 章</p>',
        f"<p>21章の目安は、合計 {total_minutes} 分です。手を動かす時間を含みます。</p>",
    ]
    part_toc = []
    current_part = None
    for chapter in chapters:
        if chapter["part"] != current_part:
            current_part = chapter["part"]
            part_slug = f"part-{current_part}"
            part_label = f"第{current_part}部 {part_titles[current_part]}"
            part_toc.append((2, part_label, part_slug))
            catalog.append(f'<h2 id="{part_slug}">{html.escape(part_label)}</h2>')
        row = [
            f'<article class="chapter-row" data-chapter-row="{chapter["id"]}">',
            f'<p class="num">第{int(chapter["id"])}章</p><div>',
        ]
        if chapter["id"] in written:
            row.append(f'<h3><a href="chapters/{chapter["id"]}.html">{html.escape(chapter["title"])}</a></h3>')
            row.append(f'<p>{html.escape(chapter["summary"])}</p>')
            row.append(
                f'<label class="done"><input type="checkbox" data-done="{chapter["id"]}">読み終えた</label></div>'
            )
        else:
            row.append(f'<h3>{html.escape(chapter["title"])}</h3>')
            row.append(f'<p>{html.escape(chapter["summary"])}</p><p>執筆中</p></div>')
        row.append(f'<p class="minutes">約{chapter["minutes"]}分</p></article>')
        catalog.append("".join(row))
    index_main = (
        '<p class="part-kicker">手を動かす教科書</p>'
        "<h1>DockerとKubernetesの教科書</h1>"
        + home_html
        + '<h2 id="章の流れ">章の流れ</h2>'
        + "".join(catalog)
    )
    index_toc = list(home_renderer.toc)
    index_toc.append((2, "章の流れ", "章の流れ"))
    index_toc.extend(part_toc)
    files["index.html"] = page_shell(
        "DockerとKubernetesの教科書", index_main, 0, "", index_toc, part_titles, chapters, written
    )

    for chapter in chapters:
        if chapter["id"] not in written:
            continue
        item = written[chapter["id"]]
        kicker = f'第{chapter["part"]}部 {part_titles[chapter["part"]]}'
        main = (
            f'<p class="part-kicker">{html.escape(kicker)}</p>'
            f'<h1>第{int(chapter["id"])}章 {html.escape(chapter["title"])}</h1>'
            f'<p class="meta">目安は約{chapter["minutes"]}分です。</p>'
            + item["article"]
            + f'<label class="done"><input type="checkbox" data-done="{chapter["id"]}">この章を読み終えた</label>'
            + pager(chapter, chapters, written)
        )
        files[f"chapters/{chapter['id']}.html"] = page_shell(
            f'第{int(chapter["id"])}章 {chapter["title"]}',
            main,
            1,
            chapter["id"],
            item["toc"],
            part_titles,
            chapters,
            written,
        )

    glossary_items = []
    for term, definition, chapter in all_terms:
        glossary_items.append(
            "<section>"
            f'<h2 id="term-{html.escape(term)}">{html.escape(term)}</h2>'
            f"<p>{html.escape(definition)}</p>"
            f'<p><a href="chapters/{chapter["id"]}.html">第{int(chapter["id"])}章 {html.escape(chapter["title"])}</a></p>'
            "</section>"
        )
    glossary_main = "<h1>用語集</h1><p>各章のまとめで説明した用語です。本文のリンクからも開けます。</p>" + "".join(glossary_items)
    glossary_toc = [(2, term, f"term-{term}") for term, _, _ in all_terms]
    files["glossary.html"] = page_shell(
        "用語集", glossary_main, 0, "", glossary_toc, part_titles, chapters, written
    )

    command_html = ["<h1>コマンド早見表</h1><p>各章の本文に出るコマンドです。ファイルの中身は載せていません。</p>"]
    command_toc = []
    last = None
    for chapter, command in all_commands:
        if chapter["id"] != last:
            last = chapter["id"]
            slug = f'commands-{chapter["id"]}'
            command_toc.append((2, f'第{int(chapter["id"])}章 {chapter["title"]}', slug))
            command_html.append(
                f'<h2 id="{slug}">第{int(chapter["id"])}章 <a href="chapters/{chapter["id"]}.html">{html.escape(chapter["title"])}</a></h2>'
            )
        command_html.append(f"<pre data-lang=\"text\"><code>{html.escape(command)}</code></pre>")
    files["commands.html"] = page_shell(
        "コマンド早見表", "".join(command_html), 0, "", command_toc, part_titles, chapters, written
    )

    search = [{
        "title": "DockerとKubernetesの教科書",
        "href": "index.html",
        "text": home_body,
    }, {
        "title": "用語集",
        "href": "glossary.html",
        "text": "\n".join(term + " " + definition for term, definition, _ in all_terms),
    }, {
        "title": "コマンド早見表",
        "href": "commands.html",
        "text": "\n".join(command for _, command in all_commands),
    }]
    for chapter in chapters:
        if chapter["id"] not in written:
            continue
        search.append({
            "title": f'第{int(chapter["id"])}章 {chapter["title"]}',
            "href": f'chapters/{chapter["id"]}.html',
            "text": written[chapter["id"]]["plain"],
        })
    payload = json.dumps(search, ensure_ascii=False)
    files["assets/search-index.js"] = "window.SEARCH_INDEX = " + payload + ";\n"

    lines = [
        "# 未確認のコマンド",
        "",
        "このファイルは `scripts/build.py` が章から作ります。手で直しても、次のビルドで上書きされます。",
        "",
        "「未確認」は、そのコマンドをこの執筆環境で実行していない、という意味です。期待する出力の欄に、想像の結果は書いていません。",
        "",
    ]
    if not all_unverified:
        lines.append("該当するコマンドはありません。")
    current = None
    for chapter, item in all_unverified:
        if chapter["id"] != current:
            current = chapter["id"]
            lines.append(f'## 第{int(chapter["id"])}章 {chapter["title"]}')
            lines.append("")
        lines.append(f'- 場所: {item["where"]}')
        lines.append("")
        lines.append("```text")
        lines.append(item["command"])
        lines.append("```")
        lines.append("")
    publish_site(files)
    (ROOT / "UNVERIFIED.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"built {len(written)} chapters, {len(all_unverified)} unverified commands")


if __name__ == "__main__":
    try:
        main()
    except BuildError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
