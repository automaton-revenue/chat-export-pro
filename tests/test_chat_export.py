"""Tests for chat_export.py (pytest-compatible)."""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import chat_export  # noqa: E402

CHATGPT_FIXTURE = os.path.join(HERE, "fixtures", "chatgpt_sample.json")
CLAUDE_FIXTURE = os.path.join(HERE, "fixtures", "claude_sample.json")
# Same shape as the real files: a top-level list of conversations.
CHATGPT_EXPORT = os.path.join(HERE, "fixtures", "chatgpt_conversations.json")
CLAUDE_EXPORT = os.path.join(HERE, "fixtures", "claude_conversations.json")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def _local(epoch):
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def _local_iso(*args):
    return datetime(*args, tzinfo=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def _convert(fixture, outdir, *extra):
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "chat_export.py"),
         "convert", fixture, "--outdir", str(outdir), *extra],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r


# --- parsing ---------------------------------------------------------------

def test_load_chatgpt_fixture():
    chats, fmt = chat_export.load_chats(CHATGPT_FIXTURE)
    assert fmt == "chatgpt"
    assert len(chats) == 1
    chat = chats[0]
    assert chat["title"] == "Python Tips"
    assert chat["id"] == "conv-001"
    assert len(chat["turns"]) == 4  # system node skipped
    assert [t["role"] for t in chat["turns"]] == ["user", "assistant", "user", "assistant"]
    assert "reverse a string" in chat["turns"][0]["text"]
    assert "slicing" in chat["turns"][1]["text"]
    with open(CHATGPT_FIXTURE, encoding="utf-8") as f:
        assert chat_export.detect_format(json.load(f)) == "chatgpt"


def test_load_claude_fixture():
    chats, fmt = chat_export.load_chats(CLAUDE_FIXTURE)
    assert fmt == "claude"
    assert len(chats) == 2
    first = chats[0]
    assert first["title"] == "Recipe Planning"
    assert first["id"] == "claude-uuid-1234"
    assert [t["role"] for t in first["turns"]] == ["user", "assistant", "user"]
    assert first["turns"][2]["text"] == "How long does that take?"  # content-list form
    assert chats[1]["title"] == "Code Review"
    with open(CLAUDE_FIXTURE, encoding="utf-8") as f:
        assert chat_export.detect_format(json.load(f)) == "claude"


def test_load_real_shaped_exports():
    chats, fmt = chat_export.load_chats(CHATGPT_EXPORT)
    assert fmt == "chatgpt" and len(chats) == 3
    assert chats[0]["created_at"] == 1760187780.512
    chats, fmt = chat_export.load_chats(CLAUDE_EXPORT)
    assert fmt == "claude" and [c["title"] for c in chats] == ["Trip planning", "Regex help"]
    assert chats[0]["turns"][1]["text"].startswith("Day 1")


def test_parse_chatgpt_skips_empty_and_system():
    data = {"conversations": [{
        "title": "T", "id": "1",
        "mapping": {
            "a": {"message": {"author": {"role": "system"},
                              "content": {"parts": ["sys"]}}},
            "b": {"message": {"author": {"role": "user"}, "content": {"parts": [""]}}},
            "c": {"message": {"author": {"role": "user"}, "content": {"parts": ["hi"]}}},
        }}]}
    chats = chat_export.parse_chatgpt(data)
    assert chats[0]["turns"] == [{"role": "user", "text": "hi"}]


# --- dates (defect 1) ------------------------------------------------------

def test_ts_chatgpt_epoch_is_local_date():
    assert chat_export._ts(1700000000) == _local(1700000000)
    assert chat_export._ts(1760187780.512) == _local(1760187780.512)
    assert chat_export._ts("1700000000.0") == _local(1700000000)
    assert DATE_RE.match(chat_export._ts(1700000000))


def test_ts_claude_iso_is_local_date():
    assert chat_export._ts("2024-01-15T10:30:00Z") == _local_iso(2024, 1, 15, 10, 30)
    assert chat_export._ts("2026-03-04T08:15:30.123456Z") == _local_iso(2026, 3, 4, 8, 15, 30)
    assert chat_export._ts("2025-12-31T23:59:00.5Z") == _local_iso(2025, 12, 31, 23, 59)
    assert chat_export._ts("2024-01-15T10:30:00.1234567+00:00") == _local_iso(2024, 1, 15, 10, 30)
    assert chat_export._ts("2024-01-15T12:30:00+02:00") == _local_iso(2024, 1, 15, 10, 30)


def test_ts_empty_and_unparseable():
    assert chat_export._ts(None) == ""
    assert chat_export._ts("") == ""
    assert chat_export._ts(0) == ""
    assert chat_export._ts("not a date") == "not a date"


def test_dates_render_readably_everywhere(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path, "--per-chat-html")
    md = (tmp_path / "deploy-checklist.md").read_text(encoding="utf-8")
    page = (tmp_path / "deploy-checklist.html").read_text(encoding="utf-8")
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    want = _local(1760187780.512)
    assert "*Created: %s*" % want in md
    assert "<time>%s</time>" % want in page
    assert "<time>%s</time>" % want in index
    for text in (md, page, index):
        assert "1760187780" not in text.replace('data-ts="1760187780"', "")
        assert "1700000000" not in text.replace('data-ts="1700000000"', "")


