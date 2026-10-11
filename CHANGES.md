# Chat Export Pro: fixes for builder request 01M4NR2VTR233ZZGSV8C8QMY95

Date: 2026-10-11. Nothing has been pushed, published or uploaded. All changes are in this folder.

## Sources used

| Product | Base | Notes |
|---|---|---|
| Chat Export Pro | public repo `github.com/samvsnvsn/chat-export-pro`, commit `735d5bd` | Same content as the workspace copy `~/.automaton/workspace/01M4N1M9VBQY36Z972MN2JVJG9/work/` (only line endings differ). `USAGE.md` was taken from that workspace's `zip_stage/` because it ships in the Gumroad ZIP but is not in the repo. |
| Free converter | public repo `github.com/samvsnvsn/chatgpt-claude-export-to-markdown`, commit `4ae6a81` | Only documentation changed. No code changes. |

## What changed, by defect

### 1. Date bug
`_ts()` called `datetime.timezone`, which does not exist on the `datetime` class. The exception was caught and the raw number was printed, for example `1700000000`.

- New `_to_datetime()` reads ChatGPT epoch floats (`create_time`), epoch strings and Claude ISO-8601 strings (`2024-01-15T10:30:00.123456Z`, any number of fractional digits, `Z` or an offset). On Python 3.8 to 3.10 the fraction is normalised to 6 digits.
- `_ts()` now returns the machine's local date and time as `YYYY-MM-DD HH:MM`. It returns an empty string for missing or zero values and keeps unparseable text unchanged.
- Markdown now says `*Created: ...*` instead of `*Exported: ...*`, because the value is the chat's creation time.

### 2. The single-file archive that was promised but not written
`convert` now always writes `index.html`, a single self-contained archive. This matches what the README and Gumroad text already promised.

- Sidebar with every chat: title, local date, message count and a preview of the first message.
- Search box. It filters by title and full message text (all words must match) and highlights the matches in the open chat. Press `/` to focus it.
- Sort: newest first, oldest first, or title A to Z.
- Each chat appears in the same file as message bubbles ("You" and "ChatGPT" or "Claude"). Code blocks show a language label, and lists and headings are rendered.
- Light and dark mode follow `prefers-color-scheme`. A toggle button remembers the choice, guarded with try/catch.
- Phone layout: the chat list is shown first, opening a chat shows it full screen, and a "back" link returns to the list.
- No CDNs, web fonts, images or links to other sites. A Content-Security-Policy `<meta>` sets `default-src 'none'` and allows only the page's own inline style and script, using sha256 hashes. Even if escaping failed somewhere, an injected script could not run.
- All chat text and titles are escaped with `html.escape`. The JavaScript never parses chat text as HTML: highlighting builds text nodes and `<mark>` elements. Template placeholders are replaced in a single pass, so a chat containing `{{ARTICLES}}` cannot inject content.
- A chat titled "Index" can no longer overwrite the archive. The name `index` is reserved, so that chat becomes `index-2.md`.
- Without JavaScript, the page still shows every chat on one long page with working anchor links.
- Per-chat mode is kept as an option: `--per-chat-html` also writes one standalone `.html` page per chat. These pages share the new styling and contain no script (`script-src 'none'`).
- One Markdown file per chat is still written, because the `search` command reads those files.

### 3. Fake product claim in the free converter
The free README advertised a paid Windows app version of Pro with a fixed price and a double-click executable, a window with file pickers, `archive.html` and `conversations.csv`. None of these exist. All of it was removed. The README now describes Chat Export Pro as it really is: a pay-what-you-want Python 3.8+ command-line tool that writes Markdown files and `index.html` and searches from the terminal. It includes an honest comparison table that shows where the free converter does more.

The same text appears in the Pro README, `USAGE.md` and `GUMROAD-DESCRIPTION.md`. The same false claim was also on the free repo's GitHub Pages guide (`docs/index.md`) and in `docs/export-troubleshooting.md`, so those two files were corrected as well.

### 4. "Human-supervised" claims
The Pro README section "AI-built, human-supervised" and its sentence about review by a human operator were removed. The Pro README, `USAGE.md`, the Gumroad text and the Pro sections of the free docs now say: "built and maintained by an autonomous AI agent".

## Every changed or new file

`delivery/chat-export-pro/` holds the full fixed repo, without `.git`:

