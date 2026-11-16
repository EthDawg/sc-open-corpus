# Agents

Read `VISION.md` first: it is the acceptance policy for every change here, and a change it says to resist is not made.
Then `DESIGN.md` for why the corpus is shaped this way, `PROTOCOL.md` before any run or score, and `HARVEST.md` before
fetching anything.

- Fetch with a plain client; record refusals, never work around them.
- Never clean the before-AI state, and never write a company claim its sources do not make.
- Keys are never readable by a run while it loads. `tools/run.py`, `tools/learn.py` and `tools/test.py` pass them as forbidden paths.
- Every quote you write must pass `python3 tools/verify_quotes.py <org>`.
- Headless only: never open files in desktop apps; use pdftotext, `soffice --headless`, python-pptx, openpyxl.
- Nothing private enters the repository. `tools/public_cut.py` makes the shareable cut and refuses on any term from the
  local deny list, which lives outside the repository.
