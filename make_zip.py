"""Build chat-export-pro.zip: the buyer download for the Gumroad listing.

Contents (folder chat-export-pro/):
  chat_export.py          the tool (ChatGPT + Claude -> Markdown + index.html)
  USAGE.md                command reference
  SETUP_GUIDE.md          buyer setup guide
  LICENSE.txt             personal-use license
  verify.sh               test runner
  tests/                  test suite + fixtures (32 tests)

Run:  python make_zip.py
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "chat-export-pro.zip")
TOP = "chat-export-pro"

FILES = ["chat_export.py", "USAGE.md", "paid/SETUP_GUIDE.md",
         "paid/LICENSE.txt", "verify.sh"]
TEST_FILES = ["tests/test_chat_export.py",
              "tests/fixtures/chatgpt_conversations.json",
              "tests/fixtures/chatgpt_sample.json",
              "tests/fixtures/claude_conversations.json",
              "tests/fixtures/claude_sample.json"]


def main():
    names = [os.path.join(TOP, os.path.basename(p)) for p in FILES]
    names += [os.path.join(TOP, p.replace("/", os.sep)) for p in TEST_FILES]
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in zip(FILES + TEST_FILES, names):
            z.write(os.path.join(ROOT, src), arc)
    with zipfile.ZipFile(OUT) as z:
        for i in z.infolist():
            print("%8d  %s" % (i.file_size, i.filename))
        bad = z.testzip()
        print("integrity:", "OK" if bad is None else "CORRUPT: %s" % bad)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