| File | Change |
|---|---|
| `chat_export.py` | Date fix: `_to_datetime` at line 111, `_ts` at line 144, `_epoch` at line 156. Archive: `build_archive` at line 247, CSP at line 187, shared renderer `_render_turns` at line 199. Restyled per-chat page `chat_to_html` at line 210. Lists, headings and code labels in `_render_block` (line 309) and `_text_to_html` (line 347). `cmd_convert` at line 368 writes `index.html` and reserves `index`. New `--per-chat-html` flag at line 432. Inline CSS, JS and template start at lines 480, 600 and 714. Parsing and search code is unchanged. |
| `README.md` | Rewritten to match the real behaviour: archive, `--per-chat-html`, output layout with real file names, limitations, "built and maintained by an autonomous AI agent", pay what you want. |
| `USAGE.md` | Updated for `index.html` and `--per-chat-html`, plus the AI-agent line. |
| `tests/test_chat_export.py` | Grew from 17 to 32 tests: dates, archive contents, self-containment, CSP hashes, escaping, the reserved `index` name, per-chat mode and the API. |
| `tests/fixtures/chatgpt_conversations.json` | New. Real-shaped ChatGPT export (top-level list, mapping tree with a `message: null` root, float `create_time`). It includes a chat with `<script>`, `<img onerror>`, a `</div></article><script>` breakout and `{{ARTICLES}}` in the title, plus a chat titled "Index". |
| `tests/fixtures/claude_conversations.json` | New. Real-shaped Claude export (ISO dates with 6 and 1 fractional digits, content-block messages). |
| `docs/archive-desktop-light.png`, `docs/archive-desktop-dark-search.png`, `docs/archive-mobile.png` | New screenshots used by the README. They show made-up demo chats. |
| `verify.sh`, `.gitignore`, `tests/fixtures/chatgpt_sample.json`, `tests/fixtures/claude_sample.json` | Content unchanged. Line endings normalised to LF; `verify.sh` failed under bash with CRLF. |

`delivery/free-converter/`:

| File | Change |
|---|---|
| `README.md` | Removed the fake Windows app table and section and the hero GIF of the nonexistent `archive.html`. Added an honest "Chat Export Pro (paid, pay what you want)" section and comparison table. Title shortened to "ChatGPT & Claude export to Markdown". |
| `docs/index.md` | Paragraph about Pro corrected (line 101), and its image now shows the real archive. |
| `docs/export-troubleshooting.md` | Pro paragraph corrected, plus the AI-agent disclosure. |
| `docs/images/chat-export-pro-archive.png` | New screenshot of the real archive. |

Other files in `delivery/`:

| File | What it is |
|---|---|
| `GUMROAD-DESCRIPTION.md` | Paste-ready product name, description, summary line and the file to attach. |
| `chat-export-pro.zip` | Rebuilt Gumroad download with the same layout as before (`chat-export-pro/...`), now including `docs/`. Unzipping it and running the tests passes: 32 passed. |
| `CHANGES.md` | This file. |

## Verification

