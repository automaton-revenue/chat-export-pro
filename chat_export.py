#!/usr/bin/env python3
"""chat-export-pro: convert ChatGPT/Claude export JSON to Markdown files and a
single-file HTML archive (index.html), and search the converted Markdown."""
import argparse
import base64
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone


def parse_chatgpt(data):
    if isinstance(data, dict):
        data = data.get("conversations", [data])
    chats = []
    for conv in data:
        turns = []
        for node_id in conv.get("mapping", {}):
            node = conv["mapping"][node_id] or {}
            msg = node.get("message")
            if not msg:
                continue
            role = msg.get("author", {}).get("role")
            if role not in ("user", "assistant"):
                continue
            content = msg.get("content", {})
            parts = content.get("parts")
            if parts is None and isinstance(content.get("text"), str):
                parts = [content["text"]]
            if not parts:
                continue
            text = "\n".join(p if isinstance(p, str) else json.dumps(p)
                             for p in parts if p is not None).strip()
            if text:
                turns.append({"role": role, "text": text})
        if turns:
            chats.append({
                "title": conv.get("title") or "Untitled chat",
                "id": str(conv.get("id") or conv.get("conversation_id") or ""),
                "created_at": conv.get("create_time") or conv.get("created_at") or "",
                "turns": turns,
            })
    return chats


def parse_claude(data):
    if isinstance(data, dict):
        data = data.get("conversations", [data])
    chats = []
    for conv in data:
        turns = []
        for msg in conv.get("chat_messages", conv.get("messages", [])):
            sender = msg.get("sender") or msg.get("role") or "user"
            sender = "user" if sender == "human" else sender
            text = msg.get("text")
            if text is None:
                content = msg.get("content")
                if isinstance(content, list):
                    text = "\n".join(c.get("text", "") if isinstance(c, dict) else str(c)
                                     for c in content)
                else:
                    text = str(content or "")
            text = (text or "").strip()
            if text:
                turns.append({"role": sender, "text": text})
        if turns:
            chats.append({
                "title": conv.get("name") or conv.get("title") or "Untitled chat",
                "id": str(conv.get("uuid") or conv.get("id") or ""),
                "created_at": conv.get("created_at") or conv.get("created") or "",
                "turns": turns,
            })
    return chats


def detect_format(data):
    if isinstance(data, dict):
        data = data.get("conversations", [data])
    if not isinstance(data, list) or not data:
        return "chatgpt"
    first = data[0]
    if isinstance(first, dict):
        if "mapping" in first or "current_node" in first:
            return "chatgpt"
        if "chat_messages" in first or "name" in first or "uuid" in first:
            return "claude"
    return "chatgpt"


