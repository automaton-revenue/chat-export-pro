# ChatGPT & Claude export to Markdown

Turn the **official data export** from ChatGPT or Claude (the ZIP you get by email) into readable files on your own computer: one Markdown file per conversation, with images, dates and project folders. It works offline. Nothing is uploaded, and you don't need a login or a browser extension.

This converter is free, open source (MIT) and complete: no limits or watermarks. A separate paid tool, [Chat Export Pro](#chat-export-pro-paid-pay-what-you-want), is described at the end of this page.

Full walkthrough: **[How to turn your ChatGPT or Claude data export into a searchable offline archive](https://samvsnvsn.github.io/chatgpt-claude-export-to-markdown/)**

## What it does

- Reads the **ChatGPT data export** and the **Claude data export** (`conversations.json` + `projects.json`), and detects which one it is.
- Supports the **current ChatGPT export format**: conversations split into `conversations-000.json`, `conversations-001.json`, … and large exports delivered as several `…-part-0001.zip`, `…-part-0002.zip` files (keep them in one folder and pass any part). Images stored as `.dat` files get their real extension back.
- **Follows the branch you actually saw.** ChatGPT stores edits and regenerations as a tree; you get the final conversation, without duplicates.
- Keeps code blocks (with language), code/tool output, quotes, Claude "thinking" blocks and Claude attachments' extracted text.
- Copies uploaded and generated **images** into `assets/` and links them.
- Puts **ChatGPT Projects** and **Claude Projects** into their own folders (`--flat` to turn off).
- Adds **YAML front-matter** (title, source, id, created, updated, project, model, message count), so it works well in **Obsidian**.
- Uses Windows-safe file names (`2025-09-24 Invoice reminder email.md`) and writes an `index.md` table of everything.
- New or unknown content types appear as a visible note instead of crashing the conversion.

Python 3.9+ standard library only; no dependencies.

## Install and run

```bash
pip install git+https://github.com/samvsnvsn/chatgpt-claude-export-to-markdown
chat-export ~/Downloads/chatgpt-export.zip -o my-chats
```

or, without installing (download the repo, then from its folder):

```bash
python -m chat_export path/to/export.zip -o my-chats
```

| Option | Meaning |
|---|---|
| `-o, --out FOLDER` | output folder (default `chat-export-markdown`) |
| `--since YYYY-MM-DD` | only conversations created on or after this date |
| `--flat` | don't group project conversations into folders |

To try it without your own data, use the made-up demo exports in [`examples/`](examples):

```bash
chat-export examples/chatgpt-export-demo.zip -o demo-chatgpt
chat-export examples/claude-export-demo.zip -o demo-claude
```

It also accepts a loose `conversations.json` or an unzipped export folder. Run it once per export: once for ChatGPT, once for Claude.

### Example output

![Markdown output: folder tree and one converted conversation (demo data)](docs/images/markdown-output.png)

```
my-chats/
  index.md
  2025-09-23 Python dedupe a CSV by email.md
  2025-09-22 What does this signup chart show.md
  assets/
    file-DEMO01-signups.png
  projects/
    g-p-freelance/
      2025-09-24 Invoice reminder email.md
```

### Searching the Markdown

Open the output folder in Obsidian or VS Code and use their search, or use `rg -i "invoice" my-chats` ([ripgrep](https://github.com/BurntSushi/ripgrep)) or `findstr /s /i "invoice" *.md` on Windows.

## How this compares with other free approaches

There are many good free tools for this; pick whatever fits you. The common approaches are:

- **Browser userscripts or extensions** export conversations from the live chatgpt.com or claude.ai page while you're logged in, often one at a time. This tool works on the official export ZIP instead, so it needs no login or extension and covers your whole history at once.
- **Python or npm converters** are usually for one provider (ChatGPT *or* Claude). This one reads both.
- **Single-file HTML viewers** let you browse an export in the browser. This converter writes Markdown files, not a viewer.

## Getting your export

- **ChatGPT:** Settings → Data controls → Export data, then confirm. You get an email with a download link.
- **Claude:** Settings → Privacy → Export data. You get an email with a download link.

## Limitations

- Exports only contain what OpenAI and Anthropic include. Claude exports don't include the uploaded files themselves; their names and extracted text are kept.
- ChatGPT Project folders are named by project id (e.g. `g-p-…`) because the export doesn't include project names. Claude project names are used.
- Voice audio isn't included; transcriptions are.
- One export per run. ChatGPT and Claude exports produce separate outputs.

## Chat Export Pro (paid, pay what you want)

[Chat Export Pro](https://samverse8.gumroad.com/l/chat-export-pro) is a separate, smaller tool sold on Gumroad at a pay-what-you-want price. It is a single-file Python 3.8+ command-line script (standard library only) for Windows, macOS or Linux. There is no installer or app window; you run it from a terminal. Its source is public at [github.com/automaton-revenue/chat-export-pro](https://github.com/automaton-revenue/chat-export-pro). Chat Export Pro is built and maintained by an autonomous AI agent.

What it does:

- `convert` reads one ChatGPT or Claude `conversations.json` file and writes one Markdown file per conversation plus **`index.html`**: a single self-contained file with every chat. It has a search box (titles and message text, with highlighted matches), sorting, readable message bubbles with styled code blocks, light/dark mode and a phone layout. It works offline and makes no network requests.
- `--per-chat-html` also writes one standalone `.html` page per chat.
- `search` searches the converted Markdown from the terminal (case-insensitive, context lines).
- Dates are shown as local date and time, e.g. `2026-10-11 14:03`.

![Chat Export Pro's index.html archive (made-up demo chats)](docs/images/chat-export-pro-archive.png)

How the two differ:

| | **Free converter** (this repo) | **Chat Export Pro** (pay what you want) |
|---|---|---|
| Input | export ZIP, folder or `conversations.json`, including split ChatGPT exports | one `conversations.json` file per run |
| Markdown output | YAML front-matter, images, project folders, `index.md` | plain Markdown per chat, text only |
| Edited or regenerated ChatGPT messages | only the branch you saw | every branch's messages |
| Single-file `index.html` archive with search | – | ✅ |
| Search from the terminal | – | ✅ |
| Requires | Python 3.9+ | Python 3.8+ |
| License | MIT | MIT |

If you only need Markdown, the free converter does more. Chat Export Pro is for people who want the one-file browsable archive.

## License

MIT. See [LICENSE](LICENSE). Not affiliated with OpenAI or Anthropic; "ChatGPT" and "Claude" are trademarks of their respective owners.
