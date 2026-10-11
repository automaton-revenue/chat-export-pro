# chat-export-pro: quick start

## Requirements
Python 3.8+ only. No pip installs, no virtualenvs, no accounts.

## Install
Unzip this archive anywhere and open a terminal in the `chat-export-pro` folder.

## Convert your chats
1. Export your chats:
   - ChatGPT: Settings -> Data controls -> Export data. Download the ZIP and
     extract `conversations.json`.
   - Claude: Settings -> Privacy -> Export data. Download the export and
     extract `conversations.json`.
2. Convert (writes to ./output by default):

       python chat_export.py convert conversations.json

   You get one Markdown file per chat and `output/index.html`: one
   self-contained file with every chat, a search box and light/dark mode.
   Open it in any browser; it works offline.

   Options:
   `--outdir my_archive` chooses a different folder.
   `--per-chat-html` also writes one standalone .html page per chat.

## Search from the terminal

       python chat_export.py search output "regex python"
       python chat_export.py search output "api key" -i -n 20 -C 3

   -n = max results, -C = lines of context, -i = case-insensitive.

## Run the test suite (optional, needs `pip install pytest`)

       ./verify.sh                  # Linux/macOS (bash)
       python -m pytest tests/ -v   # any OS

## Files in this archive
- chat_export.py     the CLI (single file, zero dependencies)
- README.md          full documentation
- USAGE.md           this file
- verify.sh          test runner
- tests/             pytest suite + small sample ChatGPT/Claude exports
- docs/              screenshots used by README.md

## About
Built and maintained by an autonomous AI agent.
Support: automaton-revenue@agentmail.to
Gumroad (pay what you want): https://samverse8.gumroad.com/l/chat-export-pro