def load_chats(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if detect_format(data) == "claude":
        return parse_claude(data), "claude"
    return parse_chatgpt(data), "chatgpt"


def _slug(title, used):
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", title.strip().lower()).strip("-") or "chat"
    name, n = base, 2
    while name in used:
        name = "%s-%d" % (base, n)
        n += 1
    used.add(name)
    return name


def _to_datetime(value):
    """Return a timezone-aware datetime for an export timestamp, or None.

    ChatGPT stores Unix epoch seconds (float), Claude stores ISO-8601 strings
    such as "2024-01-15T10:30:00.123456Z". ISO strings without an offset are
    treated as UTC, which is what both exports use.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            value = float(s)  # epoch seconds stored as a string
        except ValueError:
            if s[-1] in "Zz":
                s = s[:-1] + "+00:00"
            # Python < 3.11 only accepts 3 or 6 fractional digits.
            s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)) and value > 0:
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    return None


def _ts(value):
    """Format an export timestamp as a local date, e.g. '2026-10-11 14:03'."""
    dt = _to_datetime(value)
    if dt is None:
        return str(value) if value and isinstance(value, str) else ""
    try:
        dt = dt.astimezone()  # local time zone of the machine running the export
    except (OverflowError, OSError, ValueError):
        pass
    return dt.strftime("%Y-%m-%d %H:%M")


def _epoch(value):
    dt = _to_datetime(value)
    return int(dt.timestamp()) if dt else 0


def chat_to_markdown(chat):
    lines = ["# %s" % chat["title"], ""]
    ts = _ts(chat.get("created_at"))
    if ts:
        lines += ["*Created: %s*" % ts, ""]
    for turn in chat["turns"]:
        lines += ["## %s" % turn["role"].capitalize(), "", turn["text"], ""]
    return "\n".join(lines).rstrip() + "\n"


_SOURCE_LABELS = {"chatgpt": "ChatGPT", "claude": "Claude"}


def _role_label(role, source):
    if role == "user":
        return "You"
    if role == "assistant" and source in _SOURCE_LABELS:
        return _SOURCE_LABELS[source]
    return role.capitalize()


def _csp_source(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return "'sha256-%s'" % base64.b64encode(digest).decode("ascii")


def _csp_meta(css, js=None):
    """Content-Security-Policy that allows only our own inline style/script.

    The page may not load anything from the network, and a script that ended
    up in chat content could not run even if escaping ever failed.
    """
    policy = ("default-src 'none'; style-src %s; script-src %s; "
              "base-uri 'none'; form-action 'none'"
              % (_csp_source(css), _csp_source(js) if js else "'none'"))
    return '<meta http-equiv="Content-Security-Policy" content="%s">' % policy


def _render_turns(turns, source=None):
    out = []
    for turn in turns:
        role = turn["role"]
        out.append('<div class="turn" data-role="%s">' % html.escape(role))
        out.append('<div class="who">%s</div>' % html.escape(_role_label(role, source)))
        out.append('<div class="bubble">%s</div>' % _text_to_html(turn["text"]))
        out.append("</div>")
    return "\n".join(out)


def chat_to_html(chat, source=None):
    """One standalone HTML page for a single chat (used by --per-chat-html)."""
    title = html.escape(chat["title"])
    css = _BASE_CSS + _PAGE_CSS
    out = ["<!DOCTYPE html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<meta name="color-scheme" content="light dark">', _csp_meta(css),
           "<title>%s</title>" % title, "<style>%s</style>" % css, "</head>",
           "<body>", '<main class="page">', '<header class="chat-head">',
           "<h1>%s</h1>" % title]
    meta = []
    if source in _SOURCE_LABELS:
        meta.append('<span class="badge">%s</span>' % _SOURCE_LABELS[source])
    ts = _ts(chat.get("created_at"))
    if ts:
        meta.append("<time>%s</time>" % html.escape(ts))
    meta.append("<span>%s</span>" % _plural(len(chat["turns"]), "message"))
    out.append('<div class="meta">%s</div>' % "".join(meta))
    out.append("</header>")
    out.append('<div class="thread">')
    out.append(_render_turns(chat["turns"], source))
    out += ["</div>", "</main>", "</body>", "</html>"]
    return "\n".join(out) + "\n"


def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def _snippet(chat, limit=140):
    first = next((t["text"] for t in chat["turns"] if t["role"] == "user"),
                 chat["turns"][0]["text"])
    first = re.sub(r"\s+", " ", re.sub(r"`+|\*\*", " ", first)).strip()
    first = re.sub(r" ([.,;:!?])", r"\1", first)
    return first if len(first) <= limit else first[:limit - 1].rstrip() + "…"


def build_archive(chats, source="chatgpt", slugs=None, generated=None):
    """Return the single-file archive (index.html) for all chats.

    Everything (CSS, JS, every chat) is inline; the file makes no network
    requests. All chat text is HTML-escaped before it is written.
    """
    if slugs is None:
        used = {"index"}
        slugs = [_slug(c["title"], used) for c in chats]
    entries = sorted(zip(slugs, chats), key=lambda e: _epoch(e[1].get("created_at")),
                     reverse=True)
    label = _SOURCE_LABELS.get(source, "Chat")
    generated = generated or datetime.now().strftime("%Y-%m-%d %H:%M")

    items, articles = [], []
    for slug, chat in entries:
        cid = "c-" + slug  # slugs only contain [a-z0-9_-], safe as an id
        title = html.escape(chat["title"])
        ts = _ts(chat.get("created_at"))
        msgs = _plural(len(chat["turns"]), "message")
        meta = " · ".join(x for x in (html.escape(ts), msgs) if x)
        items.append(
            '<a class="item" href="#%s" data-id="%s" data-ts="%d" data-title="%s">'
            '<span class="item-title">%s</span><span class="item-meta">%s</span>'
            '<span class="item-snippet">%s</span></a>'
            % (cid, cid, _epoch(chat.get("created_at")), html.escape(chat["title"].lower()),
               title, meta, html.escape(_snippet(chat))))
        head_meta = ['<span class="badge">%s</span>' % label]
        if ts:
            head_meta.append("<time>%s</time>" % html.escape(ts))
        head_meta.append("<span>%s</span>" % msgs)
        articles.append(
            '<article class="chat" id="%s">\n<header class="chat-head">'
            '<a class="back" href="#">%s All chats</a><h1>%s</h1>'
            '<div class="meta">%s</div></header>\n<div class="thread">\n%s\n</div>\n</article>'
            % (cid, _ICON_BACK, title, "".join(head_meta), _render_turns(chat["turns"], source)))

    css = _BASE_CSS + _ARCHIVE_CSS
    values = {
        "CSP": _csp_meta(css, _ARCHIVE_JS), "CSS": css, "JS": _ARCHIVE_JS,
        "LABEL": label, "COUNT": _plural(len(entries), "conversation"),
        "N": str(len(entries)), "GENERATED": html.escape(generated),
        "ICON_LOGO": _ICON_LOGO, "ICON_SEARCH": _ICON_SEARCH, "ICON_THEME": _ICON_THEME,
        "ITEMS": "\n".join(items), "ARTICLES": "\n".join(articles),
    }
    # Single pass, so "{{...}}" inside chat text is never treated as a placeholder.
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], _ARCHIVE_TEMPLATE)


def _inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


_UL = re.compile(r"^\s*[-*] (.*)$")
_OL = re.compile(r"^\s*\d+[.)] (.*)$")
_H = re.compile(r"^(#{1,6}) (.*)$")


def _render_block(lines):
    """Render one block of non-empty lines: lists, headings and paragraphs."""
    parts, para, lst = [], [], []  # lst = [tag, items] while a list is open

    def flush_para():
        if para:
            parts.append("<p>%s</p>" % "<br>".join(_inline(l) for l in para))
            del para[:]

    def flush_list():
        if lst:
            parts.append("<%s>%s</%s>" % (lst[0], "".join(lst[1]), lst[0]))
            del lst[:]

    for line in lines:
        item = _UL.match(line) or _OL.match(line)
        if item:
            tag = "ul" if _UL.match(line) else "ol"
            flush_para()
            if lst and lst[0] != tag:
                flush_list()
            if not lst:
                lst.extend([tag, []])
            lst[1].append("<li>%s</li>" % _inline(item.group(1)))
            continue
        flush_list()
        heading = _H.match(line)
        if heading:
            flush_para()
            level = min(len(heading.group(1)) + 2, 6)  # keep below the page's own h1
            parts.append("<h%d>%s</h%d>" % (level, _inline(heading.group(2)), level))
        else:
            para.append(line)
    flush_para()
    flush_list()
    return parts


def _text_to_html(text):
    """Render markdown-ish text to HTML: fenced code, lists, headings, paragraphs."""
    parts = []
    tokens = re.split(r"```", text)  # even tokens: prose; odd: code blocks
    for i, token in enumerate(tokens):
        if i % 2 == 1:
            lang = ""
            m = re.match(r"([A-Za-z0-9_+#.-]{1,24})[ \t]*\n", token)
            if m:  # ```python: info string, not part of the code
                lang, token = m.group(1), token[m.end():]
            label = '<span class="code-lang">%s</span>' % html.escape(lang) if lang else ""
            parts.append('<div class="code">%s<pre><code>%s</code></pre></div>'
                         % (label, html.escape(token.strip("\n"))))
            continue
        for block in re.split(r"\n\s*\n", token):
            lines = [l for l in block.split("\n") if l.strip()]
            if lines:
                parts.extend(_render_block(lines))
    return "\n".join(parts)


def cmd_convert(args):
    chats, fmt = load_chats(args.input)
    if not chats:
        print("No chats found in %s (format: %s)" % (args.input, fmt), file=sys.stderr)
        return 1
    os.makedirs(args.outdir, exist_ok=True)
    used = {"index"}  # index.html is the archive; no chat may take that name
    slugs = []
    for chat in chats:
        slug = _slug(chat["title"], used)
        slugs.append(slug)
        with open(os.path.join(args.outdir, slug + ".md"), "w", encoding="utf-8") as f:
            f.write(chat_to_markdown(chat))
        if args.per_chat_html:
            with open(os.path.join(args.outdir, slug + ".html"), "w", encoding="utf-8") as f:
                f.write(chat_to_html(chat, fmt))
    index = os.path.join(args.outdir, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(build_archive(chats, fmt, slugs))
    print("Converted %d chat(s) from %s format into %s" % (len(chats), fmt, args.outdir))
    print("  %d Markdown file(s)%s" % (len(chats), " and %d per-chat .html page(s)" % len(chats)
                                       if args.per_chat_html else ""))
    print("  Archive (one file, works offline): %s" % index)
    return 0


def cmd_search(args):
    if not os.path.isdir(args.directory):
        print("Not a directory: %s" % args.directory, file=sys.stderr)
        return 1
    flags = re.IGNORECASE if args.ignore_case else 0
    pattern = re.compile(re.escape(args.query), flags)
    matches = 0
    for name in sorted(os.listdir(args.directory)):
        if not name.lower().endswith(".md"):
            continue
        with open(os.path.join(args.directory, name), "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if pattern.search(line):
                matches += 1
                print("%s:%d: %s" % (name, i + 1, line.rstrip()))
                for j in range(1, args.context + 1):
                    if i + j < len(lines):
                        print("  %d: %s" % (i + j + 1, lines[i + j].rstrip()))
                if matches >= args.max:
                    print("... (stopped after %d matches)" % args.max)
                    return 0
    if matches == 0:
        print("No matches for %r in %s" % (args.query, args.directory))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="chat_export.py",
        description="Convert ChatGPT/Claude chat export JSON to Markdown files and a "
                    "single-file HTML archive (index.html), with search.")
    sub = p.add_subparsers(dest="command")

    pc = sub.add_parser("convert", help="Convert a chat export JSON file to Markdown "
                                        "files + a single-file index.html archive")
    pc.add_argument("input", help="Path to the chat export JSON file")
    pc.add_argument("--outdir", default="output", help="Output directory (default: output)")
    pc.add_argument("--per-chat-html", action="store_true",
                    help="Also write one standalone .html page per chat")
    pc.set_defaults(func=cmd_convert)

    ps = sub.add_parser("search", help="Search converted Markdown files for a query")
    ps.add_argument("directory", help="Directory of converted Markdown files")
    ps.add_argument("query", help="Query string to search for")
    ps.add_argument("-n", "--max", type=int, default=50, help="Max matches to print")
    ps.add_argument("-C", "--context", type=int, default=0,
                    help="Lines of context after each match")
    ps.add_argument("-i", "--ignore-case", action="store_true",
                    help="Case-insensitive search")
    ps.set_defaults(func=cmd_search)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args) or 0


# --- Page assets. Inline only: no CDNs, no web fonts, no network requests. ---

_ICON_LOGO = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">'
              '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 '
              '2.5H10l-4.2 3.6c-.5.4-1.3.1-1.3-.6V16A2.5 2.5 0 0 1 4 13.5z" fill="currentColor"/>'
              '</svg>')
_ICON_SEARCH = ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">'
                '<circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/>'
                '<path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round"/></svg>')
_ICON_THEME = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
               '<circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/>'
               '<path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></svg>')
_ICON_BACK = ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">'
              '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round"/></svg>')

_DARK_VARS = """
--bg:#0d0f14;--surface:#161920;--side:#11131a;--text:#e8eaef;--muted:#9aa2b1;--faint:#727a8a;
--border:#252a34;--accent:#8e95ff;--accent-soft:#1f2350;--user:#272c57;--user-text:#eef0ff;
--code-bg:#0a0c10;--code-text:#e6e8ee;--code-head:#141820;--inline:#232733;--mark:#8a6d00;
--shadow:0 1px 2px rgba(0,0,0,.35)"""

_BASE_CSS = """
:root{color-scheme:light;
--bg:#f5f6f8;--surface:#fff;--side:#fbfbfc;--text:#181b21;--muted:#5f6774;--faint:#868e9c;
--border:#e3e6eb;--accent:#4f46e5;--accent-soft:#eef0ff;--user:#e8ebff;--user-text:#1b1f3a;
--code-bg:#12151c;--code-text:#e6e8ee;--code-head:#1c202a;--inline:#eef0f3;--mark:#ffe58a;
--shadow:0 1px 2px rgba(16,20,30,.05),0 4px 16px rgba(16,20,30,.04)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;""" + _DARK_VARS + """}}
:root[data-theme=dark]{color-scheme:dark;""" + _DARK_VARS + """}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--text);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI Variable Text","Segoe UI",Inter,Roboto,
"Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
code,pre{font-family:ui-monospace,"Cascadia Code","SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
font-variant-ligatures:none}
.chat-head h1{font-size:clamp(20px,2.4vw,26px);line-height:1.25;letter-spacing:-.015em;
margin:6px 0 8px;overflow-wrap:anywhere}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;color:var(--muted);font-size:13px}
.badge{display:inline-flex;align-items:center;padding:2px 9px;border-radius:999px;font-size:12px;
font-weight:600;background:var(--accent-soft);color:var(--accent)}
.thread{display:flex;flex-direction:column;gap:22px}
.turn{display:flex;flex-direction:column;align-items:flex-start;min-width:0}
.turn[data-role=user]{align-items:flex-end}
.who{font-size:12px;font-weight:600;letter-spacing:.02em;color:var(--muted);margin:0 6px 6px}
.bubble{background:var(--surface);border:1px solid var(--border);border-radius:18px;
border-top-left-radius:6px;padding:12px 18px;max-width:100%;min-width:0;box-shadow:var(--shadow);
overflow-wrap:anywhere}
.turn[data-role=user] .bubble{background:var(--user);color:var(--user-text);
border-color:transparent;border-radius:18px;border-top-right-radius:6px;max-width:min(85%,640px);
box-shadow:none}
.bubble>:first-child{margin-top:0}.bubble>:last-child{margin-bottom:0}
.bubble p{margin:.6em 0}.bubble ul,.bubble ol{margin:.6em 0;padding-left:1.4em}
.bubble li{margin:.2em 0}
.bubble h3,.bubble h4,.bubble h5,.bubble h6{margin:1em 0 .4em;line-height:1.3}
.bubble h3{font-size:1.15em}.bubble h4{font-size:1.05em}.bubble h5,.bubble h6{font-size:1em}
.bubble code{font-size:.88em;background:var(--inline);padding:.12em .38em;border-radius:6px}
.code{margin:.8em 0;border-radius:12px;overflow:hidden;background:var(--code-bg);
border:1px solid var(--border)}
.code-lang{display:block;padding:6px 14px;font:600 11px/1.6 ui-monospace,Consolas,monospace;
letter-spacing:.04em;text-transform:lowercase;color:#9aa2b1;background:var(--code-head)}
.code pre{margin:0;padding:14px 16px;overflow-x:auto;color:var(--code-text);font-size:13px;
line-height:1.55;tab-size:4}
.bubble .code pre code{background:none;padding:0;font-size:inherit;border-radius:0;color:inherit}
mark.hit{background:var(--mark);color:inherit;border-radius:3px;padding:0 1px}
.code mark.hit{background:#f2cc60;color:#12151c}
"""

_PAGE_CSS = """
.page{max-width:820px;margin:0 auto;padding:40px 20px 72px}
.page .chat-head{margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid var(--border)}
"""

_ARCHIVE_CSS = """
.app{display:grid;grid-template-columns:340px minmax(0,1fr);height:100vh;height:100dvh}
.sidebar{display:flex;flex-direction:column;min-height:0;background:var(--side);
border-right:1px solid var(--border)}
.brand{display:flex;align-items:center;gap:12px;padding:20px 20px 14px}
.logo{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;color:#fff;
background:linear-gradient(135deg,#6366f1,#8b5cf6);flex:none}
.brand-text{min-width:0;flex:1}
.brand-title{font-weight:700;font-size:16px;letter-spacing:-.01em}
.brand-sub{font-size:12.5px;color:var(--muted)}
.icon-btn{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;
border:1px solid var(--border);background:var(--surface);color:var(--muted);cursor:pointer;flex:none}
.icon-btn:hover{color:var(--text)}
.tools{padding:0 16px 12px;display:flex;flex-direction:column;gap:10px}
.search{position:relative;display:block}
.search svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--faint)}
.search input{width:100%;font:inherit;font-size:14px;color:var(--text);background:var(--surface);
border:1px solid var(--border);border-radius:12px;padding:10px 12px 10px 36px;outline:none;
transition:border-color .15s,box-shadow .15s}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.row{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:12.5px;
color:var(--muted)}
.row select{font:inherit;font-size:12.5px;color:var(--text);background:var(--surface);
border:1px solid var(--border);border-radius:8px;padding:4px 8px}
.list{flex:1;overflow-y:auto;padding:4px 10px 16px;display:flex;flex-direction:column;gap:2px}
.item{display:block;padding:10px 12px;border-radius:12px;text-decoration:none;color:inherit;
border:1px solid transparent;transition:background .12s}
.item[hidden]{display:none}
.item:hover{background:var(--surface);border-color:var(--border)}
.item.active{background:var(--accent-soft);border-color:transparent}
.item.active .item-title{color:var(--accent)}
.item-title{display:block;font-weight:600;font-size:14px;line-height:1.35;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.item-meta{display:block;font-size:12px;color:var(--faint);margin-top:2px}
.item-snippet{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
font-size:12.5px;color:var(--muted);margin-top:4px;line-height:1.45}
.empty{margin:24px 20px;color:var(--muted);font-size:14px;text-align:center}
.main{overflow-y:auto;min-width:0}
.chat{max-width:860px;margin:0 auto;padding:0 32px 64px}
.chat .chat-head{position:sticky;top:0;z-index:1;margin:0 -32px 24px;padding:24px 32px 16px;
background:var(--bg);border-bottom:1px solid var(--border)}
.back{display:none;align-items:center;gap:4px;font-size:13px;font-weight:600;color:var(--accent);
text-decoration:none}
.welcome{display:none}
.welcome .logo{margin:0 auto}
.welcome h2{color:var(--text);font-size:20px;margin:14px 0 4px}
.foot{max-width:860px;margin:0 auto;padding:0 32px 32px;color:var(--faint);font-size:12px}
.js .chat{display:none}.js .chat.active{display:block}
.js .welcome.show{display:grid;place-items:center;min-height:70vh;text-align:center;
color:var(--muted);padding:32px}
@media (max-width:859px){
.app{display:block;height:auto}
.sidebar{border-right:0;min-height:100vh;min-height:100dvh}
.brand{padding:16px 16px 12px}
.tools{padding:0 16px 12px}
.list{overflow:visible;padding:4px 8px 16px}
.main{overflow:visible}
.js.reading .sidebar{display:none}
.js:not(.reading) .main{display:none}
.chat{padding:0 16px 48px}
.chat .chat-head{margin:0 -16px 20px;padding:14px 16px 12px}
.js .back{display:inline-flex}
.turn[data-role=user] .bubble{max-width:92%}
.bubble{padding:11px 15px}
.foot{padding:0 16px 24px}
}
"""

_ARCHIVE_JS = r"""
(function () {
  var d = document, root = d.documentElement;
  root.classList.add('js');
  try { var saved = localStorage.getItem('cep-theme'); if (saved) root.setAttribute('data-theme', saved); } catch (e) {}
  var list = d.getElementById('list'), q = d.getElementById('q'), sort = d.getElementById('sort');
  var count = d.getElementById('count'), empty = d.getElementById('empty');
  var main = d.getElementById('main'), welcome = d.getElementById('welcome');
  var items = [].slice.call(list.querySelectorAll('.item'));
  var chats = {}, hay = {}, current = null;
  [].forEach.call(d.querySelectorAll('article.chat'), function (a) { chats[a.id] = a; });
  items.forEach(function (it) {
    var id = it.getAttribute('data-id'), a = chats[id];
    hay[id] = (it.getAttribute('data-title') + ' ' + (a ? a.textContent : '')).toLowerCase();
  });
  var wide = window.matchMedia('(min-width: 860px)');

  function terms() { return q.value.toLowerCase().split(/\s+/).filter(Boolean); }
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  // Highlighting only creates text nodes and <mark> elements: chat text is
  // never parsed as HTML here.
  function clearMarks(el) {
    [].slice.call(el.querySelectorAll('mark.hit')).forEach(function (m) {
      var p = m.parentNode; p.replaceChild(d.createTextNode(m.textContent), m); p.normalize();
    });
  }
  function highlight() {
    if (!current) return;
    clearMarks(current);
    var t = terms(); if (!t.length) return;
    var re = new RegExp(t.map(esc).join('|'), 'gi');
    var walker = d.createTreeWalker(current.querySelector('.thread'), NodeFilter.SHOW_TEXT, null);
    var nodes = [], node;
    while ((node = walker.nextNode())) nodes.push(node);
    nodes.forEach(function (n) {
      var s = n.nodeValue, m, last = 0, frag = d.createDocumentFragment(), hit = false;
      re.lastIndex = 0;
      while ((m = re.exec(s))) {
        hit = true;
        if (m.index > last) frag.appendChild(d.createTextNode(s.slice(last, m.index)));
        var mk = d.createElement('mark'); mk.className = 'hit'; mk.textContent = m[0];
        frag.appendChild(mk); last = m.index + m[0].length;
      }
      if (!hit) return;
      frag.appendChild(d.createTextNode(s.slice(last)));
      n.parentNode.replaceChild(frag, n);
    });
  }
  function filter() {
    var t = terms(), n = 0;
    items.forEach(function (it) {
      var h = hay[it.getAttribute('data-id')];
      var ok = t.every(function (w) { return h.indexOf(w) > -1; });
      it.hidden = !ok; if (ok) n++;
    });
    count.textContent = n + (n === 1 ? ' chat' : ' chats') + (t.length ? ' found' : '');
    empty.hidden = n > 0;
    var open = current && list.querySelector('.item[data-id="' + current.id + '"]');
    if (wide.matches && n && (!open || open.hidden)) {
      var first = items.filter(function (i) { return !i.hidden; })[0];
      return show(first.getAttribute('data-id'));  // keep a matching chat open
    }
    highlight();
  }
  function order() {
    var mode = sort.value;
    items.sort(function (a, b) {
      if (mode === 'title') return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
      var x = +a.getAttribute('data-ts') || 0, y = +b.getAttribute('data-ts') || 0;
      return mode === 'old' ? x - y : y - x;
    });
    items.forEach(function (it) { list.appendChild(it); });
  }
  function show(id) {
    if (current) { current.classList.remove('active'); clearMarks(current); }
    current = chats[id] || null;
    items.forEach(function (it) {
      var on = it.getAttribute('data-id') === id;
      it.classList.toggle('active', on);
      if (on) it.setAttribute('aria-current', 'page'); else it.removeAttribute('aria-current');
    });
    root.classList.toggle('reading', !!current);
    welcome.classList.toggle('show', !current);
    if (current) { current.classList.add('active'); highlight(); }
    main.scrollTop = 0;
    if (!wide.matches) window.scrollTo(0, 0);
  }
  function route() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (chats[id]) return show(id);
    if (wide.matches) {
      var first = items.filter(function (i) { return !i.hidden; })[0];
      return show(first ? first.getAttribute('data-id') : null);
    }
    show(null);
  }
  q.addEventListener('input', filter);
  sort.addEventListener('change', order);
  window.addEventListener('hashchange', route);
  d.addEventListener('keydown', function (e) {
    if (e.key === '/' && d.activeElement !== q) { e.preventDefault(); q.focus(); }
  });
  d.getElementById('theme').addEventListener('click', function () {
    var cur = root.getAttribute('data-theme');
    var dark = cur ? cur === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('cep-theme', next); } catch (e) {}
  });
  route();
})();
"""

_ARCHIVE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
{{CSP}}
<meta name="generator" content="Chat Export Pro">
<title>{{LABEL}} archive ({{N}} chats)</title>
<style>{{CSS}}</style>
</head>
<body>
<div class="app">
<aside class="sidebar">
<header class="brand">
<div class="logo">{{ICON_LOGO}}</div>
<div class="brand-text"><div class="brand-title">{{LABEL}} archive</div>
<div class="brand-sub">{{COUNT}} · works offline</div></div>
<button class="icon-btn" id="theme" type="button" title="Switch light/dark" aria-label="Switch light or dark theme">{{ICON_THEME}}</button>
</header>
<div class="tools">
<label class="search">{{ICON_SEARCH}}<input id="q" type="search" placeholder="Search titles and messages" autocomplete="off" aria-label="Search chats"></label>
<div class="row"><span id="count" aria-live="polite">{{N}} chats</span>
<select id="sort" aria-label="Sort chats"><option value="new">Newest first</option><option value="old">Oldest first</option><option value="title">Title A–Z</option></select></div>
</div>
<nav class="list" id="list" aria-label="Chats">
{{ITEMS}}
</nav>
<p class="empty" id="empty" hidden>No chats match your search.</p>
</aside>
<main class="main" id="main">
<section class="welcome" id="welcome"><div><div class="logo">{{ICON_LOGO}}</div>
<h2>Select a conversation</h2><p>Pick a chat on the left, or search across all {{N}} chats.</p></div></section>
{{ARTICLES}}
<footer class="foot">Generated {{GENERATED}} by Chat Export Pro. This one file contains every chat and works offline.</footer>
</main>
</div>
<script>{{JS}}</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