def test_claude_dates_in_archive(tmp_path):
    _convert(CLAUDE_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "<time>%s</time>" % _local_iso(2026, 3, 4, 8, 15) in index
    assert "2026-03-04T08:15:30" not in index


# --- Markdown / per-chat HTML ------------------------------------------------

def test_markdown_structure():
    chats, _ = chat_export.load_chats(CHATGPT_FIXTURE)
    md = chat_export.chat_to_markdown(chats[0])
    assert md.startswith("# Python Tips")
    assert "## User" in md and "## Assistant" in md
    assert "text[::-1]" in md
    assert md.index("reverse a string") < md.index("slicing") < md.index("reversing a list")
    assert md.endswith("\n")


def test_html_structure():
    chats, _ = chat_export.load_chats(CHATGPT_FIXTURE)
    out = chat_export.chat_to_html(chats[0])
    assert out.startswith("<!DOCTYPE html>") and "</html>" in out
    assert "<title>Python Tips</title>" in out and "<h1>Python Tips</h1>" in out
    assert out.count('class="turn"') == 4
    assert "<code>text[::-1]</code>" in out
    assert "<li>Simple</li>" in out
    assert "<pre><code>" in out  # fenced code block rendered


def test_html_escapes_user_input():
    chat = {"title": "A <b> & title", "id": "x", "created_at": "",
            "turns": [{"role": "user", "text": "<script>alert(1)</script>"}]}
    out = chat_export.chat_to_html(chat)
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "A &lt;b&gt; &amp; title" in out


def test_html_bold_italic():
    chats, _ = chat_export.load_chats(CLAUDE_FIXTURE)
    out = chat_export.chat_to_html(chats[0])
    assert "<em>quick</em>" in out
    assert "<strong>aglio e olio</strong>" in out
    assert "<li>Boil spaghetti</li>" in out


def test_code_language_label_and_lists():
    out = chat_export._text_to_html("Intro:\n- a\n- b\n\n1. one\n2. two\n\n```python\nx = 1\n```")
    assert "<p>Intro:</p><ul>" in out.replace("\n", "")
    assert "<ol><li>one</li><li>two</li></ol>" in out
    assert '<span class="code-lang">python</span><pre><code>x = 1</code></pre>' in out
    assert "python\nx = 1" not in out


def test_slug_unique():
    used = set()
    s1 = chat_export._slug("My Chat!", used)
    s2 = chat_export._slug("My Chat!", used)
    s3 = chat_export._slug("My Chat!", used)
    assert s1 == "my-chat"
    assert {s1, s2, s3} == {"my-chat", "my-chat-2", "my-chat-3"}


# --- single-file archive (defect 2) ------------------------------------------

class _Resources(HTMLParser):
    """Collect everything in a page that could make the browser fetch something."""

    def __init__(self):
        super().__init__()
        self.tags, self.refs, self.scripts = [], [], 0

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "script":
            self.scripts += 1
        for name, value in attrs:
            if name in ("src", "href", "srcset", "action", "poster", "data", "background"):
                self.refs.append((tag, name, value or ""))


def test_convert_cli_produces_archive_and_markdown(tmp_path):
    outdir = tmp_path / "out"
    _convert(CHATGPT_FIXTURE, outdir)
    assert sorted(os.listdir(outdir)) == ["index.html", "python-tips.md"]
    assert (outdir / "python-tips.md").read_text(encoding="utf-8").startswith("# Python Tips")
    assert "</html>" in (outdir / "index.html").read_text(encoding="utf-8")


def test_archive_contains_every_chat_and_message(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    chats, _ = chat_export.load_chats(CHATGPT_EXPORT)
    for chat in chats:
        assert "<h1>%s</h1>" % chat_export.html.escape(chat["title"]) in index
    assert index.count('<article class="chat"') == 3
    assert index.count('<a class="item"') == 3
    assert "Pin dependencies" in index and "A chat whose title is Index." in index
    assert '<span class="code-lang">bash</span>' in index
    # newest first in the list
    assert index.index('href="#c-deploy-checklist"') < index.index('href="#c-index-2"')


def test_archive_claude(tmp_path):
    _convert(CLAUDE_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Claude archive" in index
    assert "Trip planning" in index and "Regex help" in index
    assert '<div class="who">Claude</div>' in index and '<div class="who">You</div>' in index


def test_archive_is_self_contained(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    parser = _Resources()
    parser.feed(index)
    assert parser.scripts == 1  # our own inline script, no src
    for tag in ("link", "img", "iframe", "object", "embed", "video", "audio", "source", "base"):
        assert tag not in parser.tags
    for tag, name, value in parser.refs:
        assert name == "href" and tag == "a" and value.startswith("#"), (tag, name, value)
    assert "@import" not in index and "url(" not in index
    # A URL inside a chat stays plain text, never a link.
    assert "see https://example.com/docs" in index
    assert 'href="http' not in index


def test_archive_csp_allows_only_its_own_inline_code(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', index).group(1)
    assert "default-src 'none'" in csp
    for tag in ("script", "style"):
        body = re.search(r"<%s>(.*?)</%s>" % (tag, tag), index, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()
        assert "'sha256-%s'" % digest in csp


def test_archive_escapes_untrusted_chat_content(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert index.count("<script") == 1 and index.count("</script>") == 1
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in index
    assert "&lt;img src=x onerror=alert(1)&gt;" in index
    assert "<img" not in index and "onerror=" not in index.replace("onerror=alert(1)&gt;", "")
    assert "&lt;/div&gt;&lt;/article&gt;&lt;script&gt;alert(2)" in index
    assert "&lt;b&gt;Untrusted&lt;/b&gt; HTML &amp; {{ARTICLES}} test" in index
    # The title containing "{{ARTICLES}}" must not pull the chats in a second time.
    assert index.count('<article class="chat"') == 3


def test_archive_reserves_index_name(tmp_path):
    _convert(CHATGPT_EXPORT, tmp_path)
    names = sorted(os.listdir(tmp_path))
    assert "index.html" in names and "index-2.md" in names and "index.md" not in names
    assert (tmp_path / "index.html").read_text(encoding="utf-8").count('<a class="item"') == 3


def test_build_archive_api():
    chats, _ = chat_export.load_chats(CLAUDE_FIXTURE)
    page = chat_export.build_archive(chats, "claude", generated="2026-01-01 00:00")
    assert page.startswith("<!DOCTYPE html>") and page.rstrip().endswith("</html>")
    assert "Generated 2026-01-01 00:00" in page
    assert "Recipe Planning" in page and "Code Review" in page


# --- per-chat mode -----------------------------------------------------------

def test_per_chat_mode_writes_pages_and_archive(tmp_path):
    r = _convert(CHATGPT_EXPORT, tmp_path, "--per-chat-html")
    names = sorted(os.listdir(tmp_path))
    assert names == sorted(["index.html", "deploy-checklist.md", "deploy-checklist.html",
                            "b-untrusted-b-html-articles-test.md",
                            "b-untrusted-b-html-articles-test.html",
                            "index-2.md", "index-2.html"])
    assert "per-chat .html" in r.stdout
    page = (tmp_path / "b-untrusted-b-html-articles-test.html").read_text(encoding="utf-8")
    assert "<script" not in page  # per-chat pages carry no script at all
    assert "script-src 'none'" in page
    assert "&lt;script&gt;" in page


def test_convert_claude_cli(tmp_path):
    outdir = tmp_path / "out"
    _convert(CLAUDE_FIXTURE, outdir)
    assert "recipe-planning.md" in os.listdir(outdir)
    assert "code-review.md" in os.listdir(outdir)
    assert "index.html" in os.listdir(outdir)


def test_convert_empty_export_returns_error(tmp_path):
    bad = tmp_path / "empty.json"
    bad.write_text(json.dumps({"conversations": []}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "chat_export.py"),
         "convert", str(bad), "--outdir", str(tmp_path / "o")],
        capture_output=True, text=True)
    assert r.returncode != 0


def test_help_works():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "chat_export.py"), "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "convert" in r.stdout and "search" in r.stdout
    r = subprocess.run([sys.executable, os.path.join(ROOT, "chat_export.py"), "convert", "--help"],
                       capture_output=True, text=True)
    assert "--per-chat-html" in r.stdout


# --- search ------------------------------------------------------------------

@pytest.fixture()
def converted_dir(tmp_path):
    """Convert both fixtures into one directory; return its path."""
    outdir = tmp_path / "out"
    for fixture in (CHATGPT_FIXTURE, CLAUDE_FIXTURE):
        _convert(fixture, outdir)
    return str(outdir)


def _run_search(directory, *extra):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "chat_export.py"), "search", directory, *extra],
        capture_output=True, text=True)


def test_search_finds_match(converted_dir):
    r = _run_search(converted_dir, "reverse")
    assert r.returncode == 0
    assert "python-tips.md" in r.stdout
    assert "reverse a string" in r.stdout


def test_search_case_insensitive(converted_dir):
    assert "reverse a string" in _run_search(converted_dir, "REVERSE", "-i").stdout
    assert "reverse a string" not in _run_search(converted_dir, "REVERSE").stdout


def test_search_no_match(converted_dir):
    r = _run_search(converted_dir, "xyzzy-not-here")
    assert r.returncode == 0 and "No matches" in r.stdout


def test_search_context_lines(converted_dir):
    r = _run_search(converted_dir, "slicing", "-C", "1")
    assert r.returncode == 0
    assert any(line.startswith("  ") for line in r.stdout.splitlines())


def test_search_missing_directory(tmp_path):
    assert _run_search(str(tmp_path / "nope"), "query").returncode != 0