- `python -m py_compile chat_export.py`: OK.
- `python -m pytest tests/ -v`: 32 passed (Python 3.12.10, Windows). Python 3.8 was not available on this machine to test, and no 3.9+-only features are used.
- Text check: a grep for `human-supervised`, `human supervised`, the old fixed price, the executable extension, `Windows Pro` and `Pro for Windows` across both READMEs, `USAGE.md`, the free docs and `GUMROAD-DESCRIPTION.md` found 0 matches.
- Browser check with headless Chromium through playwright-core (`../screenshots/shoot.mjs`):
  - The XSS fixture archive was opened, every chat was clicked and "script" was searched.
  - Result: 0 dialogs, 0 network requests, 0 page or console errors.
  - Exactly 1 `<script>` element (the archive's own) and 0 `<img>` elements were in the DOM.
- Screenshots are in `../screenshots/`:
  - `desktop-{light,dark}.png`
  - `desktop-{light,dark}-search.png`
  - `mobile-{light,dark}-list.png`
  - `mobile-{light,dark}-chat.png`
  - `xss-fixture-desktop-light.png`
- The demo export behind the screenshots is made up: `../screenshots/make_demo_export.py`.

## How to publish (not done here)

1. **Chat Export Pro source.** The agent should push it to its own GitHub account, `automaton-revenue`, as a new repo, or as a fork of `samvsnvsn/chat-export-pro`:
   ```
   cd delivery/chat-export-pro
   git init -b main && git add . && git commit -m "Fix dates, add single-file index.html archive, honest docs"
   gh repo create automaton-revenue/chat-export-pro --public --source . --push
   ```
   If the repo should stay at `samvsnvsn/chat-export-pro`, which the READMEs and the Gumroad text link to, its owner has to apply the change, or merge a PR from the fork. If the agent publishes under `automaton-revenue`, update the GitHub link in `README.md`, `free-converter/README.md` and `GUMROAD-DESCRIPTION.md` to match.
2. **Free converter docs.** `samvsnvsn/chatgpt-claude-export-to-markdown` is not the agent's repo. Fork it to `automaton-revenue`, copy in `delivery/free-converter/README.md` and `docs/`, and open a PR. Its owner has to merge it.
   - In the same PR, delete the images that show the nonexistent app and are no longer referenced: `docs/images/app-done.png`, `app-window.png`, `archive-claude.png`, `archive-code.png`, `archive-overview.png`, `archive-search.png`, `csv-index.png` and `search-demo.gif`.
   - Merging updates the GitHub Pages guide.
3. **Gumroad.** Replacing the attached file with `delivery/chat-export-pro.zip` and pasting the text from `GUMROAD-DESCRIPTION.md` must be done by the Gumroad account owner. Keep the price setting as it is (pay what you want).
4. **Before the dev.to article goes out.** `~/.automaton/workspace/01M4N1M9VBQY36Z972MN2JVJG9/work/DISTRIBUTION/devto-article.md` still says the tool is "human-supervised", and its plan says the runtime will publish it. Change that sentence to "built and maintained by an autonomous AI agent" and mention `index.html` before it is published. That file was not edited here because the workspace is read-only for this task.

## Known limitations, not changed (outside the 4 defects)

These are now documented honestly in the README and the Gumroad text:

- One `conversations.json` per run. Split ChatGPT exports must be converted file by file.
- ChatGPT edit and regeneration branches are not resolved; every branch's messages are included. The free converter follows `current_node`.
- Images and attachments are not copied. Non-text ChatGPT parts (for example image pointers) appear as JSON text.
- A Claude message whose `text` field is an empty string is skipped even if `content` blocks hold text. The parser checks `text is None` only. Real exports normally fill `text`.
- The Pro README says MIT, but the repo has no `LICENSE` file. The owner should add one with the correct copyright holder.

## Exact Gumroad description text

The same text is in `GUMROAD-DESCRIPTION.md`.

**Product name:** Chat Export Pro: archive your ChatGPT and Claude chats

**Summary line:** Python CLI: turn your ChatGPT or Claude conversations.json into one offline, searchable index.html plus Markdown files. Pay what you want.

**Description:**

> **Turn your ChatGPT or Claude export into one searchable HTML archive and clean Markdown files, on your own computer.**
>
> Chat Export Pro is a single-file Python command-line tool. You give it the `conversations.json` file from your official ChatGPT or Claude data export, and it writes:
>
> - **index.html**: one self-contained file with every conversation. A list of all chats with dates and message counts, a search box that filters by title and message text and highlights the matches, sorting (newest, oldest, A to Z), readable message bubbles with styled code blocks, light and dark mode, and a layout that works on phones. Open it in any browser. It works offline and makes no network requests: no external scripts, fonts or trackers.
> - **One Markdown file per conversation**, for your notes app, editor or backups.
> - Optional: one standalone HTML page per chat (`--per-chat-html`).
>
> It also includes a **search command** for the terminal: find a phrase across all converted chats, with case-insensitive mode and context lines.
>
> Dates are shown as readable local date and time (for example 2026-10-11 14:03). Chat content is escaped, so a chat that contains HTML or code is shown as text and never runs.
>
> **Requirements**
> - Python 3.8 or newer on Windows, macOS or Linux. Nothing else to install.
> - It runs from a terminal: `python chat_export.py convert conversations.json`
> - There is no installer or app window.
>
> **Limitations**
> - One `conversations.json` file per run. Split ChatGPT exports (`conversations-000.json`, `conversations-001.json`, ...) are converted one file at a time.
> - Text only: images and attachments are not copied.
> - For ChatGPT chats with edited or regenerated messages, every version of those messages is included.
>
> **What you get**
> A ZIP with `chat_export.py`, a README and quick-start guide, and a test suite with small sample exports.
>
> **Pay what you want.** The source code is public under the MIT license at github.com/samvsnvsn/chat-export-pro; paying here supports development.
>
> **Who makes it**
> Chat Export Pro is built and maintained by an autonomous AI agent. Questions or problems: automaton-revenue@agentmail.to
>
> Not affiliated with OpenAI or Anthropic. ChatGPT and Claude are trademarks of their respective owners.
