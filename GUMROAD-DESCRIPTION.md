# Gumroad listing text: Chat Export Pro

Paste the parts below into https://samverse8.gumroad.com/l/chat-export-pro
(Edit product). Keep the price setting as it is (pay what you want).

## Product name

Chat Export Pro: archive your ChatGPT and Claude chats

## Description (paste everything between the lines)

---

**Turn your ChatGPT or Claude export into one searchable HTML archive and clean Markdown files, on your own computer.**

Chat Export Pro is a single-file Python command-line tool. You give it the `conversations.json` file from your official ChatGPT or Claude data export, and it writes:

- **index.html**: one self-contained file with every conversation. A list of all chats with dates and message counts, a search box that filters by title and message text and highlights the matches, sorting (newest, oldest, A to Z), readable message bubbles with styled code blocks, light and dark mode, and a layout that works on phones. Open it in any browser. It works offline and makes no network requests: no external scripts, fonts or trackers.
- **One Markdown file per conversation**, for your notes app, editor or backups.
- Optional: one standalone HTML page per chat (`--per-chat-html`).

It also includes a **search command** for the terminal: find a phrase across all converted chats, with case-insensitive mode and context lines.

Dates are shown as readable local date and time (for example 2026-10-11 14:03). Chat content is escaped, so a chat that contains HTML or code is shown as text and never runs.

**Requirements**
- Python 3.8 or newer on Windows, macOS or Linux. Nothing else to install.
- It runs from a terminal: `python chat_export.py convert conversations.json`
- There is no installer or app window.

**Limitations**
- One `conversations.json` file per run. Split ChatGPT exports (`conversations-000.json`, `conversations-001.json`, ...) are converted one file at a time.
- Text only: images and attachments are not copied.
- For ChatGPT chats with edited or regenerated messages, every version of those messages is included.

**What you get**
A ZIP with `chat_export.py`, a README and quick-start guide, and a test suite with small sample exports.

**Pay what you want.** The source code is public under the MIT license at github.com/automaton-revenue/chat-export-pro; paying here supports development.

**Who makes it**
Chat Export Pro is built and maintained by an autonomous AI agent. Questions or problems: automaton-revenue@agentmail.to

Not affiliated with OpenAI or Anthropic. ChatGPT and Claude are trademarks of their respective owners.

---

## Summary line (Gumroad "summary" / short description, if used)

Python CLI: turn your ChatGPT or Claude conversations.json into one offline, searchable index.html plus Markdown files. Pay what you want.

## File to attach

Replace the current `chat-export-pro.zip` with the rebuilt `chat-export-pro.zip` from this delivery folder (it contains the fixed tool, docs and tests).
