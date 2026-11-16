"""Terms that must never appear in anything public. The list lives outside the repository, on the machine that
publishes (~/.config/sc-open-corpus/denylist.txt, one term per line, case-insensitive), so the repository never names
what it keeps out. With no list present, nothing is denied and public_cut.py refuses to run."""
import os, re

PATH = os.path.expanduser(os.environ.get('SC_CORPUS_DENYLIST', '~/.config/sc-open-corpus/denylist.txt'))


def terms():
    if not os.path.exists(PATH): return []
    return [t.strip().lower() for t in open(PATH) if t.strip() and not t.startswith('#')]


def hit(text, ts=None):
    ts = terms() if ts is None else ts
    low = str(text).lower()
    return any(t in low for t in ts)


def file_hit(path, ts=None):
    try: return hit(open(path, 'rb').read().decode('utf-8', 'replace'), ts)
    except OSError: return False
