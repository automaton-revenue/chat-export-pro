"""Update the live Gumroad listing for Chat Export Pro (v2.0) with truthful copy.

Run:  python gumroad_update.py
Uses the Gumroad seller CLI (no secrets printed). Re-uploads the zip, sets the
square thumbnail, then updates the text fields in small calls.
The copy describes exactly what the shipped zip contains: chat_export.py
(ChatGPT + Claude -> one Markdown file per chat + index.html archive + search),
USAGE.md, SETUP_GUIDE.md, LICENSE.txt, tests/ and verify.sh.
"""

import json
import subprocess
from pathlib import Path

EXE = Path.home() / "AppData/Local/gumroad/gumroad.exe"
PRODUCT_ID = "jYHqlMkpafJU-XWkN_b2Hg=="
ROOT = Path(__file__).parent

DESCRIPTION = """\
<p><strong>Turn your ChatGPT (or Claude) export into clean Markdown files and one searchable offline archive &mdash; one command, entirely on your own computer.</strong></p>
<p>Chat Export Pro is a single-file Python command-line tool. Point it at the <code>conversations.json</code> file from your ChatGPT data export (Settings &rarr; Data controls &rarr; Export data) or your Claude data export (Settings &rarr; Privacy &rarr; Export data), and it writes:</p>
<ul>
<li><strong>One Markdown file per conversation</strong> &mdash; readable headings, turn-by-turn &ldquo;You / Assistant&rdquo; sections, code blocks preserved. Opens in Obsidian, Notion, VS Code, or any text editor.</li>
<li><strong>index.html</strong> &mdash; every conversation in one self-contained file that opens in any browser: a search box that filters by title and message text and highlights the matches, sorting by newest, oldest or A to Z, light and dark mode (follows your system, with a toggle), a phone-friendly layout, and zero network requests &mdash; it works offline forever.</li>
<li>With <code>--per-chat-html</code>: additionally one standalone HTML page per chat.</li>
</ul>
<p><strong>Search from the terminal too</strong>: <code>python chat_export.py search output &quot;deploy checklist&quot; -i</code> prints matching lines with optional context.</p>
<p>It handles the messy parts of real exports: the conversation tree is walked in the correct order, hidden system scaffolding messages are skipped, duplicate chat titles become unique filenames (<code>report.md</code>, <code>report-2.md</code>, &hellip;), chat dates are shown as readable local date and time, and chat text is HTML-escaped everywhere, so pasted HTML or <code>&lt;script&gt;</code> shows as text and never runs.</p>
<p><strong>Requirements</strong></p>
<ul>
<li>Python 3.8 or newer on Windows, macOS or Linux. Standard library only &mdash; nothing else to install, no account, no upload.</li>
<li>Runs from a terminal: <code>python chat_export.py convert conversations.json</code></li>
</ul>
<p><strong>Limitations (honest ones)</strong></p>
<ul>
<li>Text only: images and file attachments are not copied.</li>
<li>One input file per run: newer exports that split chats into <code>conversations-000.json</code>, <code>conversations-001.json</code>, &hellip; need one run per file, each with its own <code>--outdir</code>.</li>
<li>For chats with edited or regenerated messages, the live branch of the conversation is exported.</li>
<li>It is a command-line tool: no installer, no app window.</li>
</ul>
<p><strong>What you get</strong><br>A ZIP with <code>chat_export.py</code>, a step-by-step setup guide for Windows and macOS (including how to request your export from ChatGPT or Claude), a command reference, a personal-use license, and the automated test suite (32 tests) with <code>verify.sh</code> so you can prove it works on your machine before you rely on it. Free updates within the 2.x series.</p>
<p><strong>Who makes it</strong><br>Chat Export Pro is built and maintained by Automaton, an autonomous AI agent, working under human supervision. No human staff, no testimonials, no invented numbers. Questions, bulk licenses or a custom export format: <strong>automaton-revenue@agentmail.to</strong></p>
<p><strong>Pay what you want</strong> &mdash; the suggested price is $5. Every sale funds the next experiment.</p>
<p>Not affiliated with OpenAI or Anthropic. ChatGPT is a trademark of OpenAI. Your chat history never leaves your computer.</p>
"""

SUMMARY = (
    "One command turns your ChatGPT or Claude export into one Markdown file per "
    "chat plus a single searchable offline index.html. Built by an autonomous AI "
    "agent, human-supervised. Pay what you want."
)

NAME = ("Chat Export Pro: ChatGPT & Claude chats to clean Markdown "
        "+ a searchable offline archive")


def run(args):
    cmd = [str(EXE)] + args + ["--json", "--no-input", "--yes"]
    shown = [a if "\n" not in a else a[:30] + "...(html)" for a in args]
    print("$", " ".join(shown))
    p = subprocess.run(cmd, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace").strip()
    err = (p.stderr or b"").decode("utf-8", "replace").strip()
    if out:
        print(out[:220])
    if p.returncode != 0 or not out:
        print("STDERR:", err[:500])
        raise SystemExit("command failed rc=%s: %s" % (p.returncode, args[0]))
    return json.loads(out) if out.startswith("{") else out


def main():
    # 1. Upload the product zip (private attachment buyers download after paying).
    up = run(["files", "upload", str(ROOT / "chat-export-pro.zip"),
              "--name", "chat-export-pro.zip"])
    print("uploaded zip:", up.get("file_url"))

    # 2. Attach the zip to the product and set a square thumbnail.
    run(["products", "update", PRODUCT_ID, "--file", str(ROOT / "chat-export-pro.zip"),
         "--file-name", "chat-export-pro.zip",
         "--file-description", "Chat Export Pro 2.0: converter script, setup guide, license, test suite",
         "--thumbnail", str(ROOT / "cover.png")])

    # 3. Truthful relaunch copy, in small calls.
    run(["products", "update", PRODUCT_ID, "--name", NAME])
    run(["products", "update", PRODUCT_ID, "--custom-summary", SUMMARY])
    run(["products", "update", PRODUCT_ID, "--description", DESCRIPTION])
    run(["products", "update", PRODUCT_ID, "--tag", "chatgpt", "--tag", "claude",
         "--tag", "markdown", "--tag", "backup", "--tag", "chat-export"])

    print("OK: Gumroad listing updated")


if __name__ == "__main__":
    main()
