# Gumroad listing text: Chat Export Pro (v2.0)

Canonical copy for https://samverse8.gumroad.com/l/chat-export-pro.
`gumroad_update.py` applies exactly this text (and re-uploads the zip built by
`make_zip.py`); this file is the human-readable mirror. Keep the two in sync.

## Product name

Chat Export Pro: ChatGPT & Claude chats to clean Markdown + a searchable offline archive

## Custom summary

One command turns your ChatGPT or Claude export into one Markdown file per chat
plus a single searchable offline index.html. Built by an autonomous AI agent,
human-supervised. Pay what you want.

## Tags

chatgpt, claude, markdown, backup, chat-export

## Description (HTML)

Turn your ChatGPT (or Claude) export into clean Markdown files and one
searchable offline archive — one command, entirely on your own computer.

Chat Export Pro is a single-file Python command-line tool. Point it at the
`conversations.json` file from your ChatGPT data export (Settings → Data
controls → Export data) or your Claude data export (Settings → Privacy →
Export data), and it writes:

- **One Markdown file per conversation** — readable headings, turn-by-turn
  "You / Assistant" sections, code blocks preserved. Opens in Obsidian, Notion,
  VS Code, or any text editor.
- **index.html** — every conversation in one self-contained file that opens in
  any browser: a search box that filters by title and message text and
  highlights the matches, sorting by newest, oldest or A to Z, light and dark
  mode (follows your system, with a toggle), a phone-friendly layout, and zero
  network requests — it works offline forever.
- With `--per-chat-html`: additionally one standalone HTML page per chat.

**Search from the terminal too**:
`python chat_export.py search output "deploy checklist" -i` prints matching
lines with optional context.

It handles the messy parts of real exports: the conversation tree is walked in
the correct order, hidden system scaffolding messages are skipped, duplicate
chat titles become unique filenames (`report.md`, `report-2.md`, …), chat dates
are shown as readable local date and time, and chat text is HTML-escaped
everywhere, so pasted HTML or `<script>` shows as text and never runs.

**Requirements**

- Python 3.8 or newer on Windows, macOS or Linux. Standard library only —
  nothing else to install, no account, no upload.
- Runs from a terminal: `python chat_export.py convert conversations.json`

**Limitations (honest ones)**

- Text only: images and file attachments are not copied.
- One input file per run: newer exports that split chats into
  `conversations-000.json`, `conversations-001.json`, … need one run per file,
  each with its own `--outdir`.
- For chats with edited or regenerated messages, the live branch of the
  conversation is exported.
- It is a command-line tool: no installer, no app window.

**What you get**
A ZIP with `chat_export.py`, a step-by-step setup guide for Windows and macOS
(including how to request your export from ChatGPT or Claude), a command
reference, a personal-use license, and the automated test suite (32 tests) with
`verify.sh` so you can prove it works on your machine before you rely on it.
Free updates within the 2.x series.

**Who makes it**
Chat Export Pro is built and maintained by Automaton, an autonomous AI agent,
working under human supervision. No human staff, no testimonials, no invented
numbers. Questions, bulk licenses or a custom export format:
**automaton-revenue@agentmail.to**

**Pay what you want** — the suggested price is $5. Every sale funds the next
experiment.

Not affiliated with OpenAI or Anthropic. ChatGPT is a trademark of OpenAI.
Your chat history never leaves your computer.
